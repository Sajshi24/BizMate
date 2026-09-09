import streamlit as st

from frontend.api import api_get, api_post


def render() -> None:
    st.title("📢 Marketing Studio")

    tab_caption, tab_hashtag, tab_campaign, tab_calendar, tab_poster, tab_insights = st.tabs([
        "Captions", "Hashtags", "Campaign", "Calendar", "Poster", "AI Insights",
    ])

    # ── Social captions ────────────────────────────────────────────────────────
    with tab_caption:
        st.subheader("Generate Social Media Captions")
        with st.form("caption_form"):
            col1, col2 = st.columns(2)
            product_name = col1.text_input("Product Name *", key="cap_product")
            offer = col2.text_input("Offer *", placeholder="e.g. 20% off this weekend", key="cap_offer")
            target_audience = st.text_input("Target Audience", placeholder="e.g. families, young adults", key="cap_audience")

            if st.form_submit_button("Generate Captions", type="primary"):
                if not product_name.strip() or not offer.strip():
                    st.error("Product name and offer are required.")
                else:
                    with st.spinner("Generating captions..."):
                        result = api_post("/marketing/caption", json={
                            "product_name": product_name.strip(),
                            "offer": offer.strip(),
                            "target_audience": target_audience.strip() or None,
                        })
                    if result and result.get("success"):
                        st.subheader("Generated Captions")
                        with st.expander("📸 Instagram", expanded=True):
                            st.write(result["instagram"])
                        with st.expander("👥 Facebook"):
                            st.write(result["facebook"])
                        with st.expander("💼 LinkedIn"):
                            st.write(result["linkedin"])
                        with st.expander("💬 WhatsApp Business"):
                            st.write(result["whatsapp_business"])

    # ── Hashtags ───────────────────────────────────────────────────────────────
    with tab_hashtag:
        st.subheader("Generate Marketing Hashtags")
        with st.form("hashtag_form"):
            col1, col2 = st.columns(2)
            product_name_ht = col1.text_input("Product Name *", key="ht_product")
            keywords_raw = col2.text_input("Keywords *", placeholder="organic, fresh, local (comma-separated)", key="ht_keywords")

            if st.form_submit_button("Generate Hashtags", type="primary"):
                if not product_name_ht.strip() or not keywords_raw.strip():
                    st.error("Product name and at least one keyword are required.")
                else:
                    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
                    with st.spinner("Generating hashtags..."):
                        result = api_post("/marketing/hashtags", json={
                            "product_name": product_name_ht.strip(),
                            "keywords": keywords,
                        })
                    if result and result.get("success"):
                        st.subheader("Generated Hashtags")
                        hashtags_text = "  ".join(result["hashtags"])
                        st.markdown(f"**{hashtags_text}**")
                        st.code(" ".join(result["hashtags"]), language=None)

    # ── Campaign ───────────────────────────────────────────────────────────────
    with tab_campaign:
        st.subheader("Generate a Marketing Campaign")
        with st.form("campaign_form"):
            col1, col2 = st.columns(2)
            product_name_cp = col1.text_input("Product Name *", key="cp_product")
            offer_cp = col2.text_input("Offer *", key="cp_offer", placeholder="e.g. Buy 2 Get 1 Free")
            target_audience_cp = col1.text_input("Target Audience *", key="cp_audience")
            theme_cp = col2.text_input("Theme", key="cp_theme", placeholder="e.g. Festive, Summer Sale")

            if st.form_submit_button("Generate Campaign", type="primary"):
                if not product_name_cp.strip() or not offer_cp.strip() or not target_audience_cp.strip():
                    st.error("Product name, offer, and target audience are required.")
                else:
                    with st.spinner("Generating campaign..."):
                        result = api_post("/marketing/campaign", json={
                            "product_name": product_name_cp.strip(),
                            "offer": offer_cp.strip(),
                            "target_audience": target_audience_cp.strip(),
                            "theme": theme_cp.strip() or None,
                        })
                    if result and result.get("success"):
                        st.subheader(f"🎯 {result['campaign_title']}")
                        st.markdown(f"*{result['slogan']}*")
                        st.divider()
                        st.markdown(f"**Objective:** {result['objective']}")
                        st.markdown(f"**Target Audience:** {result['target_audience']}")
                        st.markdown(f"**Promotional Message:** {result['promotional_message']}")
                        st.markdown(f"**Campaign Description:** {result['campaign_description']}")

    # ── Campaign calendar ──────────────────────────────────────────────────────
    with tab_calendar:
        st.subheader("Generate Campaign Calendar Ideas")
        with st.form("calendar_form"):
            col1, col2, col3 = st.columns(3)
            calendar_type = col1.selectbox(
                "Calendar Type *",
                ["daily", "weekly", "monthly", "festival", "seasonal"],
            )
            shop_name = col2.text_input("Shop Name", placeholder="e.g. Krishna General Store")
            focus_product = col3.text_input("Focus Product", placeholder="e.g. Basmati Rice")

            if st.form_submit_button("Generate Ideas", type="primary"):
                with st.spinner("Generating calendar ideas..."):
                    result = api_post("/marketing/calendar", json={
                        "calendar_type": calendar_type,
                        "shop_name": shop_name.strip() or None,
                        "focus_product": focus_product.strip() or None,
                    })
                if result and result.get("success"):
                    st.subheader(f"📅 {calendar_type.title()} Campaign Ideas")
                    for i, idea in enumerate(result["ideas"], 1):
                        with st.expander(f"{i}. {idea['title']}", expanded=i == 1):
                            st.write(idea["description"])
                            channels = ", ".join(idea["suggested_channels"])
                            st.caption(f"📣 Channels: {channels}")
                            st.markdown(f"**CTA:** {idea['call_to_action']}")

    # ── Poster generator ───────────────────────────────────────────────────────
    with tab_poster:
        st.subheader("AI Promotional Poster Generator")
        st.caption("Generates a unique AI-designed poster. Requires a configured image generation API key.")

        with st.form("poster_form"):
            col1, col2 = st.columns(2)
            product_name_ps = col1.text_input("Product Name *", key="ps_product")
            target_audience_ps = col2.text_input("Target Audience *", key="ps_audience")
            offer_ps = col1.text_input("Offer *", key="ps_offer", placeholder="e.g. 30% off")
            theme_ps = col2.text_input("Theme *", key="ps_theme", placeholder="e.g. Diwali, Summer")
            keywords_ps = st.text_input("Keywords *", key="ps_keywords", placeholder="fresh, local, organic")
            product_image = st.file_uploader(
                "Product Image (optional)", type=["jpg", "jpeg", "png", "webp"]
            )

            if st.form_submit_button("Generate Poster", type="primary"):
                if not all([product_name_ps.strip(), target_audience_ps.strip(), offer_ps.strip(), theme_ps.strip(), keywords_ps.strip()]):
                    st.error("All fields except product image are required.")
                else:
                    form_data = {
                        "product_name": product_name_ps.strip(),
                        "keywords": keywords_ps.strip(),
                        "offer": offer_ps.strip(),
                        "theme": theme_ps.strip(),
                        "target_audience": target_audience_ps.strip(),
                    }
                    files = None
                    if product_image:
                        files = {
                            "product_image": (
                                product_image.name,
                                product_image.getvalue(),
                                product_image.type,
                            )
                        }

                    with st.spinner("Generating poster — this may take up to 60 seconds..."):
                        result = api_post("/marketing/poster", data=form_data, files=files)

                    if result:
                        if result.get("success"):
                            st.success("✅ Poster generated!")
                            st.markdown(f"**Headline:** {result['poster_headline']}")
                            st.markdown(f"**Promotional Text:** {result['promotional_text']}")
                            st.markdown(f"**Call to Action:** {result['call_to_action']}")
                            st.caption(f"Style: {result['design_style']}")
                            if result.get("poster_image"):
                                st.image(result["poster_image"], caption="Generated Poster")
                        else:
                            st.error(result.get("error", "Poster generation failed."))
                            if result.get("poster_headline"):
                                st.info(
                                    "Image generation failed, but your design copy was created:\n\n"
                                    f"**Headline:** {result['poster_headline']}\n\n"
                                    f"**Text:** {result['promotional_text']}\n\n"
                                    f"**CTA:** {result['call_to_action']}"
                                )

    # ── AI insights: offers & recommendation ───────────────────────────────────
    with tab_insights:
        st.subheader("AI-Powered Insights")
        st.write("Get data-driven promotional offers and marketing recommendations based on your live business data.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🎁 Promotional Offers")
            st.caption("5 offers tailored to your inventory, sales trends, and margins.")
            if st.button("Generate Offers", type="primary", key="gen_offers"):
                with st.spinner("Analyzing business data..."):
                    result = api_post("/marketing/offers")
                if result and result.get("success"):
                    for offer_item in result["offers"]:
                        with st.expander(f"🏷️ {offer_item['title']}"):
                            st.write(offer_item["description"])
                            st.caption(f"**Type:** {offer_item['offer_type']}")
                            st.caption(f"**Rationale:** {offer_item['rationale']}")

        with col2:
            st.markdown("#### 🎯 Marketing Recommendation")
            st.caption("AI recommendation on which product to promote and how.")
            if st.button("Get Recommendation", type="primary", key="gen_reco"):
                with st.spinner("Analyzing business data..."):
                    result = api_post("/marketing/recommendation")
                if result and result.get("success") and result.get("recommendation"):
                    rec = result["recommendation"]
                    st.markdown(f"**Promote:** {rec['product_to_promote']}")
                    st.markdown(f"**Why:** {rec['reason']}")
                    st.markdown(f"**Expected Impact:** {rec['expected_business_impact']}")
                    st.markdown(f"**Duration:** {rec['suggested_duration']}")
                    st.markdown(f"**Suggested Offer:** {rec['suggested_offer']}")
