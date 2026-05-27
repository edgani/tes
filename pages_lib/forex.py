"""forex.py — Forex page (with COT overlay)"""
from pages_lib.market_page_base import render_market_page

def render(snap):
    render_market_page(snap, "forex", "Forex", "💱", show_cot=True)
