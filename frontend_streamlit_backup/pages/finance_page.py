import streamlit as st

from frontend.api import api_get


def render() -> None:
    st.title("💵 Finance")

    data = api_get("/finance/summary")
    if not data:
        st.info("No financial data yet. Record some sales to see finance metrics.")
        return

    margin = (
        round(data["total_profit"] / data["total_revenue"] * 100, 2)
        if data["total_revenue"] > 0
        else 0.0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"₹{data['total_revenue']:,.2f}")
    c2.metric("Total Cost", f"₹{data['total_cost']:,.2f}")
    c3.metric("Total Profit", f"₹{data['total_profit']:,.2f}")
    c4.metric("Profit Margin", f"{margin:.1f}%")

    st.divider()
    st.metric("Total Sales Transactions", data["total_sales"])

    if data["total_revenue"] > 0:
        cost_ratio = round(data["total_cost"] / data["total_revenue"] * 100, 2)
        st.caption(f"Cost ratio: {cost_ratio:.1f}% of revenue")
