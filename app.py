"""
Tim Hortons International Flyer Tracker - Streamlit UI
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from scraper import MARKETS, load_offer_data, scrape_market_to_file


APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "assets" / "tim-hortons-logo.svg"


st.set_page_config(
    page_title="Tim Hortons International Flyer Tracker",
    page_icon=":coffee:",
    layout="wide",
)


def load_logo_svg() -> str:
    try:
        return LOGO_PATH.read_text(encoding="utf-8")
    except OSError:
        return "<strong>Tim Hortons</strong>"


def offers_to_df(offers: list[dict]) -> pd.DataFrame:
    if not offers:
        return pd.DataFrame(
            columns=[
                "Image",
                "Retailer",
                "Item",
                "Price",
                "Regular Price",
                "Discount",
                "Offer Details",
                "Flyer",
                "Product",
                "Flyer Title",
                "Flyer Page",
                "Valid Until",
                "Scraped At",
            ]
        )

    df = pd.DataFrame(offers)
    return pd.DataFrame(
        {
            "Image": df.get("image_url", ""),
            "Retailer": df.get("retailer", ""),
            "Item": df.get("item", ""),
            "Price": df.get("price", ""),
            "Regular Price": df.get("regular_price", ""),
            "Discount": df.get("discount", ""),
            "Offer Details": df.get("offer_details", ""),
            "Flyer": df.get("flyer_url", ""),
            "Product": df.get("product_url", ""),
            "Flyer Title": df.get("flyer_title", ""),
            "Flyer Page": df.get("flyer_page", ""),
            "Valid Until": df.get("valid_until", ""),
            "Scraped At": df.get("scraped_at", ""),
        }
    )


def render_market_section(market: dict, query: str, selected_retailers: list[str]) -> None:
    offers = market.get("offers", [])
    df = offers_to_df(offers)

    if query.strip() and not df.empty:
        needle = query.strip()
        mask = (
            df["Item"].str.contains(needle, case=False, na=False)
            | df["Retailer"].str.contains(needle, case=False, na=False)
            | df["Offer Details"].str.contains(needle, case=False, na=False)
        )
        df = df[mask]

    if selected_retailers and not df.empty:
        df = df[df["Retailer"].isin(selected_retailers)]

    with st.container():
        left, right = st.columns([3, 1])
        with left:
            st.subheader(market["name"])
        with right:
            st.metric("Offers", len(df))

        if df.empty:
            st.info("No offers loaded yet.")
            return

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "Image": st.column_config.ImageColumn("Image", width="small"),
                "Retailer": st.column_config.TextColumn("Retailer", width="medium"),
                "Item": st.column_config.TextColumn("Item", width="large"),
                "Price": st.column_config.TextColumn("Price", width="small"),
                "Regular Price": st.column_config.TextColumn("Regular", width="small"),
                "Discount": st.column_config.TextColumn("Discount", width="small"),
                "Offer Details": st.column_config.TextColumn("Offer Details", width="large"),
                "Flyer": st.column_config.LinkColumn("Flyer", display_text="Open flyer"),
                "Product": st.column_config.LinkColumn("Product", display_text="Open product"),
                "Flyer Title": st.column_config.TextColumn("Flyer Title", width="medium"),
                "Flyer Page": st.column_config.TextColumn("Page", width="small"),
                "Valid Until": st.column_config.TextColumn("Valid Until", width="small"),
                "Scraped At": st.column_config.TextColumn("Scraped At", width="medium"),
            },
        )

        st.download_button(
            f"Download {market['name']} CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"tim_hortons_{market['key'].replace('-', '_')}_offers.csv",
            mime="text/csv",
            key=f"download_{market['key']}",
        )
    st.divider()


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; }
    .th-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: .35rem;
    }
    .th-logo {
        width: 104px;
        flex: 0 0 auto;
    }
    .th-title h1 {
        font-size: 1.95rem;
        margin: 0;
        line-height: 1.15;
    }
    .th-title p {
        margin: .2rem 0 0 0;
        color: #6b7280;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.45rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="th-header">
        <div class="th-logo">{load_logo_svg()}</div>
        <div class="th-title">
            <h1>International CPG Flyer Tracker</h1>
            <p>Mexico | Saudi Arabia | Korea</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

data = load_offer_data()
markets = data.get("markets", [])
all_offers = [offer for market in markets for offer in market.get("offers", [])]
all_df = pd.DataFrame(all_offers)

with st.sidebar:
    st.header("Refresh")
    if st.button("Scrape Saudi Arabia D4D", type="primary"):
        with st.spinner("Scraping D4D and validating flyer links..."):
            data = scrape_market_to_file("saudi-arabia")
            markets = data.get("markets", [])
            all_offers = [offer for market in markets for offer in market.get("offers", [])]
            all_df = pd.DataFrame(all_offers)
        st.success("Saudi Arabia offers updated.")

    st.divider()
    query = st.text_input("Search", placeholder="Item, retailer, offer detail")

    retailer_options = (
        sorted(all_df["retailer"].dropna().unique().tolist())
        if not all_df.empty and "retailer" in all_df
        else []
    )
    selected_retailers = st.multiselect("Retailer", retailer_options, default=retailer_options)

st.divider()

metric_cols = st.columns(4)
metric_cols[0].metric("Total Offers", len(all_offers))
metric_cols[1].metric(
    "Retailers",
    all_df["retailer"].nunique() if not all_df.empty and "retailer" in all_df else 0,
)
metric_cols[2].metric(
    "Markets With Offers",
    sum(1 for market in markets if market.get("offers")),
)
metric_cols[3].metric("Last Updated", data.get("last_updated") or "Not yet")

for market_key in ("mexico", "saudi-arabia", "korea"):
    market = next(
        (
            item
            for item in markets
            if item.get("key") == market_key
        ),
        {
            "key": market_key,
            "name": MARKETS[market_key]["name"],
            "offers": [],
        },
    )
    render_market_section(market, query, selected_retailers)
