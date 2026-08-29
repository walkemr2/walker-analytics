from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Walker Analytics | Sector Flow Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard"
)

DATA_DIR = BASE_DIR / "data_processed"

SNAPSHOT_FILE = DATA_DIR / "web_asset_snapshot.csv"
PRICE_FILE = DATA_DIR / "sector_prices.csv"
MA_WIDE_FILE = DATA_DIR / "moving_average_wide.csv"
REFRESH_FILE = DATA_DIR / "web_refresh_log.csv"

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    snapshot = pd.read_csv(SNAPSHOT_FILE)
    prices = pd.read_csv(PRICE_FILE)
    ma_wide = pd.read_csv(MA_WIDE_FILE)
    refresh = pd.read_csv(REFRESH_FILE)

    return snapshot, prices, ma_wide, refresh


snapshot, prices, ma_wide, refresh = load_data()

# ============================================================
# GLOBAL HEADER
# ============================================================

st.title("Walker Analytics")
st.caption(
    "Python-powered market intelligence and sector-rotation decision support."
)

# ============================================================
# NAVIGATION
# ============================================================

page = st.sidebar.radio(
    "Navigation",
    [
        "Command Center",
        "Asset Explorer",
        "Rotation Analysis",
        "Methodology"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Portfolio demonstration project. "
    "For analytical and educational purposes only."
)

# ============================================================
# COMMAND CENTER
# ============================================================

if page == "Command Center":

    st.header("Sector Flow Decision Support System")

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

    st.subheader("Trend Structure")

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

    st.divider()

    st.subheader("Current Strong Uptrends")

    leaders = snapshot[
        snapshot["Trend_Structure"] == "Strong Uptrend"
    ].copy()

    leader_cols = [
        c for c in [
            "Ticker",
            "Price",
            "Return_1M",
            "Return_3M",
            "Pct_Above_EMA20",
            "Pct_Above_50",
            "Pct_Above_200",
            "Trend_Structure"
        ]
        if c in leaders.columns
    ]

    st.dataframe(
        leaders[leader_cols],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ASSET EXPLORER
# ============================================================

elif page == "Asset Explorer":

    st.header("Asset Explorer")

    tickers = sorted(
        snapshot["Ticker"]
        .dropna()
        .unique()
    )

    selected_ticker = st.selectbox(
        "Select Asset",
        tickers
    )

    asset = snapshot[
        snapshot["Ticker"] == selected_ticker
    ].iloc[0]

    # --------------------------------------------------------
    # SUMMARY METRICS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    price_value = asset.get("Price")
    return_1m = asset.get("Return_1M")
    return_3m = asset.get("Return_3M")

    col1.metric(
        "Current Price",
        f"${price_value:.2f}"
        if pd.notna(price_value)
        else "N/A"
    )

    col2.metric(
        "Trend Structure",
        asset.get("Trend_Structure", "N/A")
    )

    col3.metric(
        "1 Month Return",
        f"{return_1m:.2%}"
        if pd.notna(return_1m)
        else "N/A"
    )

    col4.metric(
        "3 Month Return",
        f"{return_3m:.2%}"
        if pd.notna(return_3m)
        else "N/A"
    )

    st.divider()

    # --------------------------------------------------------
    # MOVING AVERAGE STATUS
    # --------------------------------------------------------

    st.subheader("Moving Average Positioning")

    ma_definitions = [
        ("EMA20", "AboveEMA20", "Pct_Above_EMA20"),
        ("MA30", "Above30", "Pct_Above_30"),
        ("MA50", "Above50", "Pct_Above_50"),
        ("MA100", "Above100", "Pct_Above_100"),
        ("MA200", "Above200", "Pct_Above_200"),
    ]

    ma_rows = []

    for ma_name, above_name, pct_name in ma_definitions:

        ma_value = asset.get(ma_name)
        above_value = asset.get(above_name)
        pct_value = asset.get(pct_name)

        if pd.isna(ma_value):
            continue

        if above_value is True:
            position = "ABOVE"
        elif above_value is False:
            position = "BELOW"
        else:
            position = "N/A"

        ma_rows.append(
            {
                "Indicator": ma_name,
                "Value": ma_value,
                "Position": position,
                "Distance": pct_value
            }
        )

    ma_table = pd.DataFrame(ma_rows)

    if not ma_table.empty:

        display_ma = ma_table.copy()

        display_ma["Value"] = display_ma["Value"].map(
            lambda x: f"${x:.2f}"
            if pd.notna(x)
            else "N/A"
        )

        display_ma["Distance"] = display_ma["Distance"].map(
            lambda x: f"{x:.2%}"
            if pd.notna(x)
            else "N/A"
        )

        st.dataframe(
            display_ma,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # PRICE + MA CHART
    # --------------------------------------------------------

    st.subheader("Price and Moving Average History")

    date_col_prices = prices.columns[0]
    date_col_ma = ma_wide.columns[0]

    prices[date_col_prices] = pd.to_datetime(
        prices[date_col_prices]
    )

    ma_wide[date_col_ma] = pd.to_datetime(
        ma_wide[date_col_ma]
    )

    fig_ma = go.Figure()

    if selected_ticker in prices.columns:

        fig_ma.add_trace(
            go.Scatter(
                x=prices[date_col_prices],
                y=prices[selected_ticker],
                mode="lines",
                name="Price"
            )
        )

    ma_columns = {
        "EMA20": f"{selected_ticker}_EMA20",
        "MA30": f"{selected_ticker}_30",
        "MA50": f"{selected_ticker}_50",
        "MA100": f"{selected_ticker}_100",
        "MA200": f"{selected_ticker}_200",
    }

    for label, col in ma_columns.items():

        if col in ma_wide.columns:

            fig_ma.add_trace(
                go.Scatter(
                    x=ma_wide[date_col_ma],
                    y=ma_wide[col],
                    mode="lines",
                    name=label
                )
            )

    fig_ma.update_layout(
        title=f"{selected_ticker} — Price and Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode="x unified",
        legend_title="Series"
    )

    st.plotly_chart(
        fig_ma,
        use_container_width=True
    )

    st.divider()

    st.subheader("Asset Snapshot")

    st.dataframe(
        snapshot[
            snapshot["Ticker"] == selected_ticker
        ],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ROTATION ANALYSIS
# ============================================================

elif page == "Rotation Analysis":

    st.header("Rotation Analysis")

    st.info(
        "This section will integrate momentum, acceleration, "
        "rotation readiness, leadership deterioration, breadth, "
        "and market-regime analytics from the broader decision-support system."
    )

    st.subheader("Coming Next")

    st.markdown(
        """
        - Momentum leaders
        - Acceleration candidates
        - Rotation readiness
        - Leadership deterioration
        - Market breadth
        - Regime alignment
        - Decision-engine outputs
        """
    )


# ============================================================
# METHODOLOGY
# ============================================================

elif page == "Methodology":

    st.header("System Methodology")

    st.subheader("Current Analytical Flow")

    st.markdown(
        """
        1. Market price data is acquired through an automated Python pipeline.
        2. Historical returns are calculated across multiple time horizons.
        3. EMA20 and 30/50/100/200-day moving averages are calculated.
        4. Asset trend structure is classified from moving-average positioning.
        5. Processed outputs are consolidated into a dedicated web analytics layer.
        6. Streamlit presents the results through an interactive decision-support interface.
        """
    )

    st.divider()

    st.subheader("Architecture")

    st.markdown(
        """
        **Market Data**

        ↓

        **Python Data Pipeline**

        ↓

        **Return + Moving Average Engine**

        ↓

        **Web Analytics Layer**

        ↓

        **Streamlit Application**

        ↓

        **Walker Analytics**
        """
    )

    st.divider()

    st.subheader("Design Principle")

    st.write(
        "The public web application is intentionally separated from "
        "the operational Excel-based decision-support system. "
        "This allows the portfolio application to evolve independently "
        "without interfering with day-to-day execution."
    )