"""commodities.py — Commodities page (with COT overlay)"""
from pages_lib.market_page_base import render_market_page

def render(snap):
    render_market_page(snap, "commodity", "Commodities", "🛢️", show_options=True, show_cot=True)
