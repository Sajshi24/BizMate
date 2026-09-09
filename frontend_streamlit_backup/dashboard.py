"""BizMate — main Streamlit entry point with sidebar navigation and overview dashboard."""

import sys
from pathlib import Path

# Ensure project root is in sys.path so all frontend.* imports resolve correctly
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests
import streamlit as st

from frontend.api import API_BASE, api_get
from frontend.pages import (
    advisor_page,
    analytics_page,
    finance_page,
    inventory_page,
    marketing_page,
    sales_page,
)

st.set_page_config(
    page_title="BizMate — Smart Business Assistant",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "📊 Overview": "overview",
    "📦 Products & Inventory": "inventory",
    "💰 Sales": "sales",
    "📈 Analytics": "analytics",
    "💵 Finance": "finance",
    "📢 Marketing Studio": "marketing",
    "🤖 AI Advisor": "advisor",
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
logo_path = Path(__file__).parent / "assets" / "logo.png"
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)

st.sidebar.title("BizMate")
st.sidebar.caption("AI-Powered Business Assistant")
st.sidebar.divider()

page = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

st.sidebar.divider()
_db_status = "unknown"
try:
    _hr = requests.get(f"{API_BASE}/health", timeout=2)
    if _hr.ok:
        _db_status = _hr.json().get("checks", {}).get("database", "unknown")
except Exception:
    _db_status = "offline"
_icon = "🟢" if _db_status == "connected" else "🔴"
st.sidebar.caption(f"{_icon} Database: {_db_status}")
st.sidebar.caption(f"🔗 API: {API_BASE}")

# ── Page routing ───────────────────────────────────────────────────────────────
page_key = PAGES[page]

if page_key == "overview":
    st.title("📊 Business Overview")

    finance = api_get("/finance/dashboard")
    analytics = api_get("/analytics/summary")
    inv_health = api_get("/inventory/health")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("💵 Finance")
        if finance:
            st.metric("Total Revenue", f"₹{finance['revenue']:,.2f}")
            st.metric("Total Profit", f"₹{finance['profit']:,.2f}")
            st.metric("Profit Margin", f"{finance['profit_margin']:.1f}%")
            st.metric("Sales Count", finance["total_sales"])
        else:
            st.info("No finance data yet.")

    with col2:
        st.subheader("📈 Analytics")
        if analytics:
            st.metric("Total Sales", analytics["total_sales"])
            st.metric("Total Revenue", f"₹{analytics['total_revenue']:,.2f}")
            st.metric("Top Product", analytics.get("top_product") or "—")
            st.metric("Best Category", analytics.get("best_category") or "—")
        else:
            st.info("No analytics data yet.")

    with col3:
        st.subheader("📦 Inventory")
        if inv_health:
            st.metric("Total Products", inv_health["total_products"])
            st.metric("Healthy Stock", inv_health["healthy_products"])
            st.metric("Low Stock", inv_health["low_stock_products"])
            st.metric("Out of Stock", inv_health["out_of_stock_products"])
            score = inv_health["health_score"]
            st.progress(score / 100, text=f"Health Score: {score:.1f}%")
        else:
            st.info("No inventory data yet.")

elif page_key == "inventory":
    inventory_page.render()

elif page_key == "sales":
    sales_page.render()

elif page_key == "analytics":
    analytics_page.render()

elif page_key == "finance":
    finance_page.render()

elif page_key == "marketing":
    marketing_page.render()

elif page_key == "advisor":
    advisor_page.render()
