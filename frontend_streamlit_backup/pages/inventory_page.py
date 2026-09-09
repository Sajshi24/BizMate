import pandas as pd
import streamlit as st

from frontend.api import api_delete, api_get, api_post


def render() -> None:
    st.title("📦 Products & Inventory")

    tab_view, tab_add, tab_health = st.tabs(
        ["Product Catalogue", "Add Product", "Inventory Health"]
    )

    # ── Product catalogue ──────────────────────────────────────────────────────
    with tab_view:
        products = api_get("/products")
        if products:
            df = pd.DataFrame(products)[
                ["name", "category", "selling_price", "cost_price", "stock", "minimum_stock", "supplier"]
            ]
            df.columns = ["Name", "Category", "Price (₹)", "Cost (₹)", "Stock", "Min. Stock", "Supplier"]
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Delete Product")
            product_map = {p["name"]: p["product_id"] for p in products}
            to_delete = st.selectbox("Select product", list(product_map.keys()), key="del_select")
            if st.button("🗑️ Delete", type="secondary", key="del_btn"):
                if api_delete(f"/products/{product_map[to_delete]}"):
                    st.success(f"'{to_delete}' deleted successfully.")
                    st.rerun()
        else:
            st.info("No products found. Add your first product in the **Add Product** tab.")

    # ── Add product ────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add New Product")
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Product Name *")
            category = col2.text_input("Category *")
            cost_price = col1.number_input("Cost Price (₹) *", min_value=0.0, step=0.5, format="%.2f")
            selling_price = col2.number_input("Selling Price (₹) *", min_value=0.0, step=0.5, format="%.2f")
            stock = col1.number_input("Stock Quantity *", min_value=0, step=1)
            minimum_stock = col2.number_input("Minimum Stock Level *", min_value=0, step=1)
            supplier = st.text_input("Supplier Name *")

            if st.form_submit_button("Add Product", type="primary"):
                if not name.strip() or not category.strip() or not supplier.strip():
                    st.error("Name, category, and supplier are required.")
                else:
                    result = api_post("/products", json={
                        "name": name.strip(),
                        "category": category.strip(),
                        "cost_price": cost_price,
                        "selling_price": selling_price,
                        "stock": stock,
                        "minimum_stock": minimum_stock,
                        "supplier": supplier.strip(),
                    })
                    if result:
                        st.success(f"✅ '{name}' added successfully!")
                        st.rerun()

    # ── Inventory health ───────────────────────────────────────────────────────
    with tab_health:
        health = api_get("/inventory/health")
        if health:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Products", health["total_products"])
            c2.metric("✅ Healthy", health["healthy_products"])
            c3.metric("⚠️ Low Stock", health["low_stock_products"])
            c4.metric("❌ Out of Stock", health["out_of_stock_products"])
            st.progress(
                health["health_score"] / 100,
                text=f"Inventory Health: {health['health_score']:.1f}%",
            )

        st.subheader("⚠️ Low Stock Alerts")
        low = api_get("/inventory/low-stock")
        if low:
            df = pd.DataFrame(low)[["name", "category", "stock", "minimum_stock"]]
            df.columns = ["Product", "Category", "Stock", "Min. Stock"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif low is not None:
            st.success("All products are well-stocked.")

        st.subheader("📋 Restock Suggestions")
        suggestions = api_get("/inventory/restock-suggestions")
        if suggestions:
            df = pd.DataFrame(suggestions)
            df.columns = ["Product", "Current Stock", "Min. Stock", "Suggested Order Qty"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif suggestions is not None:
            st.success("No restocking required at this time.")
