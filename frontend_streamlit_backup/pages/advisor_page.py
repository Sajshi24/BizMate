import streamlit as st

from frontend.api import api_get


def render() -> None:
    st.title("🤖 AI Business Advisor")
    st.write(
        "Get actionable, AI-powered business advice based on your current revenue, "
        "profit, inventory health, and sales data."
    )
    st.caption("Requires a configured **GEMINI_API_KEY** and an active MongoDB connection.")

    if st.button("Get Business Advice", type="primary"):
        with st.spinner("Analyzing your business data..."):
            result = api_get("/advisor/advice")

        if result:
            st.divider()
            st.subheader("📋 AI Recommendations")
            st.markdown(result["advice"])
