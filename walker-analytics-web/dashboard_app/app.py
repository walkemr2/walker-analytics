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
DECISION_FILE = DATA_DIR / "web_rotation_decision_snapshot.csv"
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
    decision = pd.read_csv(DECISION_FILE)
    refresh = pd.read_csv(REFRESH_FILE)

    return snapshot, rotation, early, prices, ma_wide, ma_radar, decision, refresh


snapshot, rotation, early, prices, ma_wide, ma_radar, decision, refresh = load_data()

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
        "Wide Beach",
        "Rotation Decision Support",
        "Asset Explorer",
        "Early Rotation",
        "Rotation Analysis",
        "User Guide",
        "Research Evidence",
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

    st.caption(
        "Morning decision brief. This page summarizes lower-level analytics already calculated elsewhere in Walker Analytics. "
        "It does not create a new score; each conclusion can be investigated on the supporting pages."
    )

    latest_refresh = refresh.iloc[-1]

    leaders = rotation[rotation["Rotation_State"] == "LEADER"].copy()
    emerging = rotation[rotation["Rotation_State"] == "EMERGING"].copy()
    weakening = rotation[rotation["Rotation_State"] == "WEAKENING"].copy()

    early_entries = early[early["Early_Rotation_State"] == "EARLY ENTRY"].copy()
    building = early[early["Early_Rotation_State"] == "BUILDING"].copy()
    early_watch = early[early["Early_Rotation_State"] == "EARLY WATCH"].copy()
    extended = early[early["Early_Rotation_State"] == "EXTENDED"].copy()

    d = decision.copy()

    for col in [
        "ML_Daily_PctRank",
        "Distance_To_MA50",
        "Distance_To_MA200",
        "Days_Since_EMA20_Cross",
        "Priority_Sort",
    ]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")

    def cc_count(state):
        if "Decision_Support_State" not in d.columns:
            return 0
        return int((d["Decision_Support_State"] == state).sum())

    def cc_ordinal_percentile(value):
        if pd.isna(value):
            return "N/A"

        number = int(round(value * 100))

        if 10 <= (number % 100) <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")

        return f"{number}{suffix} percentile"

    def cc_current_ml_status(row):
        signal_window = str(row.get("Signal_Window", "")).upper()
        ml_quality = row.get("ML_Quality", "— NO CURRENT ML SIGNAL")
        rank = row.get("ML_Daily_PctRank")

        in_current_early_window = (
            "DAY 0" in signal_window
            or "DAY 1" in signal_window
            or "DAY 2" in signal_window
            or "DAY 3" in signal_window
            or "DAY 4" in signal_window
        )

        if in_current_early_window and pd.notna(rank):
            return ml_quality, cc_ordinal_percentile(rank), "CURRENT"

        if pd.notna(rank):
            return f"{ml_quality} — prior early-window signal", "N/A", "PRIOR"

        return "— NO CURRENT ML SIGNAL", "N/A", "NONE"

    # --------------------------------------------------------
    # MORNING READ
    # --------------------------------------------------------

    st.subheader("Morning Read")

    new_detection_count = cc_count("▲ NEW DETECTION")
    early_watch_count = cc_count("▲ EARLY WATCH")
    investigate_count = cc_count("★ INVESTIGATE")
    high_interest_count = cc_count("★★ HIGH INTEREST")

    morning_lines = []

    morning_lines.append(
        f"{new_detection_count} asset(s) are in Day-0 detection, while "
        f"{early_watch_count + investigate_count + high_interest_count} asset(s) are in active early-evaluation states."
    )

    current_ml_candidates = []

    if not d.empty:
        for _, row in d.iterrows():
            quality, rank_text, status = cc_current_ml_status(row)
            if status == "CURRENT" and pd.notna(row.get("ML_Daily_PctRank")):
                current_ml_candidates.append(
                    {
                        "Ticker": row.get("Ticker"),
                        "Rank": row.get("ML_Daily_PctRank"),
                        "Quality": quality,
                        "Confirmation": row.get("Confirmation_State"),
                        "Structure": row.get("Structure_State"),
                    }
                )

    if current_ml_candidates:
        best_current = sorted(
            current_ml_candidates,
            key=lambda x: x["Rank"],
            reverse=True
        )[0]

        morning_lines.append(
            f"{best_current['Ticker']} is the highest-ranked current ML opportunity at "
            f"{cc_ordinal_percentile(best_current['Rank'])}, with "
            f"{best_current['Confirmation']} and {best_current['Structure']}."
        )
    else:
        morning_lines.append(
            "No asset currently combines an active early-window state with a current ML rank."
        )

    tech_rows = d[d["Ticker"].isin(["XLK", "DRAM", "SOXX", "SMH"])].copy()

    fresh_tech = tech_rows[
        tech_rows["Decision_Support_State"] == "▲ NEW DETECTION"
    ]["Ticker"].tolist() if not tech_rows.empty else []

    prior_tech = []
    if not tech_rows.empty:
        for _, row in tech_rows.iterrows():
            quality, rank_text, status = cc_current_ml_status(row)
            if status == "PRIOR":
                prior_tech.append(str(row.get("Ticker")))

    if fresh_tech:
        morning_lines.append(
            "Technology shows renewed activity with fresh detections in "
            + ", ".join(fresh_tech)
            + "."
        )

    if prior_tech:
        morning_lines.append(
            "Prior early-window ML evidence is still displayed for "
            + ", ".join(prior_tech)
            + ", but those ranks are historical context rather than current ML opportunities."
        )

    if investigate_count == 0 and high_interest_count == 0:
        morning_lines.append(
            "Current emphasis is detection and observation rather than a confirmed early-entry setup."
        )
    elif high_interest_count > 0:
        morning_lines.append(
            f"{high_interest_count} asset(s) currently meet the High Interest state and deserve deeper investigation."
        )
    else:
        morning_lines.append(
            f"{investigate_count} asset(s) currently meet the Investigate state and deserve deeper review."
        )

    for line in morning_lines:
        st.write("• " + line)

    st.info(
        "Morning Read is deterministic. It translates the tables below into plain language; "
        "it does not generate a new prediction or trade recommendation."
    )

    st.divider()

    # --------------------------------------------------------
    # TOP-LINE MARKET STATE
    # --------------------------------------------------------

    st.subheader("1. Market / Universe State")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Assets Tracked", rotation["Ticker"].nunique())
    col2.metric("Early Entry", len(early_entries))
    col3.metric("Leaders", len(leaders))
    col4.metric("Emerging", len(emerging))
    col5.metric("Weakening", len(weakening))
    col6.metric("Last Refresh", latest_refresh.get("Refresh_Time", "N/A"))

    st.caption(
        "Use these counts as context, not trade signals. A rising number of early entries or weakening assets "
        "can indicate broadening opportunity or deterioration, but the lower-level pages explain which assets and why."
    )

    st.divider()

    # --------------------------------------------------------
    # OPPORTUNITY PIPELINE
    # --------------------------------------------------------

    st.subheader("2. Current Opportunity Pipeline")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("New Detection", new_detection_count)
    c2.metric("Early Watch", early_watch_count)
    c3.metric("Investigate", investigate_count)
    c4.metric("High Interest", high_interest_count)
    c5.metric("Established Leader", cc_count("● ESTABLISHED LEADER"))
    c6.metric("Structural Caution", cc_count("▼ STRUCTURAL CAUTION"))

    st.caption(
        "Lifecycle summary from Rotation Decision Support. Day 0 is detection; Days 1–4 are the preferred "
        "evaluation window; Day 5 is late-early; older setups transition toward established-trend logic."
    )

    st.divider()

    # --------------------------------------------------------
    # WHAT DESERVES ATTENTION
    # --------------------------------------------------------

    st.subheader("3. What Deserves Attention Now?")

    opportunity_states = [
        "★★ HIGH INTEREST",
        "★ INVESTIGATE",
        "▲ NEW DETECTION",
        "▲ EARLY WATCH",
    ]

    opportunities = d[
        d["Decision_Support_State"].isin(opportunity_states)
    ].copy() if "Decision_Support_State" in d.columns else d.head(0).copy()

    if not opportunities.empty:
        current_quality = []
        current_rank = []
        prior_quality = []
        prior_rank = []

        for _, row in opportunities.iterrows():
            quality, rank_text, status = cc_current_ml_status(row)

            if status == "CURRENT":
                current_quality.append(quality)
                current_rank.append(rank_text)
                prior_quality.append("")
                prior_rank.append("")
            elif status == "PRIOR":
                current_quality.append("— NO CURRENT ML SIGNAL")
                current_rank.append("N/A")
                prior_quality.append(quality)
                prior_rank.append(cc_ordinal_percentile(row.get("ML_Daily_PctRank")))
            else:
                current_quality.append("— NO CURRENT ML SIGNAL")
                current_rank.append("N/A")
                prior_quality.append("")
                prior_rank.append("")

        opportunities["Current_ML_Quality"] = current_quality
        opportunities["Current_ML_Rank"] = current_rank
        opportunities["Prior_ML_Quality"] = prior_quality
        opportunities["Prior_ML_Rank"] = prior_rank

        if "Priority_Sort" in opportunities.columns:
            opportunities = opportunities.sort_values(
                ["Priority_Sort", "ML_Daily_PctRank"],
                ascending=[True, False],
                na_position="last"
            )

        attention_cols = [
            c for c in [
                "Ticker",
                "Decision_Support_State",
                "Detection_State",
                "Signal_Window",
                "Current_ML_Quality",
                "Current_ML_Rank",
                "Prior_ML_Quality",
                "Prior_ML_Rank",
                "Confirmation_State",
                "Structure_State",
                "Early_Rotation_State",
                "Rotation_State",
                "Distance_To_MA50",
            ]
            if c in opportunities.columns
        ]

        attention = opportunities[attention_cols].head(12).copy()

        if "Distance_To_MA50" in attention.columns:
            attention["Distance_To_MA50"] = attention["Distance_To_MA50"] * 100

        st.dataframe(
            attention,
            width="stretch",
            hide_index=True,
            height=380,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Decision_Support_State": st.column_config.TextColumn("Decision Support", width="medium"),
                "Detection_State": st.column_config.TextColumn("Detection", width="medium"),
                "Signal_Window": st.column_config.TextColumn("Signal Window", width="medium"),
                "Current_ML_Quality": st.column_config.TextColumn("Current ML Quality", width="medium"),
                "Current_ML_Rank": st.column_config.TextColumn("Current ML Rank", width="small"),
                "Prior_ML_Quality": st.column_config.TextColumn("Prior ML Quality", width="medium"),
                "Prior_ML_Rank": st.column_config.TextColumn("Prior ML Rank", width="small"),
                "Confirmation_State": st.column_config.TextColumn("Confirmation", width="medium"),
                "Structure_State": st.column_config.TextColumn("MA Structure", width="medium"),
                "Distance_To_MA50": st.column_config.NumberColumn("% vs MA50", format="%.1f%%"),
            }
        )

        st.info(
            "Current ML columns apply only while the asset is in today's early-window population. "
            "Prior ML columns preserve useful historical context after the asset ages out of that window."
        )
    else:
        st.info("No current early-opportunity states are present in the latest decision snapshot.")

    st.divider()

    # --------------------------------------------------------
    # TECHNOLOGY COMPLEX SUMMARY
    # --------------------------------------------------------

    st.subheader("4. Technology Complex")

    st.caption(
        "Compact peer-context summary for XLK / DRAM / SOXX / SMH. "
        "This is a lifecycle comparison—not a new technology score."
    )

    tech_order = {"XLK": 1, "DRAM": 2, "SOXX": 3, "SMH": 4}

    tech = d[d["Ticker"].isin(tech_order.keys())].copy()

    if not tech.empty:
        tech["_order"] = tech["Ticker"].map(tech_order)
        tech = tech.sort_values("_order")

        tech_current_quality = []
        tech_current_rank = []
        tech_prior_quality = []
        tech_prior_rank = []

        for _, row in tech.iterrows():
            quality, rank_text, status = cc_current_ml_status(row)

            if status == "CURRENT":
                tech_current_quality.append(quality)
                tech_current_rank.append(rank_text)
                tech_prior_quality.append("")
                tech_prior_rank.append("")
            elif status == "PRIOR":
                tech_current_quality.append("— NO CURRENT ML SIGNAL")
                tech_current_rank.append("N/A")
                tech_prior_quality.append(quality)
                tech_prior_rank.append(cc_ordinal_percentile(row.get("ML_Daily_PctRank")))
            else:
                tech_current_quality.append("— NO CURRENT ML SIGNAL")
                tech_current_rank.append("N/A")
                tech_prior_quality.append("")
                tech_prior_rank.append("")

        tech["Current_ML_Quality"] = tech_current_quality
        tech["Current_ML_Rank"] = tech_current_rank
        tech["Prior_ML_Quality"] = tech_prior_quality
        tech["Prior_ML_Rank"] = tech_prior_rank

        tech_cols = [
            c for c in [
                "Ticker",
                "Decision_Support_State",
                "Signal_Window",
                "Current_ML_Quality",
                "Current_ML_Rank",
                "Prior_ML_Quality",
                "Prior_ML_Rank",
                "Confirmation_State",
                "Structure_State",
                "Rotation_State",
            ]
            if c in tech.columns
        ]

        tech_view = tech[tech_cols].copy()

        st.dataframe(
            tech_view,
            width="stretch",
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Decision_Support_State": st.column_config.TextColumn("Decision Support", width="medium"),
                "Signal_Window": st.column_config.TextColumn("Signal Window", width="medium"),
                "Current_ML_Quality": st.column_config.TextColumn("Current ML Quality", width="medium"),
                "Current_ML_Rank": st.column_config.TextColumn("Current ML Rank", width="small"),
                "Prior_ML_Quality": st.column_config.TextColumn("Prior ML Quality", width="medium"),
                "Prior_ML_Rank": st.column_config.TextColumn("Prior ML Rank", width="small"),
                "Confirmation_State": st.column_config.TextColumn("Confirmation", width="medium"),
                "Structure_State": st.column_config.TextColumn("MA Structure", width="medium"),
                "Rotation_State": st.column_config.TextColumn("Rotation State", width="small"),
            }
        )
    else:
        st.info("Technology-complex assets are not available in the current decision snapshot.")

    st.divider()

    # --------------------------------------------------------
    # LEADERSHIP / RISK SUMMARY
    # --------------------------------------------------------

    st.subheader("5. Leadership & Risk Watch")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Established Leadership")

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
            width="stretch",
            hide_index=True,
            height=300
        )

        st.caption(
            "These are already-confirmed leaders. Use Rotation Analysis to inspect the evidence and whether leadership is strengthening or fading."
        )

    with right:
        st.markdown("#### Deterioration / Structural Attention")

        risk_states = [
            "● PULLBACK / REVIEW",
            "▼ STRUCTURAL CAUTION",
        ]

        risk_view = d[
            d["Decision_Support_State"].isin(risk_states)
        ].copy() if "Decision_Support_State" in d.columns else d.head(0).copy()

        risk_cols = [
            c for c in [
                "Ticker",
                "Decision_Support_State",
                "Detection_State",
                "Structure_State",
                "Rotation_State",
                "Distance_To_MA50",
                "Distance_To_MA200",
            ]
            if c in risk_view.columns
        ]

        risk_view = risk_view[risk_cols].head(12).copy()

        for col in ["Distance_To_MA50", "Distance_To_MA200"]:
            if col in risk_view.columns:
                risk_view[col] = risk_view[col] * 100

        st.dataframe(
            risk_view,
            width="stretch",
            hide_index=True,
            height=300,
            column_config={
                "Decision_Support_State": st.column_config.TextColumn("Decision Support", width="medium"),
                "Distance_To_MA50": st.column_config.NumberColumn("% vs MA50", format="%.1f%%"),
                "Distance_To_MA200": st.column_config.NumberColumn("% vs MA200", format="%.1f%%"),
            }
        )

        st.caption(
            "This is a review list, not an automatic sell list. MA structure and position context determine whether the move is a normal pullback or actual structural failure."
        )

    st.divider()

    # --------------------------------------------------------
    # ROTATION DISTRIBUTION
    # --------------------------------------------------------

    st.subheader("6. Rotation State Distribution")

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

    # --------------------------------------------------------
    # RESEARCH RULES
    # --------------------------------------------------------

    st.subheader("7. Walker Research Rules")

    rules = pd.DataFrame([
        {
            "Rule": "Day 0 = detection",
            "Why": "The cross is the earliest warning, not proof.",
            "Where to Investigate": "MA / EMA Radar"
        },
        {
            "Rule": "Days 1–4 = preferred evaluation window",
            "Why": "Historical Early-Leader rates improved modestly after the cross while the move was still early.",
            "Where to Investigate": "Rotation Decision Support"
        },
        {
            "Rule": "Day 3 deserves extra attention—not an automatic buy",
            "Why": "Day 3 had the strongest simple day-age rate in the sample, but only slightly.",
            "Where to Investigate": "User Guide / Research Evidence"
        },
        {
            "Rule": "ML rank = quality filter",
            "Why": "Walk-forward Random Forest improved ranking lift but did not justify autonomous trading.",
            "Where to Investigate": "Rotation Decision Support / Research Evidence"
        },
        {
            "Rule": "MA200 = wider structural context",
            "Why": "Historically useful for drawdown control and long-trend preservation, but often slower and lower-CAGR.",
            "Where to Investigate": "Wide Beach / Research Evidence"
        },
        {
            "Rule": "Protection should be earned",
            "Why": "Confirmation-only tightening often truncated winners.",
            "Where to Investigate": "Research Evidence"
        },
        {
            "Rule": "Do not assume the next ranked asset is superior",
            "Why": "Slot-aware replacement testing did not support positive capital-recycling alpha.",
            "Where to Investigate": "Research Evidence"
        },
    ])

    st.dataframe(
        rules,
        width="stretch",
        hide_index=True,
        height=330,
        column_config={
            "Rule": st.column_config.TextColumn("Rule", width="medium"),
            "Why": st.column_config.TextColumn("Why", width="large"),
            "Where to Investigate": st.column_config.TextColumn("Where to Investigate", width="medium"),
        }
    )

    st.success(
        "Command Center principle: summarize lower-level evidence; do not create a new mystery score. "
        "When something looks important here, drill down to the page that produced the conclusion."
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

    def radar_fmt_pct(value, decimals=1):
        if pd.isna(value):
            return "N/A"
        return f"{value:+.{decimals}f}%"

    def radar_fmt_num(value, decimals=1):
        if pd.isna(value):
            return "N/A"
        return f"{value:.{decimals}f}"

    setup_status = focus_row.get("Setup_Status", "— NO SETUP")
    price = focus_row.get("Price")
    ema20 = focus_row.get("EMA20")
    ma30 = focus_row.get("MA30")
    ma50 = focus_row.get("MA50")
    ma100 = focus_row.get("MA100")
    ma200 = focus_row.get("MA200")

    pct_ema20 = focus_row.get("Pct_Above_EMA20")
    ema20_slope = focus_row.get("EMA20_Slope_5D_Pct")
    last_cross = focus_row.get("Price_EMA20_Last_Cross", "N/A")
    days_since_cross = focus_row.get("Days_Since_Price_EMA20_Cross")

    early_state = focus_row.get("Early_Rotation_State", "N/A")
    early_score = focus_row.get("Early_Rotation_Score")
    rotation_state = focus_row.get("Rotation_State", "N/A")
    readiness_score = focus_row.get("Rotation_Readiness_Score")

    above_ema20 = pd.notna(price) and pd.notna(ema20) and price >= ema20
    above_ma30 = pd.notna(price) and pd.notna(ma30) and price >= ma30
    above_ma50 = pd.notna(price) and pd.notna(ma50) and price >= ma50
    above_ma100 = pd.notna(price) and pd.notna(ma100) and price >= ma100
    above_ma200 = pd.notna(price) and pd.notna(ma200) and price >= ma200
    positive_ema_slope = pd.notna(ema20_slope) and ema20_slope > 0

    rotation_positive = (
        early_state in ["EARLY ENTRY", "BUILDING"]
        or rotation_state in ["EMERGING", "LEADER"]
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Setup", setup_status)
    c2.metric(
        "Early Rotation",
        early_state,
        delta=f"Score {radar_fmt_num(early_score)}"
    )

    if pd.notna(readiness_score):
        c3.metric(
            "Rotation State",
            rotation_state,
            delta=f"Readiness {radar_fmt_num(readiness_score)}"
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
        radar_fmt_pct(
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
        f"({radar_fmt_pct(ema20_slope)})."
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
        filtered = filtered[filtered["Pct_Above_EMA20"].abs() <= 0.02]
    elif filter_choice == "Above EMA20":
        filtered = filtered[filtered["Pct_Above_EMA20"] > 0]
    elif filter_choice == "Below EMA20":
        filtered = filtered[filtered["Pct_Above_EMA20"] < 0]
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
        filtered = filtered[filtered["EMA20_Above_MA30"] == True]
    elif filter_choice == "Extended Above EMA20":
        filtered = filtered[filtered["Pct_Above_EMA20"] > 0.08]

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

    st.caption(f"Showing {len(filtered)} of {len(radar)} assets.")

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
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "EMA_Signal": st.column_config.TextColumn("EMA Signal", width="medium"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "EMA20": st.column_config.NumberColumn("EMA20", format="$%.2f"),
            "Pct_Above_EMA20": st.column_config.NumberColumn("% vs EMA20", format="%.1f%%"),
            "MA30": st.column_config.NumberColumn("MA30", format="$%.2f"),
            "MA50": st.column_config.NumberColumn("MA50", format="$%.2f"),
            "MA100": st.column_config.NumberColumn("MA100", format="$%.2f"),
            "MA200": st.column_config.NumberColumn("MA200", format="$%.2f"),
            "EMA20_Slope_5D_Pct": st.column_config.NumberColumn("EMA20 5D Slope", format="%.2f"),
            "MA30_Slope_5D_Pct": st.column_config.NumberColumn("MA30 5D Slope", format="%.2f"),
            "Early_Rotation_Score": st.column_config.NumberColumn("Early Score", format="%.1f"),
            "Rotation_Readiness_Score": st.column_config.NumberColumn("Readiness", format="%.1f"),
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
        ["Days_Since_Price_EMA20_Cross", "Pct_Above_EMA20"],
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
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "EMA20": st.column_config.NumberColumn("EMA20", format="$%.2f"),
            "Pct_Above_EMA20": st.column_config.NumberColumn("% vs EMA20", format="%.1f%%"),
            "Early_Rotation_Score": st.column_config.NumberColumn("Early Score", format="%.1f"),
        }
    )

# ============================================================
# WIDE BEACH
# ============================================================

elif page == "Wide Beach":

    st.header("Wide Beach — Historical MA Workbench")

    st.caption(
        "Historical moving-average workbench built directly from moving_average_wide.csv. "
        "Use it to narrow the universe, isolate specific moving averages, inspect exact historical "
        "relationships, and then drill into one asset without losing the full underlying data."
    )

    wide = ma_wide.copy()

    # --------------------------------------------------------
    # DATE / UNIVERSE SETUP
    # --------------------------------------------------------

    wide_date_col = wide.columns[0]
    wide[wide_date_col] = pd.to_datetime(
        wide[wide_date_col],
        errors="coerce"
    )
    wide = wide.dropna(subset=[wide_date_col]).sort_values(wide_date_col)

    def infer_wide_tickers(columns):
        suffixes = [
            "_EMA20",
            "_30",
            "_50",
            "_100",
            "_200",
            "_AboveEMA20",
            "_Pct_Above_EMA20",
            "_Above30",
            "_Pct_Above_30",
            "_Above50",
            "_Pct_Above_50",
            "_Above100",
            "_Pct_Above_100",
            "_Above200",
            "_Pct_Above_200",
        ]

        tickers_found = []

        for col in columns:
            if col == wide_date_col:
                continue

            text_col = str(col)

            if not any(text_col.endswith(suffix) for suffix in suffixes):
                tickers_found.append(text_col)

        return sorted(set(tickers_found))

    wide_tickers = infer_wide_tickers(wide.columns)

    latest_market_date = wide[wide_date_col].max()
    earliest_market_date = wide[wide_date_col].min()

    h1, h2, h3 = st.columns(3)
    h1.metric("Assets Available", len(wide_tickers))
    h2.metric(
        "Market Data Through",
        latest_market_date.strftime("%Y-%m-%d")
        if pd.notna(latest_market_date)
        else "N/A"
    )
    h3.metric(
        "History Starts",
        earliest_market_date.strftime("%Y-%m-%d")
        if pd.notna(earliest_market_date)
        else "N/A"
    )

    st.divider()

    # --------------------------------------------------------
    # PRESETS / TICKER SELECTION
    # --------------------------------------------------------

    preset_map = {
        "Technology Complex": ["XLK", "DRAM", "SOXX", "SMH"],
        "Broad Market": ["SPY", "VOO", "QQQ", "DIA", "IWM", "RSP"],
        "Energy": ["XLE", "XOP", "OIH", "USO", "PDBC", "AMLP"],
        "Metals / Commodities": ["GLD", "SLV", "CPER", "COPX", "DBA", "CORN", "WEAT"],
        "Rates / Defensive": ["TLT", "IEF", "SHY", "TIP", "UUP", "XLU", "XLP"],
        "Crypto / Alternative": ["IBIT", "ETHE", "UNG", "VIXY"],
        "Custom": [],
    }

    c1, c2 = st.columns([1, 3])

    with c1:
        preset = st.selectbox(
            "Universe Preset",
            list(preset_map.keys()),
            index=0,
            key="wide_beach_preset"
        )

    default_tickers = [
        ticker
        for ticker in preset_map.get(preset, [])
        if ticker in wide_tickers
    ]

    if preset == "Custom":
        default_tickers = [
            ticker for ticker in ["SPY", "QQQ"]
            if ticker in wide_tickers
        ]

    with c2:
        selected_tickers = st.multiselect(
            "Assets",
            wide_tickers,
            default=default_tickers,
            key=f"wide_beach_assets_{preset}"
        )

    if not selected_tickers:
        st.info("Select at least one asset to build the historical workbench.")
        st.stop()

    # --------------------------------------------------------
    # HISTORY WINDOW / MA LENS
    # --------------------------------------------------------

    c3, c4, c5 = st.columns([1.2, 1.5, 2.3])

    with c3:
        history_window = st.selectbox(
            "History Window",
            [
                "Last 30 Trading Days",
                "Last 60 Trading Days",
                "Last 120 Trading Days",
                "Last 252 Trading Days",
                "All Available History",
            ],
            index=2,
            key="wide_beach_history_window"
        )

    with c4:
        view_mode = st.selectbox(
            "Table View",
            [
                "MA Values",
                "Distance From MAs",
                "Above / Below Flags",
                "Full Detail",
            ],
            index=0,
            key="wide_beach_view_mode"
        )

    with c5:
        selected_mas = st.multiselect(
            "Moving-Average Lens",
            ["EMA20", "MA30", "MA50", "MA100", "MA200"],
            default=["EMA20", "MA30", "MA50", "MA100", "MA200"],
            key="wide_beach_ma_lens"
        )

    window_rows = {
        "Last 30 Trading Days": 30,
        "Last 60 Trading Days": 60,
        "Last 120 Trading Days": 120,
        "Last 252 Trading Days": 252,
    }

    if history_window == "All Available History":
        wide_window = wide.copy()
    else:
        wide_window = wide.tail(window_rows[history_window]).copy()

    # --------------------------------------------------------
    # COLUMN BUILDERS
    # --------------------------------------------------------

    ma_value_suffix = {
        "EMA20": "_EMA20",
        "MA30": "_30",
        "MA50": "_50",
        "MA100": "_100",
        "MA200": "_200",
    }

    distance_suffix = {
        "EMA20": "_Pct_Above_EMA20",
        "MA30": "_Pct_Above_30",
        "MA50": "_Pct_Above_50",
        "MA100": "_Pct_Above_100",
        "MA200": "_Pct_Above_200",
    }

    flag_suffix = {
        "EMA20": "_AboveEMA20",
        "MA30": "_Above30",
        "MA50": "_Above50",
        "MA100": "_Above100",
        "MA200": "_Above200",
    }

    def build_columns_for_ticker(ticker, mode, ma_lens):
        cols = [ticker] if ticker in wide.columns else []

        if mode in ["MA Values", "Full Detail"]:
            for ma_name in ma_lens:
                col = f"{ticker}{ma_value_suffix[ma_name]}"
                if col in wide.columns:
                    cols.append(col)

        if mode in ["Distance From MAs", "Full Detail"]:
            for ma_name in ma_lens:
                col = f"{ticker}{distance_suffix[ma_name]}"
                if col in wide.columns:
                    cols.append(col)

        if mode in ["Above / Below Flags", "Full Detail"]:
            for ma_name in ma_lens:
                col = f"{ticker}{flag_suffix[ma_name]}"
                if col in wide.columns:
                    cols.append(col)

        return cols

    selected_cols = [wide_date_col]

    for ticker in selected_tickers:
        selected_cols.extend(
            build_columns_for_ticker(
                ticker,
                view_mode,
                selected_mas
            )
        )

    # Preserve order while removing duplicates.
    selected_cols = list(dict.fromkeys(selected_cols))

    # --------------------------------------------------------
    # HISTORICAL MATRIX
    # --------------------------------------------------------

    st.subheader("Historical MA Matrix")

    st.caption(
        f"Showing {len(wide_window):,} trading sessions for "
        f"{len(selected_tickers)} selected asset(s). "
        "Horizontal scrolling is intentional in Full Detail mode."
    )

    matrix = wide_window[selected_cols].copy()
    matrix[wide_date_col] = matrix[wide_date_col].dt.strftime("%Y-%m-%d")

    column_config = {
        wide_date_col: st.column_config.TextColumn(
            "Date",
            width="small"
        )
    }

    for ticker in selected_tickers:
        if ticker in matrix.columns:
            column_config[ticker] = st.column_config.NumberColumn(
                f"{ticker} Price",
                format="$%.2f"
            )

        for ma_name in selected_mas:
            value_col = f"{ticker}{ma_value_suffix[ma_name]}"
            if value_col in matrix.columns:
                column_config[value_col] = st.column_config.NumberColumn(
                    f"{ticker} {ma_name}",
                    format="$%.2f"
                )

            pct_col = f"{ticker}{distance_suffix[ma_name]}"
            if pct_col in matrix.columns:
                column_config[pct_col] = st.column_config.NumberColumn(
                    f"{ticker} % vs {ma_name}",
                    format="%.2f%%"
                )
                matrix[pct_col] = pd.to_numeric(
                    matrix[pct_col],
                    errors="coerce"
                ) * 100

            flag_col = f"{ticker}{flag_suffix[ma_name]}"
            if flag_col in matrix.columns:
                column_config[flag_col] = st.column_config.TextColumn(
                    f"{ticker} Above {ma_name}",
                    width="small"
                )

    st.dataframe(
        matrix,
        width="stretch",
        hide_index=True,
        height=520,
        column_config=column_config
    )

    st.divider()

    # --------------------------------------------------------
    # EXACT SNAPSHOT BY DATE
    # --------------------------------------------------------

    st.subheader("Exact MA Snapshot")

    st.caption(
        "Pick one historical session and compare the selected assets row-by-row. "
        "This is the fastest way to zero in on the exact MA relationships on a specific date."
    )

    available_dates = wide_window[wide_date_col].dropna().tolist()

    snapshot_date = st.select_slider(
        "Historical Session",
        options=available_dates,
        value=available_dates[-1],
        format_func=lambda x: x.strftime("%Y-%m-%d"),
        key="wide_beach_snapshot_date"
    )

    snap_row = wide_window.loc[
        wide_window[wide_date_col] == snapshot_date
    ].iloc[-1]

    snapshot_rows = []

    for ticker in selected_tickers:
        item = {
            "Ticker": ticker,
            "Price": snap_row.get(ticker),
        }

        for ma_name in selected_mas:
            value_col = f"{ticker}{ma_value_suffix[ma_name]}"
            pct_col = f"{ticker}{distance_suffix[ma_name]}"
            flag_col = f"{ticker}{flag_suffix[ma_name]}"

            item[ma_name] = snap_row.get(value_col)
            item[f"% vs {ma_name}"] = (
                snap_row.get(pct_col) * 100
                if pd.notna(snap_row.get(pct_col))
                else None
            )
            item[f"Above {ma_name}"] = snap_row.get(flag_col)

        snapshot_rows.append(item)

    exact_snapshot = pd.DataFrame(snapshot_rows)

    exact_column_config = {
        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
    }

    for ma_name in selected_mas:
        exact_column_config[ma_name] = st.column_config.NumberColumn(
            ma_name,
            format="$%.2f"
        )
        exact_column_config[f"% vs {ma_name}"] = st.column_config.NumberColumn(
            f"% vs {ma_name}",
            format="%.2f%%"
        )
        exact_column_config[f"Above {ma_name}"] = st.column_config.TextColumn(
            f"Above {ma_name}",
            width="small"
        )

    st.dataframe(
        exact_snapshot,
        width="stretch",
        hide_index=True,
        column_config=exact_column_config
    )

    st.divider()

    # --------------------------------------------------------
    # SINGLE-ASSET DEEP DIVE
    # --------------------------------------------------------

    st.subheader("Single-Asset MA Deep Dive")

    deep_ticker = st.selectbox(
        "Deep-Dive Asset",
        selected_tickers,
        index=0,
        key="wide_beach_deep_ticker"
    )

    fig_wide = go.Figure()

    if deep_ticker in wide_window.columns:
        fig_wide.add_trace(
            go.Scatter(
                x=wide_window[wide_date_col],
                y=wide_window[deep_ticker],
                mode="lines",
                name="Price",
                line=dict(width=3)
            )
        )

    for ma_name in selected_mas:
        col = f"{deep_ticker}{ma_value_suffix[ma_name]}"

        if col in wide_window.columns:
            fig_wide.add_trace(
                go.Scatter(
                    x=wide_window[wide_date_col],
                    y=wide_window[col],
                    mode="lines",
                    name=ma_name
                )
            )

    fig_wide.update_layout(
        title=f"{deep_ticker} — Historical Price / MA Structure",
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode="x unified",
        legend_title="Series"
    )

    st.plotly_chart(
        fig_wide,
        use_container_width=True
    )

    # --------------------------------------------------------
    # DISTANCE HISTORY
    # --------------------------------------------------------

    if selected_mas:
        st.subheader("Distance From Selected Moving Averages")

        distance_fig = go.Figure()

        for ma_name in selected_mas:
            pct_col = f"{deep_ticker}{distance_suffix[ma_name]}"

            if pct_col in wide_window.columns:
                pct_series = pd.to_numeric(
                    wide_window[pct_col],
                    errors="coerce"
                ) * 100

                distance_fig.add_trace(
                    go.Scatter(
                        x=wide_window[wide_date_col],
                        y=pct_series,
                        mode="lines",
                        name=f"% vs {ma_name}"
                    )
                )

        distance_fig.add_hline(
            y=0,
            line_dash="dash",
            annotation_text="Price = MA"
        )

        distance_fig.update_layout(
            title=f"{deep_ticker} — Percent Distance From Moving Averages",
            xaxis_title="Date",
            yaxis_title="Percent Distance",
            hovermode="x unified",
            legend_title="Series"
        )

        st.plotly_chart(
            distance_fig,
            use_container_width=True
        )

    st.info(
        "Wide Beach is intentionally exhaustive. Use presets, the MA lens, and the date controls "
        "to reduce the 1,000+ raw columns to the exact historical relationships you want to inspect."
    )


# ============================================================
# ROTATION DECISION SUPPORT
# ============================================================

elif page == "Rotation Decision Support":

    st.header("Rotation Decision Support")

    st.caption(
        "Research-to-production decision-support layer combining early EMA20 detection, "
        "walk-forward ML candidate quality, confirmation, moving-average structure, and "
        "risk context. States identify opportunities for investigation; they are not "
        "automatic buy or sell instructions."
    )

    d = decision.copy()

    # --------------------------------------------------------
    # CLEANUP / DISPLAY HELPERS
    # --------------------------------------------------------

    numeric_decision_cols = [
        "Price", "EMA20", "MA30", "MA50", "MA100", "MA200",
        "Distance_To_EMA20", "Distance_To_MA50", "Distance_To_MA200",
        "Days_Since_EMA20_Cross", "ML_Early_Leader_Probability",
        "ML_Daily_PctRank", "EMA20_Slope_5D_Pct", "MA30_Slope_5D_Pct",
        "Early_Rotation_Score", "Rotation_Readiness_Score", "Priority_Sort",
    ]

    for col in numeric_decision_cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")

    def decision_count(state):
        if "Decision_Support_State" not in d.columns:
            return 0
        return int((d["Decision_Support_State"] == state).sum())

    def display_pct_fraction(value, decimals=1):
        if pd.isna(value):
            return "N/A"
        return f"{value * 100:+.{decimals}f}%"

    def ordinal_integer(number):
        integer = int(round(number))

        if 10 <= (integer % 100) <= 20:
            suffix = "th"
        else:
            suffix = {
                1: "st",
                2: "nd",
                3: "rd",
            }.get(integer % 10, "th")

        return f"{integer}{suffix}"

    def display_percentile(value):
        if pd.isna(value):
            return "N/A"
        return f"{ordinal_integer(value * 100)} percentile"


    def display_date(value):
        if pd.isna(value):
            return "N/A"

        parsed = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed):
            return str(value)

        return parsed.strftime("%Y-%m-%d")

    # --------------------------------------------------------
    # CURRENT OPPORTUNITY PIPELINE
    # --------------------------------------------------------

    st.subheader("Current Opportunity Pipeline")
    st.caption(
        "Lifecycle counts. These states are stages, not grades: Day-0 detection can mature "
        "into an early/confirmed opportunity, while established leaders are managed separately."
    )

    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("New Detection", decision_count("▲ NEW DETECTION"))
    p2.metric("Early Watch", decision_count("▲ EARLY WATCH"))
    p3.metric("Investigate", decision_count("★ INVESTIGATE"))
    p4.metric("High Interest", decision_count("★★ HIGH INTEREST"))
    p5.metric("Established Leader", decision_count("● ESTABLISHED LEADER"))
    p6.metric("Structural Caution", decision_count("▼ STRUCTURAL CAUTION"))

    st.divider()

    # --------------------------------------------------------
    # TOP CURRENT OPPORTUNITIES
    # --------------------------------------------------------

    st.subheader("Top Current Opportunities")
    st.caption(
        "Opportunity-side view: detection → ML quality → confirmation → structure. "
        "ML rank is shown only when the asset is in the model's current early-entry population."
    )

    opportunity_states = [
        "★★ HIGH INTEREST",
        "★ INVESTIGATE",
        "▲ NEW DETECTION",
        "▲ EARLY WATCH",
    ]

    opportunities = d[
        d["Decision_Support_State"].isin(opportunity_states)
    ].copy() if "Decision_Support_State" in d.columns else d.head(0).copy()

    if "Priority_Sort" in opportunities.columns:
        opportunities = opportunities.sort_values(
            ["Priority_Sort", "ML_Daily_PctRank"],
            ascending=[True, False],
            na_position="last"
        )
    elif "ML_Daily_PctRank" in opportunities.columns:
        opportunities = opportunities.sort_values(
            "ML_Daily_PctRank", ascending=False, na_position="last"
        )

    opportunity_cols = [
        c for c in [
            "Ticker",
            "Decision_Support_State",
            "Detection_State",
            "Signal_Window",
            "ML_Quality",
            "ML_Daily_PctRank",
            "ML_Signal_Date",
            "Confirmation_State",
            "Structure_State",
            "Structure_History_Status",
            "Early_Rotation_State",
            "Rotation_State",
            "Distance_To_MA50",
        ]
        if c in opportunities.columns
    ]

    opportunity_display = opportunities[opportunity_cols].copy()

    if "ML_Daily_PctRank" in opportunity_display.columns:
        opportunity_display["ML_Daily_PctRank"] = (
            opportunity_display["ML_Daily_PctRank"] * 100
        )

    if "Distance_To_MA50" in opportunity_display.columns:
        opportunity_display["Distance_To_MA50"] = (
            opportunity_display["Distance_To_MA50"] * 100
        )

    st.dataframe(
        opportunity_display,
        width="stretch",
        hide_index=True,
        height=430,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Decision_Support_State": st.column_config.TextColumn("Decision Support", width="medium"),
            "Detection_State": st.column_config.TextColumn("Detection", width="medium"),
            "Signal_Window": st.column_config.TextColumn("Signal Window", width="medium"),
            "ML_Quality": st.column_config.TextColumn("ML Quality", width="medium"),
            "ML_Daily_PctRank": st.column_config.NumberColumn("ML Daily Rank", format="%.1f%%"),
            "Confirmation_State": st.column_config.TextColumn("Confirmation", width="medium"),
            "Structure_State": st.column_config.TextColumn("MA Structure", width="medium"),
            "Distance_To_MA50": st.column_config.NumberColumn("% vs MA50", format="%.1f%%"),
        }
    )

    st.divider()

    # --------------------------------------------------------
    # TECHNOLOGY COMPLEX
    # --------------------------------------------------------

    st.subheader("Technology Complex")
    st.caption(
        "Peer-context view for the current technology / semiconductor complex. "
        "This is a lifecycle comparison, not an additional score."
    )

    tech_tickers = ["XLK", "DRAM", "SOXX", "SMH"]

    tech = d[
        d["Ticker"].isin(tech_tickers)
    ].copy()

    if not tech.empty:
        tech["Complex_Order"] = tech["Ticker"].map({
            "XLK": 1,
            "DRAM": 2,
            "SOXX": 3,
            "SMH": 4,
        }).fillna(99)

        tech = tech.sort_values("Complex_Order")

        tech_cols = [
            c for c in [
                "Ticker",
                "Decision_Support_State",
                "Detection_State",
                "Signal_Window",
                "ML_Quality",
                "ML_Daily_PctRank",
                "Confirmation_State",
                "Structure_State",
                "Rotation_State",
            ]
            if c in tech.columns
        ]

        tech_display = tech[tech_cols].copy()

        if "ML_Daily_PctRank" in tech_display.columns:
            tech_display["ML_Daily_PctRank"] = (
                tech_display["ML_Daily_PctRank"] * 100
            )

        st.dataframe(
            tech_display,
            width="stretch",
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Decision_Support_State": st.column_config.TextColumn(
                    "Decision Support",
                    width="medium"
                ),
                "Detection_State": st.column_config.TextColumn(
                    "Detection",
                    width="medium"
                ),
                "Signal_Window": st.column_config.TextColumn(
                    "Signal Window",
                    width="medium"
                ),
                "ML_Quality": st.column_config.TextColumn(
                    "ML Quality",
                    width="medium"
                ),
                "ML_Daily_PctRank": st.column_config.NumberColumn(
                    "ML Daily Rank",
                    format="%.1f%%"
                ),
                "Confirmation_State": st.column_config.TextColumn(
                    "Confirmation",
                    width="medium"
                ),
                "Structure_State": st.column_config.TextColumn(
                    "MA Structure",
                    width="medium"
                ),
                "Rotation_State": st.column_config.TextColumn(
                    "Rotation State",
                    width="small"
                ),
            }
        )

        lifecycle_lines = []

        for _, tech_row in tech.iterrows():
            lifecycle_lines.append(
                f"**{tech_row.get('Ticker', 'N/A')}** — "
                f"{tech_row.get('Decision_Support_State', 'N/A')} | "
                f"{tech_row.get('Detection_State', 'N/A')} | "
                f"{tech_row.get('Rotation_State', 'N/A')}"
            )

        st.markdown("#### Current Lifecycle Read")
        for line in lifecycle_lines:
            st.markdown(line)

    else:
        st.info(
            "Technology complex tickers are not available in the current decision snapshot."
        )

    st.divider()

    # --------------------------------------------------------
    # TICKER FOCUS
    # --------------------------------------------------------

    st.subheader("Ticker Focus")
    st.caption(
        "Select any asset to separate opportunity quality from position-management context."
    )

    decision_tickers = sorted(d["Ticker"].dropna().astype(str).unique())
    default_index = decision_tickers.index("DRAM") if "DRAM" in decision_tickers else 0

    focus_ticker = st.selectbox(
        "Select Ticker",
        decision_tickers,
        index=default_index,
        key="decision_focus_ticker"
    )

    row = d.loc[d["Ticker"].astype(str) == focus_ticker].iloc[0]

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Decision Support", row.get("Decision_Support_State", "N/A"))
    f2.metric("Signal Window", row.get("Signal_Window", "N/A"))
    f3.metric("ML Quality", row.get("ML_Quality", "N/A"))
    f4.metric("ML Daily Rank", display_percentile(row.get("ML_Daily_PctRank")))

    f5, f6, f7, f8 = st.columns(4)
    f5.metric("Detection", row.get("Detection_State", "N/A"))
    f6.metric("Confirmation", row.get("Confirmation_State", "N/A"))
    f7.metric("MA Structure", row.get("Structure_State", "N/A"))
    f8.metric("Rotation State", row.get("Rotation_State", "N/A"))

    f9, f10 = st.columns(2)
    f9.metric(
        "Structure History",
        row.get("Structure_History_Status", "N/A")
    )
    f10.metric(
        "ML Signal Date",
        display_date(row.get("ML_Signal_Date"))
    )

    st.markdown("#### Structure and Distance")

    s1, s2, s3, s4 = st.columns(4)
    price_value = row.get("Price")
    s1.metric("Price", f"${price_value:.2f}" if pd.notna(price_value) else "N/A")
    s2.metric("vs EMA20", display_pct_fraction(row.get("Distance_To_EMA20")))
    s3.metric("vs MA50", display_pct_fraction(row.get("Distance_To_MA50")))

    if pd.notna(row.get("MA200")):
        s4.metric("vs MA200", display_pct_fraction(row.get("Distance_To_MA200")))
    else:
        s4.metric("vs MA200", "N/A — insufficient history")

    st.markdown("#### Why It Is Here")

    explanation_lines = [
        f"**Detection:** {row.get('Detection_State', 'N/A')}",
        f"**Signal window:** {row.get('Signal_Window', 'N/A')}",
        f"**ML candidate quality:** {row.get('ML_Quality', 'N/A')} "
        f"({display_percentile(row.get('ML_Daily_PctRank'))})",
        f"**Confirmation:** {row.get('Confirmation_State', 'N/A')}",
        f"**Moving-average structure:** {row.get('Structure_State', 'N/A')}",
        f"**Structure history:** {row.get('Structure_History_Status', 'N/A')}",
        f"**ML signal date:** {display_date(row.get('ML_Signal_Date'))}",
        f"**Early rotation:** {row.get('Early_Rotation_State', 'N/A')}",
        f"**Confirmed rotation:** {row.get('Rotation_State', 'N/A')}",
    ]

    for line in explanation_lines:
        st.markdown(line)

    research_note = row.get("Research_Note")
    if pd.notna(research_note) and str(research_note).strip():
        st.info(str(research_note))

    st.divider()

    # --------------------------------------------------------
    # POSITION / RISK CONTEXT
    # --------------------------------------------------------

    st.subheader("Position / Risk Context")
    st.caption(
        "This section deliberately does not convert candidate quality into an automatic trade. "
        "Research supports separate entry-quality and position-management decisions."
    )

    r1, r2 = st.columns(2)

    with r1:
        st.markdown("#### Structural Risk References")
        st.write(f"**Initial risk research reference:** {row.get('Initial_Risk_Reference', 'N/A')}")

        if pd.notna(row.get("MA200")):
            st.write(
                f"**Long-term structural reference:** "
                f"{row.get('Long_Term_Structural_Reference', 'N/A')}"
            )
            st.write(
                f"**Current distance to MA200:** "
                f"{display_pct_fraction(row.get('Distance_To_MA200'))}"
            )
        else:
            st.write(
                "**Long-term structural reference:** "
                "N/A — MA200 not yet available because the asset lacks sufficient price history"
            )

        st.write(
            f"**Current distance to MA50:** "
            f"{display_pct_fraction(row.get('Distance_To_MA50'))}"
        )

    with r2:
        st.markdown("#### Earned Protection")
        st.write(f"**Framework:** {row.get('Earned_Protection_Framework', 'N/A')}")
        st.write(f"**Current status:** {row.get('Earned_Protection_Status', 'POSITION DATA REQUIRED')}")
        st.caption(
            "MA tier ratchets tighter after it is earned; the active stop reference remains "
            "the current day's value of that moving average."
        )

    st.warning(
        "Decision-support states identify where further investigation is warranted. "
        "They do not establish position size, order type, or an automatic BUY/SELL instruction."
    )

    st.divider()

    # --------------------------------------------------------
    # WHOLE-UNIVERSE DECISION TABLE
    # --------------------------------------------------------

    st.subheader("Whole-Universe Decision View")

    universe_cols = [
        c for c in [
            "Ticker",
            "Decision_Support_State",
            "Detection_State",
            "ML_Quality",
            "ML_Daily_PctRank",
            "ML_Signal_Date",
            "Confirmation_State",
            "Structure_State",
            "Structure_History_Status",
            "Early_Rotation_State",
            "Rotation_State",
            "Distance_To_MA50",
            "Distance_To_MA200",
        ]
        if c in d.columns
    ]

    universe_display = d[universe_cols].copy()

    if "Priority_Sort" in d.columns:
        universe_display["_Priority"] = d["Priority_Sort"].values
        universe_display = universe_display.sort_values(
            ["_Priority", "ML_Daily_PctRank"],
            ascending=[True, False],
            na_position="last"
        ).drop(columns=["_Priority"])

    for col in ["ML_Daily_PctRank", "Distance_To_MA50", "Distance_To_MA200"]:
        if col in universe_display.columns:
            universe_display[col] = universe_display[col] * 100

    st.dataframe(
        universe_display,
        width="stretch",
        hide_index=True,
        height=550,
        column_config={
            "ML_Daily_PctRank": st.column_config.NumberColumn("ML Daily Rank", format="%.1f%%"),
            "Distance_To_MA50": st.column_config.NumberColumn("% vs MA50", format="%.1f%%"),
            "Distance_To_MA200": st.column_config.NumberColumn("% vs MA200", format="%.1f%%"),
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
# USER GUIDE / DECISION FRAMEWORK
# ============================================================

elif page == "User Guide":

    st.header("How to Use Walker Analytics")

    st.caption(
        "A page-by-page operating guide for turning the dashboard into a repeatable decision-support process. "
        "The system separates early detection, candidate quality, confirmation, trend structure, and position risk "
        "so that no single score is treated as an automatic trade instruction."
    )

    st.info(
        "Daily operating idea: Wide Beach tells you where the universe is moving; Early Rotation detects possible "
        "new moves; ML helps rank current early opportunities; Rotation Analysis confirms established leadership; "
        "MA structure and risk rules help manage positions after entry."
    )

    st.subheader("1. Recommended Daily Workflow")

    workflow = pd.DataFrame([
        {"Step": 1, "Page": "Command Center", "Question": "What matters today?", "Action": "Start here. Read the market-wide counts and top leaders/emerging/early candidates before drilling down."},
        {"Step": 2, "Page": "Rotation Decision Support", "Question": "What deserves investigation?", "Action": "Review New Detection, Early Watch, Investigate, and High Interest. Separate opportunity quality from position-management context."},
        {"Step": 3, "Page": "MA / EMA Radar", "Question": "What is the current technical state?", "Action": "Verify EMA20 event timing, slope, distance from moving averages, and whether broader structure supports the setup."},
        {"Step": 4, "Page": "Wide Beach", "Question": "What does the MA history look like?", "Action": "Inspect historical price/MA relationships and compare peer groups or exact historical sessions."},
        {"Step": 5, "Page": "Early Rotation", "Question": "Where may capital be starting to move?", "Action": "Use the faster EMA20/MA30 layer to identify developing candidates before full leadership confirmation."},
        {"Step": 6, "Page": "Rotation Analysis", "Question": "Where is leadership already established?", "Action": "Use momentum, acceleration, and trend confirmation to distinguish leaders, emerging assets, and weakening assets."},
        {"Step": 7, "Page": "Asset Explorer", "Question": "What does this specific asset look like?", "Action": "Inspect the individual asset, chart, returns, moving averages, and rotation analytics before making a portfolio decision."},
    ])

    st.dataframe(workflow, width="stretch", hide_index=True, column_config={
        "Step": st.column_config.NumberColumn("Step", width="small", format="%d"),
        "Page": st.column_config.TextColumn("Page", width="medium"),
        "Question": st.column_config.TextColumn("Question Answered", width="medium"),
        "Action": st.column_config.TextColumn("How to Use It", width="large"),
    })

    st.divider()

    st.subheader("2. EMA20 Cross — Which Day Matters?")
    st.caption(
        "The research does not identify a magic buy day. It supports a detection-and-confirmation window. "
        "Day numbers are trading sessions since the bullish price/EMA20 cross."
    )

    day_guide = pd.DataFrame([
        {"Day": "Day 0", "Role": "Detection", "Interpretation": "The event just happened. Earliest warning that behavior may be changing.", "Focus": "Notice it; do not treat the cross alone as proof."},
        {"Day": "Day 1", "Role": "Early confirmation", "Interpretation": "The move survived one session and can begin receiving supporting evidence.", "Focus": "Check slope, ML rank, structure, and rotation evidence."},
        {"Day": "Day 2", "Role": "Early confirmation", "Interpretation": "More evidence is available without being far removed from the original cross.", "Focus": "Strong candidates deserve investigation."},
        {"Day": "Day 3", "Role": "Research sweet spot", "Interpretation": "Our opportunity study showed a somewhat stronger Early-Leader rate around this part of the window.", "Focus": "Pay particular attention, but do not create a Day-3 automatic buy rule."},
        {"Day": "Day 4", "Role": "Late confirmation", "Interpretation": "Still inside the preferred Days 1–4 research window and has more confirmation than Day 0.", "Focus": "Useful when quality remains strong and the asset has not become excessively extended."},
        {"Day": "Day 5", "Role": "Late early window", "Interpretation": "Still fresh enough to monitor, but the research portfolio rules used Days 1–4 for entries.", "Focus": "Treat as late-stage early evidence rather than the preferred entry window."},
        {"Day": "Day 6+", "Role": "Established trend", "Interpretation": "The original cross is no longer an early event.", "Focus": "Shift emphasis toward leadership, structure, pullbacks, and position management."},
    ])

    st.dataframe(day_guide, width="stretch", hide_index=True)

    st.success(
        "Practical rule: Day 0 says LOOK. Days 1–4 say EVALUATE. Day 3 deserves extra attention from the historical sample, "
        "but ML quality, confirmation, MA structure, and risk still have to agree."
    )

    st.divider()

    st.subheader("3. How the Signals Feed the Decision")

    st.markdown(
        """
        **Wide Beach / Market Context**  \n        ↓  \n        **EMA20 Detection** — Did something change?  \n        ↓  \n        **Walk-Forward ML Quality Rank** — Among current early opportunities, which historically looked stronger?  \n        ↓  \n        **Days 1–4 Confirmation** — Is the move surviving long enough to gain evidence?  \n        ↓  \n        **MA Structure + Rotation Evidence** — Is the broader trend supportive?  \n        ↓  \n        **Asset / Peer Investigation** — Does the opportunity make sense in its own category and lifecycle?  \n        ↓  \n        **Position / Risk Management** — If capital is committed, how much room should the trend receive and when has tighter protection been earned?
        """
    )

    st.warning(
        "Important: a 95th-percentile ML rank does not mean a 95% chance of success. It means the candidate ranks near the top "
        "of the model's current opportunity population. Ranking and probability are different concepts."
    )

    st.divider()

    st.subheader("4. Research Evidence — What the Experiments Actually Told Us")
    st.caption("These are historical research findings, not promises of future performance.")

    evidence = pd.DataFrame([
        {"Research": "MA200 baseline", "Finding": "Broad-index timing generally reduced maximum drawdown but usually sacrificed raw buy-and-hold CAGR.", "System Use": "Treat MA200 primarily as a wider structural trend/risk reference."},
        {"Research": "Distinct entry / MA exits", "Finding": "MA200 captured larger trend tails; faster exits reduced risk but could cut major winners short.", "System Use": "Separate early-entry logic from structural exit logic."},
        {"Research": "Early-entry opportunity dataset", "Finding": "Day 0 was useful for detection; Days 1–4 provided a useful confirmation window. Early-Leader rates improved modestly after Day 0.", "System Use": "Detect first, then evaluate confirmation rather than waiting for mature leadership."},
        {"Research": "Walk-forward Early-Leader ML", "Finding": "Random Forest achieved about 0.67 out-of-sample AUC; top-ranked opportunities had materially higher Early-Leader success than the base population.", "System Use": "Use ML as a quality/ranking layer, not as an automatic trading engine."},
        {"Research": "ML rotation portfolio", "Finding": "ML found major winners, but MA200-only management across the whole universe was too blunt and did not beat SPY on CAGR.", "System Use": "Candidate selection alone is insufficient; position management and portfolio construction matter."},
        {"Research": "Earned progressive protection", "Finding": "Top1 earned protection improved materially versus its MA200 baseline, while diversified portfolios showed a return/drawdown tradeoff.", "System Use": "Allow a trade room initially, then tighten the MA tier only after the trade earns it."},
        {"Research": "Top5 + MA50 initial risk", "Finding": "In the tested sample, Top5 MA50 + earned protection produced about 12.3% CAGR, -25.0% max drawdown, and ~0.49 Calmar versus SPY ~13.8%, -33.7%, and ~0.41.", "System Use": "MA50 is a promising diversified failure-control reference, not a universal stop for every portfolio."},
        {"Research": "Slot-aware recycling audit", "Finding": "Replacement assets did not systematically outperform simply continuing to hold the exited asset; mean and median rotation edge were slightly negative.", "System Use": "Do not claim rotation-to-the-next-candidate creates proven alpha. The demonstrated Top5 benefit is better explained by loss containment and diversification."},
    ])

    st.dataframe(evidence, width="stretch", hide_index=True, height=430)

    st.markdown(
        """
        **Current research-backed architecture**

        **Detection → Quality / Ranking → Confirmation → Structural Risk → Earned Profit Protection → Portfolio Construction**

        - **EMA20:** early detection.
        - **Days 1–4:** preferred confirmation window used in the portfolio research.
        - **Random Forest Daily Rank:** candidate-quality filter among current early opportunities.
        - **MA50:** promising initial failure-control reference in the diversified Top5 research.
        - **MA200:** wider structural boundary and long-term trend context.
        - **Earned protection:** +5% peak → MA100; +10% → MA50; +20% → MA30. The MA tier ratchets; the stop value remains the current day's moving average.
        - **Diversification:** a major portfolio-level risk-control mechanism.
        """
    )

    st.divider()

    st.subheader("5. What Should Flow Up to the Command Center?")
    st.caption(
        "The Command Center should eventually summarize the lower-level pages rather than forcing the user to inspect every table every morning."
    )

    command_center_plan = pd.DataFrame([
        {"Lower-Level Source": "Wide Beach / MA Radar", "Command-Center Takeaway": "Breadth: how much of the universe is above/below key trend references and whether structure is improving or deteriorating."},
        {"Lower-Level Source": "Rotation Decision Support", "Command-Center Takeaway": "Top New Detection, Investigate, High Interest, and structural-caution names."},
        {"Lower-Level Source": "Early Rotation", "Command-Center Takeaway": "Best developing early opportunities and how many are entering the Days 1–4 confirmation window."},
        {"Lower-Level Source": "ML layer", "Command-Center Takeaway": "Highest current Daily_Model_PctRank candidates, with signal date and lifecycle day clearly shown."},
        {"Lower-Level Source": "Rotation Analysis", "Command-Center Takeaway": "Current leaders, emerging leadership, and weakening leadership."},
        {"Lower-Level Source": "Position / Risk", "Command-Center Takeaway": "Future: held positions approaching structural stops, earned-protection milestones, or deterioration states."},
    ])

    st.dataframe(command_center_plan, width="stretch", hide_index=True)

    st.info(
        "Next build step: upgrade Command Center so these lower-level takeaways are surfaced automatically. "
        "After that, category hierarchy can prevent unlike assets — for example XLK, DRAM, and an individual semiconductor stock — "
        "from competing as though they occupy the same level of the capital-rotation tree."
    )


# ============================================================
# RESEARCH EVIDENCE
# ============================================================

elif page == "Research Evidence":

    st.header("Research Evidence & Findings")

    st.caption(
        "Validated research findings that explain why Walker Analytics behaves the way it does. "
        "This page summarizes the historical ML, backtesting, stop-management, portfolio, and audit work. "
        "Research findings are evidence for decision support—not guarantees of future performance."
    )

    st.info(
        "Core research architecture: Detection → ML Quality → Confirmation → "
        "Structure → Risk Management → Portfolio Construction. "
        "The research repeatedly showed that one score or one moving average should not do every job."
    )

    st.subheader("1. Executive Findings")

    findings = pd.DataFrame([
        {
            "Decision Question": "When should a new move first be noticed?",
            "Research Finding": "EMA20 crosses provided useful early detection before slower structure fully developed.",
            "Walker Implementation": "Day 0 = detection. Do not treat the cross alone as proof."
        },
        {
            "Decision Question": "When should an early setup be investigated?",
            "Research Finding": "Days 1–4 formed the preferred confirmation window. Day 3 had the strongest Early-Leader rate in the simple day-age comparison, but only by a small margin.",
            "Walker Implementation": "Days 1–4 = evaluate. Day 3 deserves extra attention, not an automatic buy."
        },
        {
            "Decision Question": "Which early candidates deserve more attention?",
            "Research Finding": "Walk-forward Random Forest ranking separated higher-quality early opportunities from the baseline population.",
            "Walker Implementation": "Use ML percentile rank as a candidate-quality filter, not a trade instruction."
        },
        {
            "Decision Question": "Should long moving averages be required for discovery?",
            "Research Finding": "Long-MA structure contributed relatively little to early-leader identification compared with shorter-term behavior, momentum, volatility, and relative strength.",
            "Walker Implementation": "Do not reject a young or early asset simply because MA100/MA200 are unavailable or not yet mature."
        },
        {
            "Decision Question": "What does MA200 do well?",
            "Research Finding": "MA200 often reduced drawdown and preserved long trends, but frequently sacrificed raw CAGR versus buy-and-hold.",
            "Walker Implementation": "Treat MA200 primarily as a wider structural trend/risk reference, not as the main discovery signal."
        },
        {
            "Decision Question": "Should protection tighten immediately?",
            "Research Finding": "Aggressive confirmation-based tightening often truncated winners.",
            "Walker Implementation": "Do not immediately jump to a tight MA simply because a trade is working."
        },
        {
            "Decision Question": "When should protection tighten?",
            "Research Finding": "Earned progressive protection improved several portfolio configurations, especially concentrated Top1 performance.",
            "Walker Implementation": "Tighten only after the trade earns it; the MA tier can ratchet tighter while the MA dollar value remains dynamic."
        },
        {
            "Decision Question": "Does diversification matter?",
            "Research Finding": "Top1, Top3, and Top5 portfolios produced very different return/drawdown frontiers.",
            "Walker Implementation": "Portfolio construction itself is a risk-control decision."
        },
        {
            "Decision Question": "Does selling an asset automatically create superior replacement alpha?",
            "Research Finding": "No. Slot-aware Script 31A found mean rotation edge about -0.44%, median about -0.28%, and only about 44.6% of replacements beat the exited-asset counterfactual.",
            "Walker Implementation": "Do not claim 'sell A and buy B' simply because B ranks higher."
        },
    ])

    st.dataframe(
        findings,
        width="stretch",
        hide_index=True,
        height=500,
        column_config={
            "Decision Question": st.column_config.TextColumn("Decision Question", width="medium"),
            "Research Finding": st.column_config.TextColumn("Research Finding", width="large"),
            "Walker Implementation": st.column_config.TextColumn("Walker Implementation", width="large"),
        }
    )

    st.divider()

    st.subheader("2. Entry & Detection Evidence")

    st.markdown(
        """
        **Why EMA20?**

        EMA20 reacts faster than the longer moving averages and therefore works well as an early-event detector.
        The project does not treat EMA20 as a complete entry system by itself. Instead, an EMA20 cross opens an
        investigation window.

        **Trading-session age matters.**

        Walker Analytics counts trading sessions, not calendar days. The bullish cross session is Day 0.
        """
    )

    day_evidence = pd.DataFrame([
        {"EMA20 Day": "Day 0", "Early-Leader Rate": 13.1, "Interpretation": "Detection only. Earliest warning."},
        {"EMA20 Day": "Day 1", "Early-Leader Rate": 13.8, "Interpretation": "First confirmation session."},
        {"EMA20 Day": "Day 2", "Early-Leader Rate": 14.1, "Interpretation": "More evidence; still close to the event."},
        {"EMA20 Day": "Day 3", "Early-Leader Rate": 14.7, "Interpretation": "Highest simple day-age rate in the sample."},
        {"EMA20 Day": "Day 4", "Early-Leader Rate": 14.5, "Interpretation": "Still inside preferred confirmation window."},
        {"EMA20 Day": "Day 5", "Early-Leader Rate": 14.5, "Interpretation": "Late early window; research portfolios used Days 1–4."},
    ])

    st.dataframe(
        day_evidence,
        width="stretch",
        hide_index=True,
        column_config={
            "EMA20 Day": st.column_config.TextColumn("EMA20 Day", width="small"),
            "Early-Leader Rate": st.column_config.NumberColumn(
                "Early-Leader Rate",
                format="%.1f%%"
            ),
            "Interpretation": st.column_config.TextColumn("Interpretation", width="large"),
        }
    )

    st.success(
        "Operational takeaway: Day 0 says LOOK. Days 1–4 say EVALUATE. "
        "Day 3 deserves extra attention from the historical sample, but the evidence does not justify a Day-3 automatic-buy rule."
    )

    st.divider()

    st.subheader("3. Machine-Learning Evidence")

    ml_summary = pd.DataFrame([
        {
            "Model": "Logistic Regression",
            "Out-of-Sample AUC": 0.653,
            "Top-Decile Success": 27.3,
            "Base Success Rate": 14.94,
            "Interpretation": "Useful ranking lift with a simple, interpretable linear model."
        },
        {
            "Model": "Random Forest",
            "Out-of-Sample AUC": 0.667,
            "Top-Decile Success": 26.2,
            "Base Success Rate": 14.94,
            "Interpretation": "Best overall discrimination in the walk-forward tests; adopted as the main candidate-quality rank."
        },
    ])

    st.dataframe(
        ml_summary,
        width="stretch",
        hide_index=True,
        column_config={
            "Out-of-Sample AUC": st.column_config.NumberColumn("OOS AUC", format="%.3f"),
            "Top-Decile Success": st.column_config.NumberColumn("Top-Decile Success", format="%.1f%%"),
            "Base Success Rate": st.column_config.NumberColumn("Base Success Rate", format="%.2f%%"),
        }
    )

    st.markdown(
        """
        **What the model learned from**

        Important inputs included volatility, drawdowns, short-term relative strength versus SPY, short-term returns,
        momentum acceleration, distance from EMA20, and moving-average slopes.

        **What it did not prove**

        A high percentile does not mean the asset will win. It means that among historically similar early-entry
        opportunities, the setup ranked more favorably. ML quality is therefore shown separately from detection,
        confirmation, structure, and position-management context.
        """
    )

    st.warning(
        "The production dashboard may display an ML signal date older than the current market date. "
        "That is intentional when the model last scored the asset during its early-entry event. "
        "The market lifecycle continues to advance independently."
    )

    st.divider()

    st.subheader("4. Stop & Risk-Management Evidence")

    stop_findings = pd.DataFrame([
        {
            "Finding": "MA200 as a structural exit",
            "Evidence": "Broad indices generally gave up some CAGR versus buy-and-hold but materially reduced maximum drawdown.",
            "Implication": "MA200 is useful as a wide structural trend reference."
        },
        {
            "Finding": "Fast exits",
            "Evidence": "EMA20/MA30 exits controlled risk more tightly but often cut off the right tail of large trend winners.",
            "Implication": "The fastest MA is not automatically the best wealth-building stop."
        },
        {
            "Finding": "Progressive-confirm tightening",
            "Evidence": "Tightening simply because confirmation improved was often too aggressive.",
            "Implication": "Retire the idea of automatically stepping 200→100→50→30 based only on confirmation."
        },
        {
            "Finding": "Earned progressive protection",
            "Evidence": "Milestone-based tightening improved several portfolio configurations.",
            "Implication": "Current framework: +5% peak→MA100, +10%→MA50, +20%→MA30."
        },
        {
            "Finding": "Dynamic MA semantics",
            "Evidence": "Audit 30B found that freezing/ratcheting the dollar price of an MA stop produced false exits.",
            "Implication": "The MA tier ratchets; the active stop reference is today's value of that MA."
        },
        {
            "Finding": "MA50 in diversified Top5",
            "Evidence": "Top5 MA50 Initial + Earned produced 12.31% CAGR, -24.99% max drawdown, and 0.492 Calmar in the research sample.",
            "Implication": "MA50 may be useful as a diversified initial failure-control reference; it is not a universal single-position rule."
        },
    ])

    st.dataframe(
        stop_findings,
        width="stretch",
        hide_index=True,
        height=430,
        column_config={
            "Finding": st.column_config.TextColumn("Finding", width="medium"),
            "Evidence": st.column_config.TextColumn("Evidence", width="large"),
            "Implication": st.column_config.TextColumn("Implication", width="large"),
        }
    )

    st.divider()

    st.subheader("5. Portfolio Evidence")

    portfolio_summary = pd.DataFrame([
        {
            "Configuration": "SPY Buy & Hold Benchmark",
            "Ending Wealth": 453886,
            "CAGR": 13.84,
            "Max Drawdown": -33.72,
            "Calmar": 0.410,
            "Research Read": "Benchmark"
        },
        {
            "Configuration": "Top1 + MA200 + Earned",
            "Ending Wealth": 552243,
            "CAGR": 15.77,
            "Max Drawdown": -45.81,
            "Calmar": 0.344,
            "Research Read": "Higher return, materially worse drawdown"
        },
        {
            "Configuration": "Top3 + MA200 + Earned",
            "Ending Wealth": 413758,
            "CAGR": 12.94,
            "Max Drawdown": -35.02,
            "Calmar": 0.369,
            "Research Read": "Middle of the frontier"
        },
        {
            "Configuration": "Top5 + MA200 + Earned",
            "Ending Wealth": 335991,
            "CAGR": 10.94,
            "Max Drawdown": -27.11,
            "Calmar": 0.404,
            "Research Read": "Lower return, improved drawdown"
        },
        {
            "Configuration": "Top5 + MA50 Initial + Earned",
            "Ending Wealth": 387487,
            "CAGR": 12.31,
            "Max Drawdown": -24.99,
            "Calmar": 0.492,
            "Research Read": "Best risk-adjusted Top5 result in this branch"
        },
    ])

    st.dataframe(
        portfolio_summary,
        width="stretch",
        hide_index=True,
        column_config={
            "Ending Wealth": st.column_config.NumberColumn("Ending Wealth", format="$%d"),
            "CAGR": st.column_config.NumberColumn("CAGR", format="%.2f%%"),
            "Max Drawdown": st.column_config.NumberColumn("Max Drawdown", format="%.2f%%"),
            "Calmar": st.column_config.NumberColumn("Calmar", format="%.3f"),
        }
    )

    st.info(
        "Portfolio construction changed the risk/return frontier substantially. "
        "Top1 concentrated upside but suffered larger drawdowns; Top5 diversified failure risk but diluted some return. "
        "This is why Walker Analytics should eventually separate candidate quality from portfolio-allocation logic."
    )

    st.divider()

    st.subheader("6. Rejected or Modified Hypotheses")

    rejected = pd.DataFrame([
        {
            "Hypothesis": "The next ranked candidate usually creates positive capital-recycling alpha after an MA50 exit.",
            "Result": "NOT SUPPORTED",
            "Evidence": "Script 31A: 130 unique replacement events; mean rotation edge -0.44%, median -0.28%, only 44.6% positive.",
            "What Changed": "Walker no longer treats a higher-ranked replacement as mathematically superior to continuing to hold the exited asset."
        },
        {
            "Hypothesis": "A tighter progressive stop should activate as confirmation improves.",
            "Result": "MODIFIED",
            "Evidence": "Progressive-confirm variants often truncated winners and performed poorly in concentrated portfolios.",
            "What Changed": "Protection is now earned through profit milestones rather than confirmation alone."
        },
        {
            "Hypothesis": "One moving-average stop family should be best for all assets and portfolio structures.",
            "Result": "NOT SUPPORTED",
            "Evidence": "Stop-family dominance was mixed; MA200 often won return, EMA20 often won risk, progressive often won consistency.",
            "What Changed": "Walker separates structural invalidation, profit protection, and portfolio construction."
        },
        {
            "Hypothesis": "A model with a high-confidence prediction can function as a direct trade rule.",
            "Result": "NOT SUPPORTED",
            "Evidence": "Walk-forward lift existed, but year-to-year stability and portfolio performance were not strong enough for autonomous trading.",
            "What Changed": "ML remains a quality/ranking layer inside a broader decision framework."
        },
    ])

    st.dataframe(
        rejected,
        width="stretch",
        hide_index=True,
        height=360,
        column_config={
            "Hypothesis": st.column_config.TextColumn("Hypothesis", width="large"),
            "Result": st.column_config.TextColumn("Result", width="small"),
            "Evidence": st.column_config.TextColumn("Evidence", width="large"),
            "What Changed": st.column_config.TextColumn("What Changed", width="large"),
        }
    )

    st.divider()

    st.subheader("7. Research Timeline")

    timeline = pd.DataFrame([
        {"Script / Phase": "18", "Question": "How do distinct entry events behave under different MA exits?", "Takeaway": "Created clean non-overlapping event-based entry/exit comparisons."},
        {"Script / Phase": "19", "Question": "What does the trade-return distribution look like?", "Takeaway": "Confirmed trend-following asymmetry: many losses/small wins, a small right tail drives much of the gain."},
        {"Script / Phase": "20A", "Question": "What does the classic MA200 baseline really do?", "Takeaway": "Generally reduced drawdown but did not beat buy-and-hold CAGR on broad indices."},
        {"Script / Phase": "20B/20C", "Question": "Do asset behavior and stop families differ?", "Takeaway": "Yes. No single stop dominated all return, consistency, and risk objectives."},
        {"Script / Phase": "21", "Question": "What happens when returns are actually compounded?", "Takeaway": "Active timing often improved drawdown/Calmar but usually sacrificed raw broad-index CAGR."},
        {"Script / Phase": "22", "Question": "Can a simple early-entry rotation strategy outperform?", "Takeaway": "Fresh EMA20 was best of the simple rules, but capital became trapped in long-held positions."},
        {"Script / Phase": "23", "Question": "What predicts a future Early Leader?", "Takeaway": "Built a leakage-safe early-opportunity dataset with forward outcomes and cross-sectional ranks."},
        {"Script / Phase": "24", "Question": "Can walk-forward ML rank early opportunities?", "Takeaway": "Yes, modestly. RF AUC 0.667 and top-decile lift supported use as a quality filter."},
        {"Script / Phase": "25", "Question": "Is RF merely learning high volatility?", "Takeaway": "No. Lift persisted within several volatility buckets; successful setups still needed room for normal adverse excursion."},
        {"Script / Phase": "26", "Question": "Does ML ranking alone create a superior rotation portfolio?", "Takeaway": "No. Entry selection improved faster than position management."},
        {"Script / Phase": "27", "Question": "Can progressive stops improve portfolio outcomes?", "Takeaway": "Earned progressive protection helped; confirmation-based tightening was too aggressive."},
        {"Script / Phase": "28/29", "Question": "How much did COVID/stress regimes distort drawdown conclusions?", "Takeaway": "Stress regimes matter, but should be contextualized rather than optimized away."},
        {"Script / Phase": "30/30A/30B", "Question": "Are the stop backtests mechanically correct?", "Takeaway": "Found and fixed evaluation-window and moving-stop timing/accounting errors."},
        {"Script / Phase": "31/31A", "Question": "Does MA50 work because replacement trades are superior?", "Takeaway": "No. Main demonstrated benefit is loss containment/diversification, not proven replacement alpha."},
        {"Script / Phase": "Production Audit", "Question": "Are EMA cross ages counted correctly?", "Takeaway": "Found calendar-day counting bug; corrected production logic to use trading sessions."},
    ])

    st.dataframe(
        timeline,
        width="stretch",
        hide_index=True,
        height=560,
        column_config={
            "Script / Phase": st.column_config.TextColumn("Script / Phase", width="small"),
            "Question": st.column_config.TextColumn("Question", width="large"),
            "Takeaway": st.column_config.TextColumn("Takeaway", width="large"),
        }
    )

    st.divider()

    st.subheader("8. Research Limitations")

    st.markdown(
        """
        - Historical results do **not** guarantee future performance.
        - The 67-asset universe contains survivorship and selection effects.
        - Some ETFs have short histories, so comparisons are not equally deep across all assets.
        - Transaction costs, slippage, taxes, liquidity, and overnight gaps are not modeled identically in every experiment.
        - Several parameters were deliberately **not optimized** to avoid turning the research into curve fitting.
        - The walk-forward model provides ranking lift, not certainty.
        - Extraordinary market regimes can behave differently from ordinary conditions.
        - Portfolio-level results depend on diversification, replacement rules, position sizing, and stop architecture—not only entry quality.
        """
    )

    st.warning(
        "Research rule: when an audit contradicts a good story, keep the audit and change the story."
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
