"""Stub engine - restore from original if needed."""
def get_all_tickers(market='us_equity'):
    if market == 'us_equity': return ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'AMD', 'CRM', 'NFLX']
    elif market == 'ihsg': return ['BBCA.JK', 'BBRI.JK', 'TLKM.JK']
    elif market == 'forex': return ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X', 'USDCAD=X', 'NZDUSD=X']
    elif market == 'crypto': return ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'XRP-USD']
    elif market == 'commodity': return ['GC=F', 'SI=F', 'CL=F', 'NG=F', 'HG=F']
    return []
