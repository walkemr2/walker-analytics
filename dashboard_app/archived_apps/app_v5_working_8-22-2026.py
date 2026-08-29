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
ROTATION_FILE = DATA_DIR / "web_rotation_snapshot.csv"
PRICE_FILE = DATA_DIR / "sector_prices.csv"
MA_WIDE_FILE = DATA_DIR / "moving_average_wide.csv"
REFRESH_FILE = DATA_DIR / "web_refresh_log.csv"

# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():
    snapshot = pd.read_csv(SNAPSHOT_FILE)
    rotation = pd.read_csv(ROTATION_FILE)
    prices = pd.read_csv(PRICE_FILE)
    ma_wide = pd.read_csv(MA_WIDE_FILE)
    refresh = pd.read_csv(REFRESH_FILE)

    return snapshot, rotation, prices, ma_wide, refresh


snapshot, rotation, prices, ma_wide, refresh = load_data()

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
# HELPERS
# ============================================================

def fmt_score(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.1f}"

def fmt_pct(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2%}"

def get_top_state(df, state, n=5, sort_col="Rotation_Readiness_Score"):
    subset = df[df["Rotation_State"] == state].copy()
    if sort_col in subset.columns:
        subset = subset.sort_values(sort_col, ascending=False)
    return subset.head(n)

# ============================================================
# COMMAND CENTER
# ============================================================

if page == "Command Center":

    st.header("Sector Flow Decision Support System")

    latest_refresh = refresh.iloc[-1]

    leaders = rotation[rotation["Rotation_State"] == "LEADER"].copy()
    emerging = rotation[rotation["Rotation_State"] == "EMERGING"].copy()
    weakening = rotation[rotation["Rotation_State"] == "WEAKENING"].copy()

    top_leader = (
        leaders.sort_values("Rotation_Readiness_Score", ascending=False).iloc[0]["Ticker"]
        if not leaders.empty else "N/A"
    )

    top_emerging = (
        emerging.sort_values("Rotation_Readiness_Score", ascending=False).iloc[0]["Ticker"]
        if not emerging.empty else "N/A"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Assets Tracked", rotation["Ticker"].nunique())
    col2.metric("Leaders", len(leaders))
    col3.metric("Emerging", len(emerging))
    col4.metric("Weakening", len(weakening))
    col5.metric("Last Refresh", latest_refresh.get("Refresh_Time", "N/A"))

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Leader")
        st.metric("Highest Rotation Readiness", top_leader)

    with col2:
        st.subheader("Top Emerging Candidate")
        st.metric("Highest Emerging Readiness", top_emerging)

    st.divider()

    st.subheader("Rotation State Distribution")

    state_order = ["LEADER", "EMERGING", "WATCH", "WEAKENING", "LAGGING"]

    state_counts = (
        rotation["Rotation_State"]
        .value_counts()
        .reindex(state_order, fill_value=0)
        .reset_index()
    )
    state_counts.columns = ["Rotation State", "Assets"]

    fig_state = px.bar(
        state_counts,
        x="Rotation State",
        y="Assets",
        title="Asset Distribution by Rotation State"
    )

    st.plotly_chart(fig_state, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Leadership")

        leader_view = get_top_state(rotation, "LEADER", n=8)

        leader_cols = [
            c for c in [
                "Ticker",
                "Momentum_Score",
                "Acceleration_Score",
                "Trend_Score",
                "Rotation_Readiness_Score",
                "Rotation_Readiness_Rank",
            ]
            if c in leader_view.columns
        ]

        st.dataframe(
            leader_view[leader_cols],
            use_container_width=True,
            hide_index=True
        )

    with col2:
        st.subheader("Emerging Rotation")

        emerging_view = get_top_state(rotation, "EMERGING", n=8)

        emerging_cols = [
            c for c in [
                "Ticker",
                "Momentum_Score",
                "Acceleration_Score",
                "Trend_Score",
                "Rotation_Readiness_Score",
                "Rotation_Readiness_Rank",
            ]
            if c in emerging_view.columns
        ]

        st.dataframe(
            emerging_view[emerging_cols],
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# ASSET EXPLORER
# ============================================================

elif page == "Asset Explorer":

    st.header("Asset Explorer")

    tickers = sorted(snapshot["Ticker"].dropna().unique())

    selected_ticker = st.selectbox(
        "Select Asset",
        tickers
    )

    asset = snapshot[
        snapshot["Ticker"] == selected_ticker
    ].iloc[0]

    rotation_row = rotation[
        rotation["Ticker"] == selected_ticker
    ].iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)

    price_value = asset.get("Price")
    return_1m = rotation_row.get("Return_1M")
    return_3m = rotation_row.get("Return_3M")

    col1.metric(
        "Current Price",
        f"${price_value:.2f}" if pd.notna(price_value) else "N/A"
    )

    col2.metric(
        "Trend Structure",
        asset.get("Trend_Structure", "N/A")
    )

    col3.metric(
        "Rotation State",
        rotation_row.get("Rotation_State", "N/A")
    )

    col4.metric(
        "1 Month Return",
        fmt_pct(return_1m)
    )

    col5.metric(
        "3 Month Return",
        fmt_pct(return_3m)
    )

    st.divider()

    st.subheader("Rotation Analytics")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Momentum Score", fmt_score(rotation_row.get("Momentum_Score")))
    c2.metric("Acceleration Score", fmt_score(rotation_row.get("Acceleration_Score")))
    c3.metric("Trend Score", fmt_score(rotation_row.get("Trend_Score")))
    c4.metric("Rotation Readiness", fmt_score(rotation_row.get("Rotation_Readiness_Score")))

    st.divider()

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

        above_text = str(above_value).strip().lower()

        if above_value is True or above_text in {"true", "yes", "1"}:
            position = "ABOVE"
        elif above_value is False or above_text in {"false", "no", "0"}:
            position = "BELOW"
        else:
            position = "N/A"

        ma_rows.append({
            "Indicator": ma_name,
            "Value": ma_value,
            "Position": position,
            "Distance": pct_value
        })

    ma_table = pd.DataFrame(ma_rows)

    if not ma_table.empty:
        display_ma = ma_table.copy()
        display_ma["Value"] = display_ma["Value"].map(
            lambda x: f"${x:.2f}" if pd.notna(x) else "N/A"
        )
        display_ma["Distance"] = display_ma["Distance"].map(
            lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
        )

        st.dataframe(
            display_ma,
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Price and Moving Average History")

    date_col_prices = prices.columns[0]
    date_col_ma = ma_wide.columns[0]

    prices[date_col_prices] = pd.to_datetime(prices[date_col_prices])
    ma_wide[date_col_ma] = pd.to_datetime(ma_wide[date_col_ma])

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

    st.plotly_chart(fig_ma, use_container_width=True)

    st.divider()

    st.subheader("Asset Snapshot")

    asset_cols = [
        c for c in [
            "Ticker",
            "Price",
            "Return_1W",
            "Return_1M",
            "Return_3M",
            "Momentum_Score",
            "Momentum_Rank",
            "Acceleration_Score",
            "Acceleration_Rank",
            "Trend_Score",
            "Rotation_Readiness_Score",
            "Rotation_Readiness_Rank",
            "Rotation_State",
        ]
        if c in rotation.columns
    ]

    st.dataframe(
        rotation.loc[
            rotation["Ticker"] == selected_ticker,
            asset_cols
        ],
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# ROTATION ANALYSIS
# ============================================================

elif page == "Rotation Analysis":

    st.header("Rotation Analysis")

    st.caption(
        "Cross-sectional momentum, acceleration, trend confirmation, "
        "and rotation-readiness analytics."
    )

    leaders = rotation[
        rotation["Rotation_State"] == "LEADER"
    ].sort_values(
        "Rotation_Readiness_Score",
        ascending=False
    )

    emerging = rotation[
        rotation["Rotation_State"] == "EMERGING"
    ].sort_values(
        ["Rotation_Readiness_Score", "Acceleration_Score"],
        ascending=[False, False]
    )

    weakening = rotation[
        rotation["Rotation_State"].isin(["WEAKENING", "LAGGING"])
    ].sort_values(
        "Rotation_Readiness_Score",
        ascending=True
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Leaders", len(leaders))
    col2.metric("Emerging", len(emerging))
    col3.metric("Weakening / Lagging", len(weakening))

    st.divider()

    st.subheader("Leadership")

    display_cols = [
        c for c in [
            "Ticker",
            "Momentum_Score",
            "Momentum_Rank",
            "Acceleration_Score",
            "Trend_Score",
            "Rotation_Readiness_Score",
            "Rotation_Readiness_Rank",
            "Rotation_State"
        ]
        if c in rotation.columns
    ]

    st.dataframe(
        leaders[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Emerging Rotation")

    st.dataframe(
        emerging[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Leadership Risk")

    st.dataframe(
        weakening[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("Rotation Readiness Map")

    fig_rotation = px.scatter(
        rotation,
        x="Momentum_Score",
        y="Acceleration_Score",
        size="Rotation_Readiness_Score",
        hover_name="Ticker",
        hover_data=[
            "Trend_Score",
            "Rotation_Readiness_Score",
            "Rotation_State"
        ],
        title="Momentum vs. Acceleration"
    )

    st.plotly_chart(
        fig_rotation,
        use_container_width=True
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
        4. Trend structure is classified from moving-average positioning.
        5. Momentum and acceleration are evaluated cross-sectionally across the asset universe.
        6. Trend confirmation is combined with momentum and acceleration to derive Rotation Readiness.
        7. Assets are classified as Leader, Emerging, Watch, Weakening, or Lagging.
        8. Processed outputs are published through an interactive Streamlit decision-support interface.
        """
    )

    st.divider()

    st.subheader("Rotation Analytics")

    st.markdown(
        """
        **Momentum Score**

        Measures relative performance persistence across several time horizons.

        **Acceleration Score**

        Measures whether recent momentum is improving or deteriorating relative to longer horizons.

        **Trend Score**

        Uses position relative to EMA20 and the 30/50/100/200-day moving averages to confirm structural trend.

        **Rotation Readiness**

        Combines Momentum, Acceleration, and Trend into a single cross-sectional decision-support score.
        """
    )

    st.divider()

    st.subheader("Architecture")

    st.markdown(
        """
        **Market Data**

        ↓

        **Python Price / Return / MA Pipeline**

        ↓

        **Web Asset Snapshot**

        ↓

        **Rotation Analytics Engine**

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
