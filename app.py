"""
Tim Hortons International Flyer Tracker - Streamlit UI
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from scraper import MARKETS, load_offer_data


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


def format_display_date(value: str | None) -> str:
    if not value:
        return "Not yet"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[:10]
    return parsed.strftime("%b %d, %Y")


def offers_to_df(offers: list[dict]) -> pd.DataFrame:
    if not offers:
        return pd.DataFrame(
            columns=[
                "Image",
                "Month",
                "Offer Start",
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
                "Month Key",
            ]
        )

    df = pd.DataFrame(offers)
    return pd.DataFrame(
        {
            "Image": df.get("image_url", ""),
            "Month": df.get("offer_month", "Unknown"),
            "Offer Start": df.get("offer_start_date", ""),
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
            "Month Key": df.get("offer_month_key", "unknown"),
        }
    )


def month_sort_key(month_label: str) -> str:
    try:
        return datetime.strptime(month_label, "%B %Y").strftime("%Y-%m")
    except ValueError:
        return "9999-99"


def render_market_section(
    market: dict,
    query: str,
    selected_months: list[str],
    selected_retailers: list[str],
) -> None:
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

    if selected_months and not df.empty:
        df = df[df["Month"].isin(selected_months)]

    if selected_retailers and not df.empty:
        df = df[df["Retailer"].isin(selected_retailers)]

    with st.container():
        left, right = st.columns([4, 1])
        with left:
            st.subheader(market["name"])
        with right:
            st.metric("Offers", len(df))

        if df.empty:
            st.info("No offers loaded yet.")
            return

        visible_columns = [
            "Image",
            "Month",
            "Offer Start",
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
        ]

        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_order=visible_columns,
            column_config={
                "Image": st.column_config.ImageColumn("Image", width="small"),
                "Month": st.column_config.TextColumn("Month", width="small"),
                "Offer Start": st.column_config.TextColumn("Start", width="small"),
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
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .th-header {
        display: flex;
        align-items: center;
        gap: .85rem;
        padding-bottom: .85rem;
        margin-bottom: .5rem;
        border-bottom: 1px solid #e5e7eb;
    }
    .th-logo {
        width: 118px;
        flex: 0 0 auto;
        overflow: hidden;
    }
    .th-logo svg {
        width: 118px !important;
        height: auto !important;
        max-height: 32px;
        display: block;
    }
    .th-title h1 {
        font-size: 1.45rem;
        margin: 0;
        line-height: 1.2;
        font-weight: 750;
    }
    .th-title p {
        margin: .2rem 0 0 0;
        color: #6b7280;
        font-size: .9rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem;
    }
    div[data-testid="stMetricLabel"] {
        color: #6b7280;
    }
    .stDownloadButton {
        margin-top: .35rem;
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
            <h1>International Flyer Tracker</h1>
            <p>Tim Hortons CPG offers across Mexico, Saudi Arabia, and Korea</p>
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
    st.header("Filters")
    query = st.text_input("Search", placeholder="Item, retailer, offer detail")

    month_options = (
        sorted(all_df["offer_month"].dropna().unique().tolist(), key=month_sort_key)
        if not all_df.empty and "offer_month" in all_df
        else []
    )
    selected_months = st.multiselect("Month", month_options, default=month_options)

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
metric_cols[3].metric("Last Updated", format_display_date(data.get("last_updated")))

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
    render_market_section(market, query, selected_months, selected_retailers)
