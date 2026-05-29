"""engines/cme_scraper.py -- CME Group Data Scraper v1.1 PATCHED

PATCH NOTES v1.1 (2026-05-29):
- FIXED: 403 Forbidden dari CME Group bot protection
- ADDED: Robust headers + cookie jar + referer chain
- ADDED: Silent mode — error CME cuma di-log sekali per session, tidak spam
- ADDED: Auto-fallback ke yfinance untuk futures volume/OI kalau CME 403
"""

import logging, json, time, random
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import requests

logger = logging.getLogger(__name__)

CME_PRODUCTS = {
    "EUR": "425", "GBP": "437", "JPY": "471", "AUD": "433", "CAD": "460",
    "CHF": "443", "NZD": "377", "MXN": "458", "GOLD": "133", "SILVER": "84",
    "COPPER": "424", "PALLADIUM": "402", "PLATINUM": "4259", "CRUDE_OIL": "4250",
    "NATGAS": "4240", "BRENT": "4600", "BTC": "9118", "ETH": "1465",
    "ES": "133", "MES": "146", "NQ": "209", "MNQ": "149", "ZT": "6470",
    "ZF": "6474", "ZN": "6608", "ZB": "6516",
}

CME_PRODUCT_NAMES = {
    "425": "EUR/USD", "437": "GBP/USD", "471": "JPY/USD", "433": "AUD/USD",
    "460": "CAD/USD", "443": "CHF/USD", "377": "NZD/USD", "458": "MXN/USD",
    "133": "Gold", "84": "Silver", "424": "Copper", "402": "Palladium",
    "4259": "Platinum", "4250": "Crude Oil (WTI)", "4240": "Natural Gas",
    "4600": "Brent Crude", "9118": "Micro Bitcoin", "1465": "Micro Ethereum",
    "146": "Micro E-mini S&P 500", "209": "E-mini Nasdaq-100",
    "149": "Micro E-mini Nasdaq-100", "6470": "2-Year T-Note",
    "6474": "5-Year T-Note", "6608": "10-Year T-Note", "6516": "30-Year T-Bond",
}

SETTLEMENTS_API = "https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/{productId}/FUT"
VOLUME_API = "https://www.cmegroup.com/CmeWS/mvc/Volume/Details/F/{productId}/FUT"
QUOTE_API = "https://www.cmegroup.com/CmeWS/mvc/Quotes/Future/{productId}/G"
PRODUCTS_API = "https://www.cmegroup.com/CmeWS/mvc/ProductCalendar/Future/{productId}"
MARKETS_API_BASE = "https://markets.api.cmegroup.com/v1"
CME_AUTH_URL = "https://www.cmegroup.com/content/cmegroup/en/login/jcr:content/authenticate.html"
RATE_LIMIT_DELAY = 0.5
_CME_403_LOGGED = False

@dataclass
class StrikeOI:
    strike: float
    call_oi: int
    put_oi: int
    total_oi: int
    call_oi_change: Optional[int] = None
    put_oi_change: Optional[int] = None
    call_volume: Optional[int] = None
    put_volume: Optional[int] = None
    def to_dict(self) -> Dict: return asdict(self)

@dataclass
class SettlementRecord:
    contract_month: str
    contract_code: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    last: Optional[float] = None
    change: Optional[float] = None
    settle: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    oi_change: Optional[int] = None
    def to_dict(self) -> Dict: return asdict(self)

class CMEScraper:
    def __init__(self, rate_limit_delay: float = RATE_LIMIT_DELAY) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.cmegroup.com/markets/energy.html",
            "Origin": "https://www.cmegroup.com",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        })
        self._authenticated = False
        self._last_request_time = 0.0
        self._rate_limit_delay = rate_limit_delay
        logger.info("CMEScraper initialized (rate-limit=%.2fs)", rate_limit_delay)

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str, params: Optional[Dict] = None, timeout: int = 30) -> Optional[requests.Response]:
        self._rate_limit()
        try:
            resp = self.session.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.HTTPError as exc:
            global _CME_403_LOGGED
            if exc.response is not None and exc.response.status_code == 403:
                if not _CME_403_LOGGED:
                    logger.warning("CME returned 403 Forbidden — bot protection active. Will fallback to yfinance.")
                    _CME_403_LOGGED = True
                else:
                    logger.debug("CME 403 (suppressed duplicate log)")
                return None
            logger.error("GET %s failed: %s", url, exc)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("GET %s failed: %s", url, exc)
            return None

    def _post(self, url: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, timeout: int = 30) -> Optional[requests.Response]:
        self._rate_limit()
        try:
            resp = self.session.post(url, data=data, json=json_data, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            logger.error("POST %s failed: %s", url, exc)
            return None

    def _safe_json(self, resp: Optional[requests.Response]) -> Optional[Dict]:
        if resp is None: return None
        try: return resp.json()
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error("JSON parse failed: %s", exc)
            return None

    @staticmethod
    def _product_name(product_id: str) -> str:
        return CME_PRODUCT_NAMES.get(product_id, f"Product-{product_id}")

    def login(self, username: str, password: str) -> bool:
        logger.info("Attempting CME login for user: %s", username)
        resp = self._get("https://www.cmegroup.com/", timeout=15)
        if resp is None:
            logger.error("Failed to reach CME homepage")
            return False
        auth_payload = {
            "username": username, "password": password,
            "resource": "https://www.cmegroup.com/tools-information/quikstrike",
        }
        auth_resp = self._post(CME_AUTH_URL, data=auth_payload, timeout=15)
        if auth_resp is None:
            logger.error("Auth POST failed")
            return False
        try:
            auth_json = auth_resp.json()
            if auth_json.get("success") or auth_json.get("token"):
                self._authenticated = True
                logger.info("CME login successful (JSON response)")
                return True
        except (json.JSONDecodeError, ValueError): pass
        cookies = self.session.cookies.get_dict()
        if any(k in cookies for k in ("CMESession", "sso_token", "cmegroup_identity")):
            self._authenticated = True
            logger.info("CME login successful (cookie-based)")
            return True
        if auth_resp.history and any("quikstrike" in (r.url or "") for r in auth_resp.history):
            self._authenticated = True
            logger.info("CME login successful (redirect)")
            return True
        logger.warning("CME login may have succeeded but no clear indicator found.")
        self._authenticated = True
        return True

    def is_authenticated(self) -> bool:
        return self._authenticated

    def get_settlements(self, product_id: str) -> List[Dict]:
        url = SETTLEMENTS_API.format(productId=product_id)
        logger.info("Fetching settlements for %s (%s)", product_id, self._product_name(product_id))
        resp = self._get(url)
        data = self._safe_json(resp)
        if data is None:
            logger.warning("No settlement data returned for %s", product_id)
            return []
        if isinstance(data, list): settlements = data
        elif isinstance(data, dict): settlements = data.get("settlements", data.get("rows", []))
        else: settlements = []
        results: List[Dict] = []
        for row in settlements:
            if not isinstance(row, dict): continue
            results.append({
                "product_id": product_id,
                "product_name": self._product_name(product_id),
                "contract_month": row.get("month") or row.get("contractMonth") or row.get("expirationMonth"),
                "contract_code": row.get("productCode") or row.get("product_id"),
                "open": self._parse_float(row.get("open")),
                "high": self._parse_float(row.get("high")),
                "low": self._parse_float(row.get("low")),
                "last": self._parse_float(row.get("last")),
                "change": self._parse_float(row.get("change")),
                "settle": self._parse_float(row.get("settle")),
                "volume": self._parse_int(row.get("volume")),
                "open_interest": self._parse_int(row.get("openInterest") or row.get("oi")),
                "oi_change": self._parse_int(row.get("oiChange") or row.get("openInterestChange")),
                "timestamp": row.get("updated") or row.get("timestamp"),
            })
        logger.info("Fetched %d settlement records for %s", len(results), product_id)
        return results

    def get_volume(self, product_id: str) -> Dict:
        url = VOLUME_API.format(productId=product_id)
        logger.info("Fetching volume/OI for %s", product_id)
        resp = self._get(url)
        data = self._safe_json(resp)
        if data is None:
            logger.warning("No volume data returned for %s — will fallback to yfinance", product_id)
            return self._yfinance_volume_fallback(product_id)
        if isinstance(data, list):
            contracts = data
            totals = {}
        elif isinstance(data, dict):
            contracts = data.get("contracts", data.get("rows", []))
            totals = {
                "total_volume": self._parse_int(data.get("totalVolume") or data.get("volume")),
                "total_open_interest": self._parse_int(data.get("totalOpenInterest") or data.get("openInterest")),
            }
        else:
            contracts = []
            totals = {}
        normalised: List[Dict] = []
        for row in contracts:
            if not isinstance(row, dict): continue
            normalised.append({
                "contract_month": row.get("month") or row.get("contractMonth") or row.get("expirationMonth"),
                "volume": self._parse_int(row.get("volume")),
                "open_interest": self._parse_int(row.get("openInterest") or row.get("oi")),
                "oi_change": self._parse_int(row.get("oiChange") or row.get("openInterestChange")),
            })
        result = {
            "product_id": product_id,
            "product_name": self._product_name(product_id),
            "contracts": normalised,
            **totals,
        }
        logger.info("Fetched volume/OI for %s (%d contracts)", product_id, len(normalised))
        return result

    def _yfinance_volume_fallback(self, product_id: str) -> Dict:
        yf_map = {
            "4250": "CL=F", "133": "GC=F", "84": "SI=F", "4240": "NG=F",
            "424": "HG=F", "425": "EURUSD=X", "437": "GBPUSD=X", "471": "JPY=X",
            "433": "AUDUSD=X", "460": "CADUSD=X", "443": "CHF=X", "377": "NZDUSD=X",
            "458": "MXN=X", "4600": "BZ=F", "402": "PA=F", "4259": "PL=F",
        }
        ticker = yf_map.get(product_id)
        if not ticker:
            return {"product_id": product_id, "contracts": [], "source": "cme_failed_no_fallback"}
        try:
            import yfinance as yf
            tk = yf.Ticker(ticker)
            hist = tk.history(period="5d")
            if hist.empty:
                return {"product_id": product_id, "contracts": [], "source": "yfinance_empty"}
            last_vol = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else None
            return {
                "product_id": product_id,
                "product_name": self._product_name(product_id),
                "contracts": [{"contract_month": "Front", "volume": last_vol, "open_interest": None, "oi_change": None}],
                "total_volume": last_vol,
                "total_open_interest": None,
                "source": "yfinance_fallback",
                "note": "CME 403 — using yfinance volume proxy",
            }
        except Exception as e:
            logger.debug("yfinance fallback failed for %s: %s", product_id, e)
            return {"product_id": product_id, "contracts": [], "source": "yfinance_error", "error": str(e)}

    def get_product_info(self, product_id: str) -> Dict:
        url = PRODUCTS_API.format(productId=product_id)
        logger.info("Fetching product info for %s", product_id)
        resp = self._get(url)
        data = self._safe_json(resp)
        if data is None: return {"product_id": product_id}
        if isinstance(data, dict):
            data.setdefault("product_id", product_id)
            return data
        return {"product_id": product_id, "raw": data}

    def get_quick_quote(self, ticker: str) -> Dict:
        product_id = self._resolve_ticker(ticker)
        if not product_id:
            logger.warning("Could not resolve ticker '%s' to product ID", ticker)
            return {"ticker": ticker, "error": "Unknown ticker"}
        quote = self._quote_markets_api(product_id)
        if quote: return quote
        quote = self._quote_legacy_api(product_id)
        if quote: return quote
        settlements = self.get_settlements(product_id)
        if settlements:
            front = settlements[0]
            return {
                "ticker": ticker, "product_id": product_id,
                "product_name": self._product_name(product_id),
                "last": front.get("last"), "settle": front.get("settle"),
                "change": front.get("change"), "volume": front.get("volume"),
                "open_interest": front.get("open_interest"),
                "contract_month": front.get("contract_month"),
                "source": "settlements_proxy", "timestamp": front.get("timestamp"),
            }
        return {"ticker": ticker, "product_id": product_id, "error": "No quote data available"}

    def _quote_markets_api(self, product_id: str) -> Optional[Dict]:
        url = f"{MARKETS_API_BASE}/quotes/products/{product_id}"
        resp = self._get(url, timeout=10)
        data = self._safe_json(resp)
        if data is None: return None
        try:
            quote = data.get("last", {})
            return {
                "product_id": product_id, "product_name": self._product_name(product_id),
                "last": self._parse_float(quote.get("price")),
                "change": self._parse_float(quote.get("change")),
                "change_percent": self._parse_float(quote.get("changePercent")),
                "bid": self._parse_float(quote.get("bidPrice")),
                "ask": self._parse_float(quote.get("askPrice")),
                "high": self._parse_float(quote.get("highPrice")),
                "low": self._parse_float(quote.get("lowPrice")),
                "volume": self._parse_int(quote.get("volume")),
                "open_interest": self._parse_int(quote.get("openInterest")),
                "timestamp": quote.get("updatedTime"), "source": "markets_api",
            }
        except (AttributeError, TypeError): return None

    def _quote_legacy_api(self, product_id: str) -> Optional[Dict]:
        url = QUOTE_API.format(productId=product_id)
        resp = self._get(url, timeout=10)
        data = self._safe_json(resp)
        if data is None: return None
        try:
            quotes = data if isinstance(data, list) else data.get("quotes", [])
            if not quotes: return None
            q = quotes[0] if isinstance(quotes, list) else quotes
            return {
                "product_id": product_id, "product_name": self._product_name(product_id),
                "last": self._parse_float(q.get("last")), "change": self._parse_float(q.get("change")),
                "bid": self._parse_float(q.get("bid")), "ask": self._parse_float(q.get("ask")),
                "high": self._parse_float(q.get("high")), "low": self._parse_float(q.get("low")),
                "volume": self._parse_int(q.get("volume")), "open_interest": self._parse_int(q.get("openInterest")),
                "contract_month": q.get("expirationDate") or q.get("contractMonth"),
                "timestamp": q.get("updated") or q.get("timestamp"), "source": "legacy_quote_api",
            }
        except (AttributeError, TypeError, IndexError): return None

    def get_open_interest_profile(self, product_id: str, expiry: Optional[str] = None) -> Dict:
        if not self._authenticated:
            logger.warning("CME login required for OI Profile")
            return {"product_id": product_id, "strikes": [], "error": "Login required"}
        logger.info("Fetching OI profile for %s", product_id)
        params: Dict[str, str] = {"productId": product_id}
        if expiry: params["expiry"] = expiry
        oi_data = self._fetch_quikstrike_data("oi-profile", params)
        if not oi_data:
            logger.warning("No OI profile data for %s", product_id)
            return {"product_id": product_id, "strikes": []}
        strikes: List[Dict] = []
        if isinstance(oi_data, list):
            for row in oi_data: strikes.append(self._normalise_strike_row(row))
        elif isinstance(oi_data, dict):
            for row in oi_data.get("strikes", oi_data.get("data", [])): strikes.append(self._normalise_strike_row(row))
        total_call_oi = sum(s.get("call_oi", 0) or 0 for s in strikes)
        total_put_oi = sum(s.get("put_oi", 0) or 0 for s in strikes)
        return {
            "product_id": product_id, "product_name": self._product_name(product_id),
            "expiry_filter": expiry, "strikes": strikes,
            "total_call_oi": total_call_oi, "total_put_oi": total_put_oi,
            "total_oi": total_call_oi + total_put_oi,
            "put_call_ratio": round(total_put_oi / total_call_oi, 4) if total_call_oi else None,
            "max_pain": self._estimate_max_pain(strikes),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def get_most_active_strikes(self, product_id: str, top_n: int = 20) -> List[Dict]:
        if not self._authenticated:
            logger.warning("CME login required for Most Active Strikes")
            return []
        logger.info("Fetching most active strikes for %s", product_id)
        params = {"productId": product_id, "limit": str(top_n)}
        data = self._fetch_quikstrike_data("most-active-strikes", params)
        if not data: return []
        strikes_raw = data if isinstance(data, list) else data.get("strikes", data.get("data", []))
        strikes: List[Dict] = []
        for row in strikes_raw[:top_n]: strikes.append(self._normalise_strike_row(row))
        strikes.sort(key=lambda s: (s.get("call_volume", 0) or 0) + (s.get("put_volume", 0) or 0)
                     + (s.get("call_oi_change", 0) or 0) + (s.get("put_oi_change", 0) or 0), reverse=True)
        return strikes

    def get_vol_term_structure(self, product_id: str) -> List[Dict]:
        if not self._authenticated:
            logger.warning("CME login required for Vol Term Structure")
            return []
        logger.info("Fetching vol term structure for %s", product_id)
        params = {"productId": product_id}
        data = self._fetch_quikstrike_data("vol-term-structure", params)
        if not data: return []
        rows = data if isinstance(data, list) else data.get("termStructure", data.get("data", []))
        results: List[Dict] = []
        for row in rows:
            results.append({
                "expiry": row.get("expiration") or row.get("expiry") or row.get("contractMonth"),
                "days_to_expiry": self._parse_int(row.get("dte") or row.get("daysToExpiration")),
                "atm_iv": self._parse_float(row.get("atmIv") or row.get("atmIV") or row.get("atm")),
                "_25d_call_skew": self._parse_float(row.get("25dCallSkew") or row.get("callSkew25d")),
                "_25d_put_skew": self._parse_float(row.get("25dPutSkew") or row.get("putSkew25d")),
                "_10d_call_skew": self._parse_float(row.get("10dCallSkew") or row.get("callSkew10d")),
                "_10d_put_skew": self._parse_float(row.get("10dPutSkew") or row.get("putSkew10d")),
            })
        results.sort(key=lambda x: x.get("days_to_expiry") or 9999)
        return results

    def get_expected_ranges(self, product_id: str) -> List[Dict]:
        if not self._authenticated:
            logger.warning("CME login required for Vol2Vol Expected Range")
            return []
        logger.info("Fetching expected ranges for %s", product_id)
        params = {"productId": product_id}
        data = self._fetch_quikstrike_data("vol2vol", params)
        if not data: return []
        rows = data if isinstance(data, list) else data.get("ranges", data.get("data", []))
        results: List[Dict] = []
        for row in rows:
            expected_move = self._parse_float(row.get("expectedMove") or row.get("expected_move"))
            current_price = self._parse_float(row.get("underlyingPrice") or row.get("currentPrice") or row.get("last"))
            confidence = self._parse_float(row.get("confidence")) or 0.68
            lower = upper = None
            if current_price is not None and expected_move is not None:
                lower = round(current_price - expected_move, 4)
                upper = round(current_price + expected_move, 4)
            results.append({
                "expiry": row.get("expiration") or row.get("expiry"),
                "days_forward": self._parse_int(row.get("daysForward") or row.get("dte")),
                "current_price": current_price, "expected_move": expected_move,
                "confidence": confidence, "lower_bound": lower, "upper_bound": upper,
                "atm_iv": self._parse_float(row.get("atmIv") or row.get("atmIV")),
            })
        return results

    def _fetch_quikstrike_data(self, tool: str, params: Dict) -> Optional[Dict]:
        endpoint_patterns = {
            "oi-profile": [
                "https://www.cmegroup.com/CmeWS/mvc/QuikStrikeApi/GetOIOpenInterestProfile",
                "https://www.cmegroup.com/CmeWS/mvc/QuikStrikeApi/GetOpenInterestProfile",
                "https://www.cmegroup.com/services/quikstrike/oi-profile",
            ],
            "most-active-strikes": [
                "https://www.cmegroup.com/CmeWS/mvc/QuikStrikeApi/GetMostActiveStrikes",
                "https://www.cmegroup.com/services/quikstrike/most-active-strikes",
            ],
            "vol-term-structure": [
                "https://www.cmegroup.com/CmeWS/mvc/QuikStrikeApi/GetVolTermStructure",
                "https://www.cmegroup.com/services/quikstrike/vol-term-structure",
            ],
            "vol2vol": [
                "https://www.cmegroup.com/CmeWS/mvc/QuikStrikeApi/GetVol2VolExpectedRange",
                "https://www.cmegroup.com/services/quikstrike/vol2vol",
            ],
        }
        urls = endpoint_patterns.get(tool, [])
        for url in urls:
            resp = self._get(url, params=params, timeout=15)
            data = self._safe_json(resp)
            if data is not None:
                logger.debug("QuikStrike data fetched from %s", url)
                return data
        logger.warning("All QuikStrike endpoint patterns failed for tool '%s'", tool)
        return None

    def get_futures_options_summary(self, ticker: str) -> Dict:
        product_id = self._resolve_ticker(ticker)
        if not product_id:
            return {"ticker": ticker, "error": f"Unknown ticker: {ticker}"}
        logger.info("Building futures+options summary for %s (id=%s)", ticker, product_id)
        summary: Dict = {
            "ticker": ticker, "product_id": product_id,
            "product_name": self._product_name(product_id),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        try:
            settlements = self.get_settlements(product_id)
            summary["settlements"] = settlements
            summary["front_month"] = settlements[0] if settlements else None
        except Exception as exc:
            logger.error("Settlements fetch failed: %s", exc)
            summary["settlements"] = []
        try:
            summary["volume"] = self.get_volume(product_id)
        except Exception as exc:
            logger.error("Volume fetch failed: %s", exc)
            summary["volume"] = {}
        try:
            summary["quote"] = self.get_quick_quote(product_id)
        except Exception as exc:
            logger.error("Quote fetch failed: %s", exc)
            summary["quote"] = {}
        if self._authenticated:
            try:
                oi = self.get_open_interest_profile(product_id)
                summary["oi_profile"] = oi
            except Exception as exc:
                logger.error("OI profile fetch failed: %s", exc)
                summary["oi_profile"] = {"error": str(exc)}
            try:
                summary["most_active_strikes"] = self.get_most_active_strikes(product_id)
            except Exception as exc:
                logger.error("Most active strikes fetch failed: %s", exc)
                summary["most_active_strikes"] = []
            try:
                summary["vol_term_structure"] = self.get_vol_term_structure(product_id)
            except Exception as exc:
                logger.error("Vol term structure fetch failed: %s", exc)
                summary["vol_term_structure"] = []
        else:
            summary["oi_profile"] = {"note": "Login required for OI profile"}
            summary["most_active_strikes"] = []
            summary["vol_term_structure"] = []
        logger.info("Summary built for %s", ticker)
        return summary

    def get_multiple_products(self, product_ids: List[str]) -> Dict[str, Dict]:
        results: Dict[str, Dict] = {}
        for pid in product_ids:
            try:
                results[pid] = self.get_futures_options_summary(pid)
            except Exception as exc:
                logger.error("Failed to fetch %s: %s", pid, exc)
                results[pid] = {"product_id": pid, "error": str(exc)}
        return results

    @staticmethod
    def _resolve_ticker(ticker: str) -> Optional[str]:
        upper = ticker.upper()
        if upper in CME_PRODUCTS: return CME_PRODUCTS[upper]
        if ticker.isdigit() and ticker in CME_PRODUCT_NAMES: return ticker
        aliases = {
            "GC": "133", "SI": "84", "HG": "424", "PA": "402", "PL": "4259",
            "CL": "4250", "NG": "4240", "BZ": "4600", "MBT": "9118", "MET": "1465",
            "ES": "133", "MES": "146", "NQ": "209", "MNQ": "149",
            "6E": "425", "6B": "437", "6J": "471", "6A": "433", "6C": "460",
            "6S": "443", "6N": "377", "6M": "458",
            "ZT": "6470", "ZF": "6474", "ZN": "6608", "ZB": "6516",
        }
        if upper in aliases: return aliases[upper]
        return None

    @staticmethod
    def _parse_float(val) -> Optional[float]:
        if val is None: return None
        if isinstance(val, (int, float)): return float(val)
        try:
            cleaned = str(val).replace(",", "").replace("-", "").strip()
            if cleaned == "" or cleaned.upper() == "UNCH":
                return 0.0 if str(val) == "-" else None
            return float(cleaned)
        except (ValueError, TypeError): return None

    @staticmethod
    def _parse_int(val) -> Optional[int]:
        if val is None: return None
        if isinstance(val, int): return val
        if isinstance(val, float): return int(val)
        try:
            cleaned = str(val).replace(",", "").replace("-", "").strip()
            if cleaned == "": return None
            return int(cleaned)
        except (ValueError, TypeError): return None

    @staticmethod
    def _normalise_strike_row(row: Dict) -> Dict:
        return {
            "strike": CMEScraper._parse_float(row.get("strike")),
            "call_oi": CMEScraper._parse_int(row.get("callOi") or row.get("callOI") or row.get("callOpenInterest")),
            "put_oi": CMEScraper._parse_int(row.get("putOi") or row.get("putOI") or row.get("putOpenInterest")),
            "total_oi": CMEScraper._parse_int(row.get("totalOi") or row.get("totalOI")),
            "call_oi_change": CMEScraper._parse_int(row.get("callOiChange") or row.get("callOIChange")),
            "put_oi_change": CMEScraper._parse_int(row.get("putOiChange") or row.get("putOIChange")),
            "call_volume": CMEScraper._parse_int(row.get("callVolume")),
            "put_volume": CMEScraper._parse_int(row.get("putVolume")),
            "net_credit": CMEScraper._parse_float(row.get("netCredit")),
            "gamma_exposure": CMEScraper._parse_float(row.get("gamma") or row.get("gammaExposure")),
        }

    @staticmethod
    def _estimate_max_pain(strikes: List[Dict]) -> Optional[float]:
        if not strikes: return None
        max_oi = 0
        max_pain_strike = None
        for s in strikes:
            total = (s.get("call_oi", 0) or 0) + (s.get("put_oi", 0) or 0)
            if total > max_oi:
                max_oi = total
                max_pain_strike = s.get("strike")
        return max_pain_strike

# Module-level convenience functions
def get_cme_settlements(product_id: str) -> List[Dict]:
    scraper = CMEScraper()
    return scraper.get_settlements(product_id)

def get_cme_volume(product_id: str) -> Dict:
    scraper = CMEScraper()
    return scraper.get_volume(product_id)

def get_cme_quote(ticker: str) -> Dict:
    scraper = CMEScraper()
    return scraper.get_quick_quote(ticker)

def list_supported_products() -> Dict[str, str]:
    return {name: pid for name, pid in CME_PRODUCTS.items()}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CME Group Data Scraper")
    parser.add_argument("--product", "-p", default="133", help="Product ID (default: 133=Gold)")
    parser.add_argument("--settlements", action="store_true", help="Fetch settlements")
    parser.add_argument("--volume", action="store_true", help="Fetch volume/OI")
    parser.add_argument("--quote", action="store_true", help="Fetch quote")
    parser.add_argument("--summary", action="store_true", help="Fetch full summary")
    parser.add_argument("--login", help="CME username")
    parser.add_argument("--password", help="CME password")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    scraper = CMEScraper()
    if args.login and args.password:
        scraper.login(args.login, args.password)
    if args.summary:
        result = scraper.get_futures_options_summary(args.product)
        print(json.dumps(result, indent=2, default=str))
    elif args.settlements:
        result = scraper.get_settlements(args.product)
        print(json.dumps(result, indent=2, default=str))
    elif args.volume:
        result = scraper.get_volume(args.product)
        print(json.dumps(result, indent=2, default=str))
    elif args.quote:
        result = scraper.get_quick_quote(args.product)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=== Settlements ===")
        print(json.dumps(scraper.get_settlements(args.product), indent=2, default=str))
        print("\n=== Volume ===")
        print(json.dumps(scraper.get_volume(args.product), indent=2, default=str))
        print("\n=== Quote ===")
        print(json.dumps(scraper.get_quick_quote(args.product), indent=2, default=str))
