import pandas as pd
import streamlit as st

from frontend.api import api_get


def render() -> None:
    st.title("📈 Analytics")

    # ── Summary metrics ────────────────────────────────────────────────────────
    summary = api_get("/analytics/summary")
    if summary:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"₹{summary['total_revenue']:,.2f}")
        c2.metric("Total Profit", f"₹{summary['total_profit']:,.2f}")
        c3.metric("Total Sales", summary["total_sales"])
        c4.metric("Top Product", summary.get("top_product") or "—")

    st.divider()

    col_left, col_right = st.columns(2)

    # ── Sales trend ────────────────────────────────────────────────────────────
    with col_left:
        st.subheader("Sales Trend")
        trend = api_get("/analytics/sales-trend")
        if trend:
            df = pd.DataFrame(trend).set_index("date")
            st.line_chart(df["sales_count"], use_container_width=True)
        else:
            st.info("No sales trend data yet.")

    # ── Revenue trend ──────────────────────────────────────────────────────────
    with col_right:
        st.subheader("Revenue Trend")
        rev_trend = api_get("/analytics/revenue-trend")
        if rev_trend:
            df = pd.DataFrame(rev_trend).set_index("date")
            st.line_chart(df["revenue"], use_container_width=True)
        else:
            st.info("No revenue trend data yet.")

    col_left2, col_right2 = st.columns(2)

    # ── Top products ───────────────────────────────────────────────────────────
    with col_left2:
        st.subheader("Top Products by Volume")
        top = api_get("/analytics/top-products")
        if top:
            df = pd.DataFrame(top).set_index("product_name")[["quantity_sold"]]
            df.columns = ["Units Sold"]
            st.bar_chart(df, use_container_width=True)
        else:
            st.info("No product sales data yet.")

    # ── Category performance ───────────────────────────────────────────────────
    with col_right2:
        st.subheader("Revenue by Category")
        cat = api_get("/analytics/category-performance")
        if cat:
            df = pd.DataFrame(cat).set_index("category")[["revenue"]]
            df.columns = ["Revenue (₹)"]
            st.bar_chart(df, use_container_width=True)
        else:
            st.info("No category performance data yet.")
