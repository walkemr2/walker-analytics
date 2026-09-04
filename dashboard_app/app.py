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

# app.py is located in:
# <project folder>\dashboard_app\app.py

APP_DIR = Path(__file__).resolve().parent

BASE_DIR = APP_DIR.parent

DATA_DIR = BASE_DIR / "data_processed"

SNAPSHOT_FILE = DATA_DIR / "web_asset_snapshot.csv"
ROTATION_FILE = DATA_DIR / "web_rotation_snapshot.csv"
EARLY_FILE = DATA_DIR / "web_early_rotation_snapshot.csv"
PRICE_FILE = DATA_DIR / "sector_prices.csv"
MA_WIDE_FILE = DATA_DIR / "moving_average_wide.csv"
MA_RADAR_FILE = DATA_DIR / "web_ma_wide_snapshot.csv"
REFRESH_FILE = DATA_DIR / "web_refresh_log.csv"
# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=300)
def load_data():
    snapshot = pd.read_csv(SNAPSHOT_FILE)
    rotation = pd.read_csv(ROTATION_FILE)
    early = pd.read_csv(EARLY_FILE)
    prices = pd.read_csv(PRICE_FILE)
    ma_wide = pd.read_csv(MA_WIDE_FILE)
    ma_radar = pd.read_csv(MA_RADAR_FILE)
    refresh = pd.read_csv(REFRESH_FILE)

    return snapshot, rotation, early, prices, ma_wide, ma_radar, refresh


snapshot, rotation, early, prices, ma_wide, ma_radar, refresh = load_data()

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
        "MA / EMA Radar",
        "Asset Explorer",
        "Early Rotation",
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
    # sector_returns.csv stores percentage-point values:
    # 6.98 means +6.98%, not +698%.
    return f"{value:.2f}%"

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

    early_entries = early[early["Early_Rotation_State"] == "EARLY ENTRY"].copy()
    building = early[early["Early_Rotation_State"] == "BUILDING"].copy()
    early_watch = early[early["Early_Rotation_State"] == "EARLY WATCH"].copy()
    extended = early[early["Early_Rotation_State"] == "EXTENDED"].copy()

    top_leader = (
        leaders.sort_values("Rotation_Readiness_Score", ascending=False).iloc[0]["Ticker"]
        if not leaders.empty else "N/A"
    )

    top_emerging = (
        emerging.sort_values("Rotation_Readiness_Score", ascending=False).iloc[0]["Ticker"]
        if not emerging.empty else "N/A"
    )

    top_early = (
        early_entries.sort_values("Early_Rotation_Score", ascending=False).iloc[0]["Ticker"]
        if not early_entries.empty else "N/A"
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Assets Tracked", rotation["Ticker"].nunique())
    col2.metric("Early Entry", len(early_entries))
    col3.metric("Leaders", len(leaders))
    col4.metric("Emerging", len(emerging))
    col5.metric("Weakening", len(weakening))
    col6.metric("Last Refresh", latest_refresh.get("Refresh_Time", "N/A"))

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Top Early Entry")
        st.metric("Highest Early Rotation Score", top_early)

    with col2:
        st.subheader("Top Confirmed Leader")
        st.metric("Highest Confirmed Readiness", top_leader)

    with col3:
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
# MA / EMA RADAR
# ============================================================

elif page == "MA / EMA Radar":

    st.header("MA / EMA Radar")

    st.caption(
        "Whole-universe moving-average radar for identifying recent EMA20 "
        "crosses, assets near the EMA20, trend structure, and developing "
        "rotation opportunities."
    )

    radar = ma_radar.copy()

    # --------------------------------------------------------
    # EMA SIGNAL
    # --------------------------------------------------------

    def ema_signal(row):
        days = row.get("Days_Since_Price_EMA20_Cross")
        cross = row.get("Price_EMA20_Last_Cross")
        pct = row.get("Pct_Above_EMA20")

        if pd.notna(days) and days <= 5:
            if cross == "CROSS ABOVE":
                return "▲ FRESH CROSS"
            elif cross == "CROSS BELOW":
                return "▼ FRESH CROSS"

        if pd.notna(pct):
            if abs(pct) <= 0.02:
                return "● NEAR EMA20"
            elif pct > 0:
                return "▲ ABOVE EMA20"
            else:
                return "▼ BELOW EMA20"

        return "— UNKNOWN"

    radar["EMA_Signal"] = radar.apply(
        ema_signal,
        axis=1
    )

    # --------------------------------------------------------
    # BASIC CLEANUP
    # --------------------------------------------------------

    numeric_cols = [
        "Price",
        "EMA20",
        "Pct_Above_EMA20",
        "MA30",
        "Pct_Above_30",
        "MA50",
        "Pct_Above_50",
        "MA100",
        "Pct_Above_100",
        "MA200",
        "Pct_Above_200",
        "Days_Since_Price_EMA20_Cross",
        "EMA20_Slope_5D_Pct",
        "MA30_Slope_5D_Pct",
        "Early_Rotation_Score",
        "Rotation_Readiness_Score",
    ]

    for col in numeric_cols:
        if col in radar.columns:
            radar[col] = pd.to_numeric(
                radar[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # SUMMARY METRICS
    # --------------------------------------------------------

    above_ema20 = (
        radar["Pct_Above_EMA20"] > 0
    ).sum()

    below_ema20 = (
        radar["Pct_Above_EMA20"] < 0
    ).sum()

    near_ema20 = (
        radar["Pct_Above_EMA20"].abs() <= 0.02
    ).sum()

    recent_cross = (
        radar["Days_Since_Price_EMA20_Cross"] <= 5
    ).sum()

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Assets",
        radar["Ticker"].nunique()
    )

    c2.metric(
        "Above EMA20",
        int(above_ema20)
    )

    c3.metric(
        "Below EMA20",
        int(below_ema20)
    )

    c4.metric(
        "Near EMA20",
        int(near_ema20)
    )

    c5.metric(
        "Crossed EMA20 ≤ 5 Days",
        int(recent_cross)
    )

    st.divider()
    # --------------------------------------------------------
    # MA STRUCTURE BEACH
    # --------------------------------------------------------

    st.subheader("MA Structure Beach")

    st.caption(
        "Whole-universe view of price positioning relative to the "
        "EMA20 and major moving averages. ▲ = above, ▼ = below."
    )

    def ma_position_text(price, ma_value):
        if pd.isna(price) or pd.isna(ma_value) or ma_value == 0:
            return "—"

        pct = ((price / ma_value) - 1) * 100

        if pct >= 0:
            return f"▲ {pct:+.1f}%"
        else:
            return f"▼ {pct:+.1f}%"

    beach = radar.copy()

    beach["EMA20 Position"] = beach.apply(
        lambda row: ma_position_text(
            row.get("Price"),
            row.get("EMA20")
        ),
        axis=1
    )

    beach["MA30 Position"] = beach.apply(
        lambda row: ma_position_text(
            row.get("Price"),
            row.get("MA30")
        ),
        axis=1
    )

    beach["MA50 Position"] = beach.apply(
        lambda row: ma_position_text(
            row.get("Price"),
            row.get("MA50")
        ),
        axis=1
    )

    beach["MA100 Position"] = beach.apply(
        lambda row: ma_position_text(
            row.get("Price"),
            row.get("MA100")
        ),
        axis=1
    )

    beach["MA200 Position"] = beach.apply(
        lambda row: ma_position_text(
            row.get("Price"),
            row.get("MA200")
        ),
        axis=1
    )

    beach_cols = [
        "Ticker",
        "EMA20 Position",
        "MA30 Position",
        "MA50 Position",
        "MA100 Position",
        "MA200 Position",
        "Early_Rotation_State",
        "Rotation_State",
    ]

    beach_cols = [
        col for col in beach_cols
        if col in beach.columns
    ]

    beach_display = beach[beach_cols].copy()

    beach_display = beach_display.sort_values(
        "Ticker",
        ascending=True
    )

    st.dataframe(
        beach_display,
        width="stretch",
        hide_index=True,
        height=500,
        column_config={
            "Ticker": st.column_config.TextColumn(
                "Ticker",
                width="small"
            ),
            "EMA20 Position": st.column_config.TextColumn(
                "EMA20",
                width="small"
            ),
            "MA30 Position": st.column_config.TextColumn(
                "MA30",
                width="small"
            ),
            "MA50 Position": st.column_config.TextColumn(
                "MA50",
                width="small"
            ),
            "MA100 Position": st.column_config.TextColumn(
                "MA100",
                width="small"
            ),
            "MA200 Position": st.column_config.TextColumn(
                "MA200",
                width="small"
            ),
        }
    )

    st.divider()

    # --------------------------------------------------------
    # ACTIONABLE SETUP MONITOR
    # --------------------------------------------------------

    st.subheader("Actionable Setup Monitor")

    st.caption(
        "Rule-based decision-support screen combining EMA20 behavior, "
        "moving-average structure, trend slope, and rotation evidence. "
        "Designed to identify assets that deserve further investigation."
    )

    def classify_setup(row):

        price = row.get("Price")
        ema20 = row.get("EMA20")
        ma30 = row.get("MA30")
        ma50 = row.get("MA50")
        ma100 = row.get("MA100")
        ma200 = row.get("MA200")

        pct_ema = row.get("Pct_Above_EMA20")
        days_cross = row.get("Days_Since_Price_EMA20_Cross")
        cross = row.get("Price_EMA20_Last_Cross")
        ema_slope = row.get("EMA20_Slope_5D_Pct")

        early_state = row.get("Early_Rotation_State")
        rotation_state = row.get("Rotation_State")

        # --------------------------------------------
        # Supporting conditions
        # --------------------------------------------

        fresh_above = (
            cross == "CROSS ABOVE"
            and pd.notna(days_cross)
            and days_cross <= 5
        )

        fresh_below = (
            cross == "CROSS BELOW"
            and pd.notna(days_cross)
            and days_cross <= 5
        )

        near_ema = (
            pd.notna(pct_ema)
            and abs(pct_ema) <= 0.02
        )

        positive_slope = (
            pd.notna(ema_slope)
            and ema_slope > 0
        )

        above_50 = (
            pd.notna(price)
            and pd.notna(ma50)
            and price > ma50
        )

        above_100 = (
            pd.notna(price)
            and pd.notna(ma100)
            and price > ma100
        )

        above_200 = (
            pd.notna(price)
            and pd.notna(ma200)
            and price > ma200
        )

        long_term_support = (
            above_50
            and (above_100 or above_200)
        )

        rotation_positive = (
            early_state in ["EARLY ENTRY", "BUILDING"]
            or rotation_state in ["EMERGING", "LEADER"]
        )

        # --------------------------------------------
        # Classification hierarchy
        # --------------------------------------------

        if (
            fresh_above
            and positive_slope
            and long_term_support
            and rotation_positive
        ):
            return "▲ HIGH INTEREST"

        elif (
            fresh_below
            and long_term_support
        ):
            return "▼ PULLBACK WATCH"

        elif (
            near_ema
            and positive_slope
            and long_term_support
        ):
            return "● SETUP WATCH"

        elif fresh_below:
            return "▼ CAUTION"

        elif fresh_above:
            return "▲ EARLY CROSS"

        else:
            return "— NO SETUP"

    radar["Setup_Status"] = radar.apply(
        classify_setup,
        axis=1
    )

    setup_counts = radar["Setup_Status"].value_counts()

    high_interest_count = setup_counts.get(
        "▲ HIGH INTEREST", 0
    )

    pullback_count = setup_counts.get(
        "▼ PULLBACK WATCH", 0
    )

    setup_watch_count = setup_counts.get(
        "● SETUP WATCH", 0
    )

    caution_count = setup_counts.get(
        "▼ CAUTION", 0
    )

    early_cross_count = setup_counts.get(
        "▲ EARLY CROSS", 0
    )

    s1, s2, s3, s4, s5 = st.columns(5)

    s1.metric(
        "High Interest",
        int(high_interest_count)
    )

    s2.metric(
        "Pullback Watch",
        int(pullback_count)
    )

    s3.metric(
        "Setup Watch",
        int(setup_watch_count)
    )

    s4.metric(
        "Early Cross",
        int(early_cross_count)
    )

    s5.metric(
        "Caution",
        int(caution_count)
    )

    actionable = radar[
        radar["Setup_Status"] != "— NO SETUP"
    ].copy()

    setup_priority = {
        "▲ HIGH INTEREST": 1,
        "▼ PULLBACK WATCH": 2,
        "● SETUP WATCH": 3,
        "▲ EARLY CROSS": 4,
        "▼ CAUTION": 5,
    }

    actionable["Setup_Priority"] = (
        actionable["Setup_Status"]
        .map(setup_priority)
        .fillna(99)
    )

    actionable = actionable.sort_values(
        [
            "Setup_Priority",
            "Rotation_Readiness_Score",
            "Early_Rotation_Score",
        ],
        ascending=[True, False, False],
        na_position="last"
    )

    setup_cols = [
        c for c in [
            "Ticker",
            "Setup_Status",
            "Price",
            "EMA20",
            "Pct_Above_EMA20",
            "Price_EMA20_Last_Cross",
            "Days_Since_Price_EMA20_Cross",
            "EMA20_Slope_5D_Pct",
            "MA50",
            "MA100",
            "MA200",
            "Early_Rotation_State",
            "Early_Rotation_Score",
            "Rotation_State",
            "Rotation_Readiness_Score",
        ]
        if c in actionable.columns
    ]

    setup_display = actionable[
        setup_cols
    ].copy()

    if "Pct_Above_EMA20" in setup_display.columns:
        setup_display["Pct_Above_EMA20"] = (
            setup_display["Pct_Above_EMA20"] * 100
        )

    st.caption(
        f"{len(actionable)} of {len(radar)} assets currently "
        "meet at least one setup condition."
    )

    st.dataframe(
        setup_display,
        width="stretch",
        hide_index=True,
        height=450,
        column_config={

            "Ticker": st.column_config.TextColumn(
                "Ticker",
                width="small"
            ),

            "Setup_Status": st.column_config.TextColumn(
                "Setup",
                width="medium"
            ),

            "Price": st.column_config.NumberColumn(
                "Price",
                format="$%.2f"
            ),

            "EMA20": st.column_config.NumberColumn(
                "EMA20",
                format="$%.2f"
            ),

            "Pct_Above_EMA20": st.column_config.NumberColumn(
                "% vs EMA20",
                format="%.1f%%"
            ),

            "Price_EMA20_Last_Cross":
                st.column_config.TextColumn(
                    "Last EMA20 Cross"
                ),

            "Days_Since_Price_EMA20_Cross":
                st.column_config.NumberColumn(
                    "Days Since Cross",
                    format="%d"
                ),

            "EMA20_Slope_5D_Pct":
                st.column_config.NumberColumn(
                    "EMA20 5D Slope",
                    format="%.2f"
                ),

            "Early_Rotation_State":
                st.column_config.TextColumn(
                    "Early Rotation"
                ),

            "Early_Rotation_Score":
                st.column_config.NumberColumn(
                    "Early Score",
                    format="%.1f"
                ),

            "Rotation_State":
                st.column_config.TextColumn(
                    "Rotation State"
                ),

            "Rotation_Readiness_Score":
                st.column_config.NumberColumn(
                    "Readiness",
                    format="%.1f"
                ),
        }
    )

    st.divider()

# ---------------------------------------------------------
# TICKER FOCUS / WHY THIS SETUP?
# ---------------------------------------------------------

st.divider()
st.subheader("Ticker Focus")

st.caption(
    "Select an asset to see why the current EMA / MA and rotation "
    "conditions produced its present setup classification."
)

focus_tickers = sorted(radar["Ticker"].dropna().unique())

focus_ticker = st.selectbox(
    "Select Ticker",
    focus_tickers,
    key="radar_focus_ticker"
)

focus_row = radar.loc[radar["Ticker"] == focus_ticker].iloc[0]


def fmt_pct(value, decimals=1):
    if pd.isna(value):
        return "N/A"
    return f"{value:+.{decimals}f}%"


def fmt_num(value, decimals=1):
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def yes_no(condition):
    return "YES" if condition else "NO"


setup_status = focus_row.get("Setup_Status", "— NO SETUP")
price = focus_row.get("Price")
ema20 = focus_row.get("EMA20")
ma30 = focus_row.get("MA30")
ma50 = focus_row.get("MA50")
ma100 = focus_row.get("MA100")
ma200 = focus_row.get("MA200")

pct_ema20 = focus_row.get("Pct_Above_EMA20")
ema20_slope = focus_row.get("EMA20_Slope_5D_Pct")
ma30_slope = focus_row.get("MA30_Slope_5D_Pct")

last_cross = focus_row.get("Price_EMA20_Last_Cross", "N/A")
days_since_cross = focus_row.get("Days_Since_Price_EMA20_Cross")

early_state = focus_row.get("Early_Rotation_State", "N/A")
early_score = focus_row.get("Early_Rotation_Score")

rotation_state = focus_row.get("Rotation_State", "N/A")
readiness_score = focus_row.get("Rotation_Readiness_Score")

above_ema20 = (
    pd.notna(price)
    and pd.notna(ema20)
    and price >= ema20
)

above_ma30 = (
    pd.notna(price)
    and pd.notna(ma30)
    and price >= ma30
)

above_ma50 = (
    pd.notna(price)
    and pd.notna(ma50)
    and price >= ma50
)

above_ma100 = (
    pd.notna(price)
    and pd.notna(ma100)
    and price >= ma100
)

above_ma200 = (
    pd.notna(price)
    and pd.notna(ma200)
    and price >= ma200
)

positive_ema_slope = (
    pd.notna(ema20_slope)
    and ema20_slope > 0
)

rotation_positive = (
    early_state in ["EARLY ENTRY", "BUILDING"]
    or rotation_state in ["EMERGING", "LEADER"]
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Setup",
    setup_status
)

c2.metric(
    "Early Rotation",
    early_state,
    delta=f"Score {fmt_num(early_score)}"
)

if pd.notna(readiness_score):
    c3.metric(
        "Rotation State",
        rotation_state,
        delta=f"Readiness {fmt_num(readiness_score)}"
    )
else:
    c3.metric(
        "Rotation State",
        rotation_state,
        delta="Readiness not available",
        delta_color="off"
    )

c4.metric(
    "EMA20 Position",
    fmt_pct(
        pct_ema20 * 100
        if pd.notna(pct_ema20)
        else float("nan")
    )
)

st.markdown("#### Why This Setup?")

reasons = []

if last_cross == "CROSS ABOVE":
    if pd.notna(days_since_cross):
        if days_since_cross <= 5:
            reasons.append(
                f"▲ FRESH EMA20 cross ABOVE — "
                f"{int(days_since_cross)} trading day(s) ago."
            )
        else:
            reasons.append(
                f"● Last EMA20 cross was ABOVE — "
                f"{int(days_since_cross)} trading day(s) ago."
            )
    else:
        reasons.append("▲ Last identified EMA20 cross was ABOVE.")

elif last_cross == "CROSS BELOW":
    if pd.notna(days_since_cross):
        if days_since_cross <= 5:
            reasons.append(
                f"▼ FRESH EMA20 cross BELOW — "
                f"{int(days_since_cross)} trading day(s) ago."
            )
        else:
            reasons.append(
                f"● Last EMA20 cross was BELOW — "
                f"{int(days_since_cross)} trading day(s) ago."
            )
    else:
        reasons.append("▼ Last identified EMA20 cross was BELOW.")

reasons.append(
    f"{'▲' if above_ema20 else '▼'} "
    f"Price is {'above' if above_ema20 else 'below'} EMA20."
)

reasons.append(
    f"{'▲' if positive_ema_slope else '▼'} "
    f"EMA20 5-day slope is "
    f"{'positive' if positive_ema_slope else 'flat or negative'} "
    f"({fmt_pct(ema20_slope)})."
)

reasons.append(
    f"{'▲' if above_ma30 else '▼'} "
    f"Price is {'above' if above_ma30 else 'below'} MA30."
)

reasons.append(
    f"{'▲' if above_ma50 else '▼'} "
    f"Price is {'above' if above_ma50 else 'below'} MA50."
)

if pd.notna(ma100):
    reasons.append(
        f"{'▲' if above_ma100 else '▼'} "
        f"Price is {'above' if above_ma100 else 'below'} MA100."
    )

if pd.notna(ma200):
    reasons.append(
        f"{'▲' if above_ma200 else '▼'} "
        f"Price is {'above' if above_ma200 else 'below'} MA200."
    )

reasons.append(
    f"{'▲' if rotation_positive else '●'} "
    f"Rotation evidence is "
    f"{'supportive' if rotation_positive else 'not yet fully supportive'} "
    f"(Early: {early_state}; Confirmed: {rotation_state})."
)

for reason in reasons:
    st.write(reason)

st.markdown("#### Decision-Support Interpretation")

if setup_status == "▲ HIGH INTEREST":
    interpretation = (
        "Technical structure and rotation evidence are aligned. "
        "This asset deserves near-term investigation for a possible "
        "entry, add, or continuation setup."
    )

elif setup_status == "▼ PULLBACK WATCH":
    interpretation = (
        "Price has weakened through EMA20, but broader trend structure "
        "remains sufficiently intact to investigate whether this is a "
        "constructive pullback rather than a trend failure."
    )

elif setup_status == "● SETUP WATCH":
    interpretation = (
        "The asset is near EMA20 with improving trend characteristics, "
        "but the setup is not yet fully confirmed. Watch for additional "
        "price or rotation confirmation."
    )

elif setup_status == "▲ EARLY CROSS":
    interpretation = (
        "A fresh bullish EMA20 event has occurred, but broader trend "
        "structure and/or rotation confirmation is incomplete. "
        "Treat this as an early signal rather than a confirmed entry."
    )

elif setup_status == "▼ CAUTION":
    interpretation = (
        "Recent EMA20 behavior indicates deterioration. Review broader "
        "MA support, rotation state, and position risk before taking action."
    )

else:
    interpretation = (
        "The asset does not currently satisfy one of the actionable "
        "setup conditions. Continue monitoring for a meaningful technical "
        "or rotation change."
    )

st.info(interpretation)


    # --------------------------------------------------------
    # RADAR FILTER
    # --------------------------------------------------------

st.subheader("Market Radar")

filter_choice = st.selectbox(
    "Radar View",
    [
        "All Assets",
        "Fresh Cross Above EMA20",
        "Fresh Cross Below EMA20",
        "Near EMA20",
        "Above EMA20",
        "Below EMA20",
        "Early Entry + Above EMA20",
        "Emerging + Above EMA20",
        "Leaders Near EMA20",
        "EMA20 Above MA30",
        "Extended Above EMA20",
    ]
)

filtered = radar.copy()

if filter_choice == "Fresh Cross Above EMA20":
    filtered = filtered[
        (filtered["Price_EMA20_Last_Cross"] == "CROSS ABOVE") &
        (filtered["Days_Since_Price_EMA20_Cross"] <= 5)
    ]

elif filter_choice == "Fresh Cross Below EMA20":
    filtered = filtered[
        (filtered["Price_EMA20_Last_Cross"] == "CROSS BELOW") &
        (filtered["Days_Since_Price_EMA20_Cross"] <= 5)
    ]

elif filter_choice == "Near EMA20":
    filtered = filtered[
        filtered["Pct_Above_EMA20"].abs() <= 0.02
    ]

elif filter_choice == "Above EMA20":
    filtered = filtered[
        filtered["Pct_Above_EMA20"] > 0
    ]

elif filter_choice == "Below EMA20":
    filtered = filtered[
        filtered["Pct_Above_EMA20"] < 0
    ]

elif filter_choice == "Early Entry + Above EMA20":
    filtered = filtered[
        (filtered["Early_Rotation_State"] == "EARLY ENTRY") &
        (filtered["Pct_Above_EMA20"] > 0)
    ]

elif filter_choice == "Emerging + Above EMA20":
    filtered = filtered[
        (filtered["Rotation_State"] == "EMERGING") &
        (filtered["Pct_Above_EMA20"] > 0)
    ]

elif filter_choice == "Leaders Near EMA20":
    filtered = filtered[
        (filtered["Rotation_State"] == "LEADER") &
        (filtered["Pct_Above_EMA20"].abs() <= 0.02)
    ]

elif filter_choice == "EMA20 Above MA30":
    filtered = filtered[
        filtered["EMA20_Above_MA30"] == True
    ]

elif filter_choice == "Extended Above EMA20":
    filtered = filtered[
        filtered["Pct_Above_EMA20"] > 0.08
    ]
    # --------------------------------------------------------
    # SORT CONTROLS
    # --------------------------------------------------------

    sort_options = {
        "Ticker": "Ticker",
        "Distance From EMA20": "Pct_Above_EMA20",
        "Days Since EMA20 Cross": "Days_Since_Price_EMA20_Cross",
        "Early Rotation Score": "Early_Rotation_Score",
        "Confirmed Readiness": "Rotation_Readiness_Score",
    }

    c1, c2 = st.columns([3, 1])

    with c1:
        sort_label = st.selectbox(
            "Sort By",
            list(sort_options.keys()),
            index=2
        )

    with c2:
        ascending = st.checkbox(
            "Ascending",
            value=True
        )

    sort_col = sort_options[sort_label]

    if sort_col in filtered.columns:
        filtered = filtered.sort_values(
            sort_col,
            ascending=ascending,
            na_position="last"
        )

    # --------------------------------------------------------
    # DISPLAY TABLE
    # --------------------------------------------------------

    radar_cols = [
        c for c in [
            "Ticker",
            "EMA_Signal",
            "Price",
            "EMA20",
            "Pct_Above_EMA20",
            "Price_EMA20_Last_Cross",
            "Days_Since_Price_EMA20_Cross",
            "EMA20_Zone",
            "MA30",
            "MA50",
            "MA100",
            "MA200",
            "EMA20_Slope_5D_Pct",
            "MA30_Slope_5D_Pct",
            "Early_Rotation_State",
            "Early_Rotation_Score",
            "Rotation_State",
            "Rotation_Readiness_Score",
        ]
        if c in filtered.columns
    ]

    st.caption(
        f"Showing {len(filtered)} of {len(radar)} assets."
    )

    display_radar = filtered[radar_cols].copy()

    if "Pct_Above_EMA20" in display_radar.columns:
        display_radar["Pct_Above_EMA20"] = (
            display_radar["Pct_Above_EMA20"] * 100
        )

    st.dataframe(
        display_radar,
        width="stretch",
        hide_index=True,
        height=650,
        column_config={
            "Ticker": st.column_config.TextColumn(
                "Ticker",
                width="small"
            ),

            "EMA_Signal": st.column_config.TextColumn(
                "EMA Signal",
                width="medium"
            ),

            "Price": st.column_config.NumberColumn(
                "Price",
                format="$%.2f"
            ),

            "EMA20": st.column_config.NumberColumn(
                "EMA20",
                format="$%.2f"
            ),

            "Pct_Above_EMA20": st.column_config.NumberColumn(
                "% vs EMA20",
                format="%.1f%%"
            ),

            "MA30": st.column_config.NumberColumn(
                "MA30",
                format="$%.2f"
            ),

            "MA50": st.column_config.NumberColumn(
                "MA50",
                format="$%.2f"
            ),

            "MA100": st.column_config.NumberColumn(
                "MA100",
                format="$%.2f"
            ),

            "MA200": st.column_config.NumberColumn(
                "MA200",
                format="$%.2f"
            ),

            "EMA20_Slope_5D_Pct": st.column_config.NumberColumn(
                "EMA20 5D Slope",
                format="%.2f"
            ),

            "MA30_Slope_5D_Pct": st.column_config.NumberColumn(
                "MA30 5D Slope",
                format="%.2f"
            ),

            "Early_Rotation_Score": st.column_config.NumberColumn(
                "Early Score",
                format="%.1f"
            ),

            "Rotation_Readiness_Score": st.column_config.NumberColumn(
                "Readiness",
                format="%.1f"
            ),
        }
    )

    st.divider()

    # --------------------------------------------------------
    # RECENT EMA20 CROSS MONITOR
    # --------------------------------------------------------

    st.subheader("Recent EMA20 Cross Monitor")

    recent = radar[
        radar["Days_Since_Price_EMA20_Cross"] <= 10
    ].copy()

    recent = recent.sort_values(
        [
            "Days_Since_Price_EMA20_Cross",
            "Pct_Above_EMA20"
        ],
        ascending=[True, False]
    )

    recent_cols = [
        c for c in [
            "Ticker",
            "Price",
            "EMA20",
            "Pct_Above_EMA20",
            "Price_EMA20_Last_Cross",
            "Price_EMA20_Last_Cross_Date",
            "Days_Since_Price_EMA20_Cross",
            "EMA20_Zone",
            "EMA20_Slope_5D_Pct",
            "Early_Rotation_State",
            "Early_Rotation_Score",
            "Rotation_State",
        ]
        if c in recent.columns
    ]

    display_recent = recent[recent_cols].copy()

    if "Pct_Above_EMA20" in display_recent.columns:
        display_recent["Pct_Above_EMA20"] = (
            display_recent["Pct_Above_EMA20"] * 100
        )

    st.dataframe(
        display_recent,
        width="stretch",
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(
                "Price",
                format="$%.2f"
            ),

            "EMA20": st.column_config.NumberColumn(
                "EMA20",
                format="$%.2f"
            ),

            "Pct_Above_EMA20": st.column_config.NumberColumn(
                "% vs EMA20",
                format="%.1f%%"
            ),

            "Early_Rotation_Score": st.column_config.NumberColumn(
                "Early Score",
                format="%.1f"
            ),
        }
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
    c4.metric("Confirmed Readiness", fmt_score(rotation_row.get("Rotation_Readiness_Score")))

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

    st.sidebar.divider()
    st.sidebar.subheader("Chart Moving Averages")
    st.sidebar.caption("Price is always shown.")

    show_ema20 = st.sidebar.checkbox("EMA20", value=True)
    show_ma30 = st.sidebar.checkbox("MA30", value=True)
    show_ma50 = st.sidebar.checkbox("MA50", value=False)
    show_ma100 = st.sidebar.checkbox("MA100", value=False)
    show_ma200 = st.sidebar.checkbox("MA200", value=False)

    selected_ma_labels = []
    if show_ema20:
        selected_ma_labels.append("EMA20")
    if show_ma30:
        selected_ma_labels.append("MA30")
    if show_ma50:
        selected_ma_labels.append("MA50")
    if show_ma100:
        selected_ma_labels.append("MA100")
    if show_ma200:
        selected_ma_labels.append("MA200")

    for label in selected_ma_labels:
        col = ma_columns[label]
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
# EARLY ROTATION
# ============================================================

elif page == "Early Rotation":

    st.header("Early Rotation")

    st.caption(
        "Fast-signal layer focused on EMA20 / MA30 behavior, short-term momentum, "
        "and acceleration before full confirmation is present."
    )

    early_entries = early[
        early["Early_Rotation_State"] == "EARLY ENTRY"
    ].sort_values("Early_Rotation_Score", ascending=False)

    building = early[
        early["Early_Rotation_State"] == "BUILDING"
    ].sort_values("Early_Rotation_Score", ascending=False)

    early_watch = early[
        early["Early_Rotation_State"] == "EARLY WATCH"
    ].sort_values("Early_Rotation_Score", ascending=False)

    extended = early[
        early["Early_Rotation_State"] == "EXTENDED"
    ].sort_values("Early_Rotation_Score", ascending=False)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Early Entry", len(early_entries))
    c2.metric("Building", len(building))
    c3.metric("Early Watch", len(early_watch))
    c4.metric("Extended", len(extended))

    st.divider()

    display_cols = [
        c for c in [
            "Ticker",
            "Early_Rotation_Score",
            "Early_Rotation_Rank",
            "Pct_Above_EMA20",
            "Pct_Above_MA30",
            "EMA20_Slope_5D_Pct",
            "MA30_Slope_5D_Pct",
            "Acceleration_Score",
            "Momentum_Score",
            "Early_Rotation_State",
        ]
        if c in early.columns
    ]

    st.subheader("Early Entry Candidates")
    st.dataframe(
        early_entries[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Building / Early Watch")

    building_watch = pd.concat(
        [building, early_watch],
        ignore_index=True
    ).sort_values("Early_Rotation_Score", ascending=False)

    st.dataframe(
        building_watch[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Extended")

    st.caption(
        "Strong or accelerating assets that may no longer be in an early-stage entry zone."
    )

    st.dataframe(
        extended[display_cols],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader("Early Rotation Map")

    plot_early = early.copy()
    plot_early = plot_early.dropna(
        subset=["Pct_Above_EMA20", "Acceleration_Score", "Early_Rotation_Score"]
    )

    plot_early["Plot_Size"] = (
        pd.to_numeric(plot_early["Early_Rotation_Score"], errors="coerce")
        .fillna(1)
        .clip(lower=1)
    )

    fig_early = px.scatter(
        plot_early,
        x="Pct_Above_EMA20",
        y="Acceleration_Score",
        size="Plot_Size",
        hover_name="Ticker",
        hover_data=[
            "Early_Rotation_Score",
            "EMA20_Slope_5D_Pct",
            "MA30_Slope_5D_Pct",
            "Early_Rotation_State"
        ],
        title="EMA20 Expansion vs. Acceleration"
    )

    st.plotly_chart(fig_early, use_container_width=True)


# ============================================================
# ROTATION ANALYSIS
# ============================================================

elif page == "Rotation Analysis":

    st.header("Rotation Analysis")

    st.caption(
        "Cross-sectional momentum, acceleration, trend confirmation, "
        "and confirmation-stage rotation analytics. Early-rotation signals "
        "will be added as a separate layer rather than mixed into the confirmation model."
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

    rotation_map = rotation.copy()

    # Plotly cannot use NaN values for marker size.
    rotation_map["Plot_Size"] = (
        pd.to_numeric(
            rotation_map["Rotation_Readiness_Score"],
            errors="coerce"
        )
        .fillna(0)
        .clip(lower=1)
    )

    rotation_map = rotation_map.dropna(
        subset=["Momentum_Score", "Acceleration_Score"]
    )

    fig_rotation = px.scatter(
        rotation_map,
        x="Momentum_Score",
        y="Acceleration_Score",
        size="Plot_Size",
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

        **Confirmed Readiness**

        Combines Momentum, Acceleration, and Trend into a confirmation-stage decision-support score.
        It is intentionally not treated as the earliest possible entry signal.

        **Early Rotation Signal — planned next layer**

        Uses the faster EMA20 / MA30 relationship, price expansion from EMA20, and improving momentum
        to identify assets earlier in a possible rotation before full confirmation is present.
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

        **Early Rotation Engine**

        ↓

        **Confirmed Rotation Analytics Engine**

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
