from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Walker Analytics | Sector Flow Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(
    r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard"
)

DATA_DIR = BASE_DIR / "data_processed"

SNAPSHOT_FILE = DATA_DIR / "web_asset_snapshot.csv"
PRICE_FILE = DATA_DIR / "sector_prices.csv"
REFRESH_FILE = DATA_DIR / "web_refresh_log.csv"

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    snapshot = pd.read_csv(SNAPSHOT_FILE)
    prices = pd.read_csv(PRICE_FILE)
    refresh = pd.read_csv(REFRESH_FILE)

    return snapshot, prices, refresh


snapshot, prices, refresh = load_data()

# ============================================================
# HEADER
# ============================================================

st.title("Walker Analytics")

st.subheader("Sector Flow Decision Support System")

st.caption(
    "Python-powered market analytics platform demonstrating automated "
    "data pipelines, moving-average analysis, momentum measures, "
    "trend classification, and decision-support visualization."
)

st.info(
    "Portfolio demonstration project. "
    "This application is for analytical and educational purposes only."
)

st.divider()

# ============================================================
# SYSTEM STATUS
# ============================================================

st.header("Market Analytics Snapshot")

latest_refresh = refresh.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Assets Tracked",
    snapshot["Ticker"].nunique()
)

col2.metric(
    "Strong Uptrends",
    (snapshot["Trend_Structure"] == "Strong Uptrend").sum()
)

col3.metric(
    "Uptrends",
    (snapshot["Trend_Structure"] == "Uptrend").sum()
)

col4.metric(
    "Last Data Refresh",
    latest_refresh.get("Refresh_Time", "N/A")
)

st.divider()

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

st.header("Trend Structure")

trend_counts = (
    snapshot["Trend_Structure"]
    .value_counts()
    .reset_index()
)

trend_counts.columns = ["Trend Structure", "Assets"]

fig = px.bar(
    trend_counts,
    x="Trend Structure",
    y="Assets",
    title="Asset Distribution by Trend Structure"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ============================================================
# ASSET EXPLORER
# ============================================================

st.divider()

st.header("Asset Explorer")

tickers = sorted(snapshot["Ticker"].dropna().unique())

selected_ticker = st.selectbox(
    "Select Asset",
    tickers
)

asset = snapshot[
    snapshot["Ticker"] == selected_ticker
].iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Current Price",
    f"${asset['Price']:.2f}"
    if pd.notna(asset.get("Price"))
    else "N/A"
)

col2.metric(
    "Trend Structure",
    asset.get("Trend_Structure", "N/A")
)

col3.metric(
    "1 Month Return",
    f"{asset['Return_1M']:.2%}"
    if pd.notna(asset.get("Return_1M"))
    else "N/A"
)

col4.metric(
    "3 Month Return",
    f"{asset['Return_3M']:.2%}"
    if pd.notna(asset.get("Return_3M"))
    else "N/A"
)

# ============================================================
# MOVING AVERAGES
# ============================================================

st.subheader("Moving Average Positioning")

ma_cols = [
    "EMA20",
    "MA30",
    "MA50",
    "MA100",
    "MA200"
]

ma_display = []

for ma in ma_cols:

    if ma in asset.index and pd.notna(asset[ma]):

        ma_display.append({
            "Indicator": ma,
            "Value": asset[ma]
        })

ma_df = pd.DataFrame(ma_display)

st.dataframe(
    ma_df,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# PRICE HISTORY
# ============================================================

st.subheader("Price History")

date_col = prices.columns[0]

if selected_ticker in prices.columns:

    price_chart = prices[
        [date_col, selected_ticker]
    ].copy()

    price_chart[date_col] = pd.to_datetime(
        price_chart[date_col]
    )

    fig_price = px.line(
        price_chart,
        x=date_col,
        y=selected_ticker,
        title=f"{selected_ticker} Price History"
    )

    st.plotly_chart(
        fig_price,
        use_container_width=True
    )

else:

    st.warning(
        f"No price history found for {selected_ticker}."
    )

# ============================================================
# FULL ASSET TABLE
# ============================================================

st.divider()

st.header("Full Asset Snapshot")

st.dataframe(
    snapshot,
    use_container_width=True
)

# ============================================================
# METHODOLOGY
# ============================================================

st.divider()

st.header("System Methodology")

st.markdown(
    """
### Current Analytical Flow

1. Market price data is downloaded using Python.
2. Historical returns are calculated across multiple time horizons.
3. EMA20 and 30/50/100/200-day moving averages are calculated.
4. Each asset is classified according to its relationship to the major moving averages.
5. The processed results are consolidated into a web-facing asset snapshot.
6. Streamlit presents the analytical outputs through an interactive dashboard.

### Current Architecture

**Market Data**

↓

**Python Data Pipeline**

↓

**Moving Average & Return Calculations**

↓

**Web Analytics Layer**

↓

**Streamlit Dashboard**

↓

**Walker Analytics**
"""
)