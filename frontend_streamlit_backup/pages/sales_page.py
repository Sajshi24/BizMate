import pandas as pd
import streamlit as st

from frontend.api import api_get, api_post


def render() -> None:
    st.title("💰 Sales")

    tab_history, tab_new = st.tabs(["Sales History", "Record Sale"])

    # ── Sales history ──────────────────────────────────────────────────────────
    with tab_history:
        sales = api_get("/sales")
        if sales:
            df = pd.DataFrame(sales)
            df["sale_date"] = pd.to_datetime(df["sale_date"]).dt.strftime("%Y-%m-%d %H:%M")
            df = df[["product_name", "quantity", "unit_price", "revenue", "cost", "profit", "sale_date"]]
            df.columns = ["Product", "Qty", "Unit Price (₹)", "Revenue (₹)", "Cost (₹)", "Profit (₹)", "Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            total_rev = sum(s["revenue"] for s in sales)
            total_profit = sum(s["profit"] for s in sales)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Transactions", len(sales))
            c2.metric("Total Revenue", f"₹{total_rev:,.2f}")
            c3.metric("Total Profit", f"₹{total_profit:,.2f}")
        else:
            st.info("No sales recorded yet. Use **Record Sale** to add your first sale.")

    # ── Record sale ────────────────────────────────────────────────────────────
    with tab_new:
        st.subheader("Record a Sale")
        products = api_get("/products")

        if not products:
            st.warning("No products available. Add products in the Products & Inventory section first.")
            return

        in_stock = [p for p in products if p["stock"] > 0]
        if not in_stock:
            st.warning("All products are out of stock.")
            return

        product_map = {p["name"]: p for p in in_stock}

        with st.form("record_sale_form"):
            product_name = st.selectbox("Select Product", list(product_map.keys()))
            selected = product_map[product_name]

            st.caption(
                f"Available stock: **{selected['stock']}** | "
                f"Price: **₹{selected['selling_price']:.2f}**"
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                max_value=selected["stock"],
                step=1,
            )

            preview_revenue = quantity * selected["selling_price"]
            preview_profit = quantity * (selected["selling_price"] - selected["cost_price"])
            st.caption(
                f"Expected revenue: ₹{preview_revenue:.2f} | Expected profit: ₹{preview_profit:.2f}"
            )

            if st.form_submit_button("Record Sale", type="primary"):
                result = api_post("/sales", json={
                    "product_id": selected["product_id"],
                    "quantity": quantity,
                })
                if result:
                    st.success(
                        f"✅ Sale recorded! Revenue: ₹{result['revenue']:.2f} | "
                        f"Profit: ₹{result['profit']:.2f}"
                    )
                    st.rerun()
