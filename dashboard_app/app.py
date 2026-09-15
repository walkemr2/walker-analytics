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
WIDE_BEACH_FILE = DATA_DIR / "web_wide_beach_snapshot.csv"
MA_RADAR_FILE = DATA_DIR / "web_ma_wide_snapshot.csv"
DECISION_FILE = DATA_DIR / "web_rotation_decision_snapshot.csv"
REFRESH_FILE = DATA_DIR / "web_refresh_log.csv"
HIERARCHY_FILE = DATA_DIR / "asset_hierarchy.csv"
PEER_RELATIVE_FILE = DATA_DIR / "web_peer_relative_snapshot.csv"
PEER_GROUP_FILE = DATA_DIR / "web_peer_group_summary.csv"
VERTICAL_HIERARCHY_FILE = DATA_DIR / "web_vertical_hierarchy_snapshot.csv"
HIERARCHY_LEVEL_FILE = DATA_DIR / "web_hierarchy_level_summary.csv"
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
    wide_beach = pd.read_csv(WIDE_BEACH_FILE)
    refresh = pd.read_csv(REFRESH_FILE)

    return snapshot, rotation, early, prices, ma_wide, ma_radar, decision, wide_beach, refresh


snapshot, rotation, early, prices, ma_wide, ma_radar, decision, wide_beach, refresh = load_data()

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
        "Market Map",
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
# HIERARCHICAL MARKET MAP
# ============================================================

elif page == "Market Map":

    st.header("Hierarchical Market Map")

    st.caption(
        "Market hierarchy, peer-relative intelligence, and vertical confirmation. "
        "Use this page to ask whether strength is isolated or supported across Asset Class → Sector → Peer Group → Instrument. "
        "This page remains descriptive: it does not change Walker scoring, ML, entry logic, or stop logic."
    )

    required_files = {
        "Asset Hierarchy": HIERARCHY_FILE,
        "Peer Relative Snapshot": PEER_RELATIVE_FILE,
        "Peer Group Summary": PEER_GROUP_FILE,
        "Vertical Hierarchy Snapshot": VERTICAL_HIERARCHY_FILE,
        "Hierarchy Level Summary": HIERARCHY_LEVEL_FILE,
    }

    missing_files = [
        f"{label}: {path.name}"
        for label, path in required_files.items()
        if not path.exists()
    ]

    if missing_files:
        st.error(
            "Required Market Map file(s) are missing: "
            + " | ".join(missing_files)
            + ". Run Scripts 36A, 36C, and 36E before using this page."
        )
        st.stop()

    hierarchy = pd.read_csv(HIERARCHY_FILE)
    peer_relative = pd.read_csv(PEER_RELATIVE_FILE)
    peer_groups = pd.read_csv(PEER_GROUP_FILE)
    vertical = pd.read_csv(VERTICAL_HIERARCHY_FILE)
    hierarchy_levels = pd.read_csv(HIERARCHY_LEVEL_FILE)

    for df in [hierarchy, peer_relative, vertical]:
        if "Ticker" in df.columns:
            df["Ticker"] = (
                df["Ticker"]
                .astype(str)
                .str.upper()
                .str.strip()
            )

    for col in [
        "Peer_Group_Size",
        "ML_Daily_PctRank",
        "Momentum_Score",
        "Acceleration_Score",
        "Trend_Score",
        "Rotation_Readiness_Score",
        "Early_Rotation_Score",
        "Pct_Above_EMA20",
        "EMA20_Slope_5D_Pct",
        "PeerPct_Momentum",
        "PeerPct_Acceleration",
        "PeerPct_Trend",
        "PeerPct_Rotation_Readiness",
        "PeerPct_Early_Rotation",
        "Support_Level_Count",
        "Caution_Level_Count",
        "Asset_Class_Size",
        "Sector_Size",
        "PeerGroup_Size_Summary",
        "AssetClass_Pct_Leader_or_Emerging",
        "AssetClass_Pct_Early_or_Building",
        "AssetClass_Pct_New_Detection",
        "AssetClass_Pct_Structural_Caution",
        "Sector_Pct_Leader_or_Emerging",
        "Sector_Pct_Early_or_Building",
        "Sector_Pct_New_Detection",
        "Sector_Pct_Structural_Caution",
        "PeerGroup_Pct_Leader_or_Emerging",
        "PeerGroup_Pct_Early_or_Building",
        "PeerGroup_Pct_New_Detection",
        "PeerGroup_Pct_Structural_Caution",
    ]:
        if col in vertical.columns:
            vertical[col] = pd.to_numeric(
                vertical[col],
                errors="coerce"
            )

    for col in [
        "Peer_Group_Size",
        "Pct_Leader_or_Emerging",
        "Pct_Early_Entry_or_Building",
        "Pct_Structural_Caution",
        "Pct_New_Detection",
        "Mean_Momentum_Score",
        "Mean_Acceleration_Score",
        "Mean_Trend_Score",
        "Mean_Early_Rotation_Score",
    ]:
        if col in peer_groups.columns:
            peer_groups[col] = pd.to_numeric(
                peer_groups[col],
                errors="coerce"
            )

    for col in [
        "Asset_Count",
        "Pct_Leader_or_Emerging",
        "Pct_Early_Entry_or_Building",
        "Pct_New_Detection",
        "Pct_Structural_Caution",
        "Mean_Momentum_Score",
        "Mean_Acceleration_Score",
        "Mean_Trend_Score",
        "Mean_Early_Rotation_Score",
    ]:
        if col in hierarchy_levels.columns:
            hierarchy_levels[col] = pd.to_numeric(
                hierarchy_levels[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    st.subheader("1. Hierarchy Overview")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Mapped Assets", hierarchy["Ticker"].nunique())
    c2.metric("Asset Classes", hierarchy["Asset_Class"].nunique())
    c3.metric("Sectors / Major Groups", hierarchy["Sector"].nunique())
    c4.metric("Peer Groups", hierarchy["Peer_Group"].nunique())

    comparable_assets = int(
        (peer_relative["Peer_Comparison_Available"] == "YES").sum()
    ) if "Peer_Comparison_Available" in peer_relative.columns else 0

    c5.metric("Assets With Peer Comparison", comparable_assets)

    st.info(
        "Read the hierarchy in two directions: horizontally against appropriate peers, "
        "then vertically through the broader market structure. A strong ticker inside a weak peer group is different "
        "from a strong ticker supported by its peer group and sector."
    )

    st.divider()

    # --------------------------------------------------------
    # HIERARCHY NAVIGATION
    # --------------------------------------------------------

    st.subheader("2. Navigate the Market Hierarchy")

    f1, f2, f3, f4 = st.columns(4)

    asset_classes = ["All"] + sorted(
        hierarchy["Asset_Class"].dropna().unique().tolist()
    )

    selected_asset_class = f1.selectbox(
        "Asset Class",
        asset_classes,
        index=0,
        key="market_map_asset_class"
    )

    h1 = hierarchy.copy()
    if selected_asset_class != "All":
        h1 = h1[h1["Asset_Class"] == selected_asset_class]

    sectors = ["All"] + sorted(
        h1["Sector"].dropna().unique().tolist()
    )

    selected_sector = f2.selectbox(
        "Sector / Major Group",
        sectors,
        index=0,
        key="market_map_sector"
    )

    h2 = h1.copy()
    if selected_sector != "All":
        h2 = h2[h2["Sector"] == selected_sector]

    peer_group_options = ["All"] + sorted(
        h2["Peer_Group"].dropna().unique().tolist()
    )

    selected_peer_group = f3.selectbox(
        "Peer Group",
        peer_group_options,
        index=0,
        key="market_map_peer_group"
    )

    h3 = h2.copy()
    if selected_peer_group != "All":
        h3 = h3[h3["Peer_Group"] == selected_peer_group]

    ticker_options = sorted(
        h3["Ticker"].dropna().unique().tolist()
    )

    selected_ticker = f4.selectbox(
        "Instrument",
        ticker_options if ticker_options else ["N/A"],
        index=0,
        key="market_map_ticker"
    )

    st.divider()

    # --------------------------------------------------------
    # VERTICAL HIERARCHY STATE
    # --------------------------------------------------------

    st.subheader("3. Vertical Hierarchy State")

    vertical_visible = vertical.copy()

    if selected_asset_class != "All":
        vertical_visible = vertical_visible[
            vertical_visible["Asset_Class"] == selected_asset_class
        ]

    if selected_sector != "All":
        vertical_visible = vertical_visible[
            vertical_visible["Sector"] == selected_sector
        ]

    if selected_peer_group != "All":
        vertical_visible = vertical_visible[
            vertical_visible["Peer_Group"] == selected_peer_group
        ]

    strong_labels = {
        "★★ BROAD MULTI-LEVEL CONFIRMATION",
        "★ STRONG HIERARCHICAL CONFIRMATION",
        "▲ MULTI-LEVEL SUPPORT",
    }

    caution_labels = {
        "⚠ ISOLATED STRENGTH / BROADER CAUTION",
        "▼ MULTI-LEVEL CAUTION",
    }

    v1, v2, v3, v4 = st.columns(4)

    v1.metric(
        "Multi-Level Confirmation",
        int(vertical_visible["Vertical_Hierarchy_Read"].isin(strong_labels).sum())
    )

    v2.metric(
        "Isolated / Broader Caution",
        int(vertical_visible["Vertical_Hierarchy_Read"].isin(caution_labels).sum())
    )

    v3.metric(
        "Mixed Hierarchy",
        int((vertical_visible["Vertical_Hierarchy_Read"] == "● MIXED HIERARCHY").sum())
    )

    v4.metric(
        "Assets in Current View",
        len(vertical_visible)
    )

    vertical_cols = [
        c for c in [
            "Ticker",
            "Vertical_Hierarchy_Read",
            "Support_Level_Count",
            "Caution_Level_Count",
            "Asset_Class_Read",
            "Sector_Read",
            "Peer_Group_Read",
            "Peer_Relative_Read",
            "Decision_Support_State",
            "Signal_Window",
            "Rotation_State",
            "Early_Rotation_State",
        ]
        if c in vertical_visible.columns
    ]

    vertical_view = vertical_visible[vertical_cols].copy()

    vertical_view = vertical_view.sort_values(
        ["Support_Level_Count", "Caution_Level_Count", "Ticker"],
        ascending=[False, True, True],
        na_position="last"
    )

    st.dataframe(
        vertical_view,
        width="stretch",
        hide_index=True,
        height=min(560, 90 + 34 * max(len(vertical_view), 1)),
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Vertical_Hierarchy_Read": st.column_config.TextColumn(
                "Vertical Read",
                width="large"
            ),
            "Support_Level_Count": st.column_config.NumberColumn(
                "Support Levels",
                format="%d"
            ),
            "Caution_Level_Count": st.column_config.NumberColumn(
                "Caution Levels",
                format="%d"
            ),
            "Asset_Class_Read": st.column_config.TextColumn(
                "Asset Class",
                width="medium"
            ),
            "Sector_Read": st.column_config.TextColumn(
                "Sector",
                width="medium"
            ),
            "Peer_Group_Read": st.column_config.TextColumn(
                "Peer Group",
                width="medium"
            ),
            "Peer_Relative_Read": st.column_config.TextColumn(
                "Asset vs Peers",
                width="medium"
            ),
            "Decision_Support_State": st.column_config.TextColumn(
                "Decision Support",
                width="medium"
            ),
            "Signal_Window": st.column_config.TextColumn(
                "Signal Window",
                width="medium"
            ),
            "Rotation_State": st.column_config.TextColumn(
                "Rotation",
                width="small"
            ),
            "Early_Rotation_State": st.column_config.TextColumn(
                "Early Rotation",
                width="medium"
            ),
        }
    )

    st.caption(
        "Support Level Count is a descriptive count of aligned hierarchy evidence. "
        "It is not a new Walker score and is not used by the ML model."
    )

    st.divider()

    # --------------------------------------------------------
    # BROADER LEVEL SUMMARIES
    # --------------------------------------------------------

    st.subheader("4. Broader-Level Breadth")

    level_choice = st.radio(
        "Hierarchy Level",
        ["Asset Class", "Sector"],
        horizontal=True,
        key="market_map_level_choice"
    )

    level_view = hierarchy_levels[
        hierarchy_levels["Hierarchy_Level"] == level_choice
    ].copy()

    if level_choice == "Sector" and selected_asset_class != "All":
        sectors_for_class = set(
            hierarchy[
                hierarchy["Asset_Class"] == selected_asset_class
            ]["Sector"]
            .dropna()
            .tolist()
        )
        level_view = level_view[
            level_view["Group_Name"].isin(sectors_for_class)
        ]

    broader_cols = [
        c for c in [
            "Group_Name",
            "Asset_Count",
            "Hierarchy_Read",
            "Pct_Leader_or_Emerging",
            "Pct_Early_Entry_or_Building",
            "Pct_New_Detection",
            "Pct_Structural_Caution",
            "Mean_Momentum_Score",
            "Mean_Acceleration_Score",
            "Mean_Trend_Score",
        ]
        if c in level_view.columns
    ]

    broader_view = level_view[broader_cols].copy()

    for col in [
        "Pct_Leader_or_Emerging",
        "Pct_Early_Entry_or_Building",
        "Pct_New_Detection",
        "Pct_Structural_Caution",
    ]:
        if col in broader_view.columns:
            broader_view[col] = broader_view[col] * 100

    st.dataframe(
        broader_view,
        width="stretch",
        hide_index=True,
        height=min(520, 90 + 34 * max(len(broader_view), 1)),
        column_config={
            "Group_Name": st.column_config.TextColumn(
                level_choice,
                width="medium"
            ),
            "Asset_Count": st.column_config.NumberColumn(
                "Assets",
                format="%d"
            ),
            "Hierarchy_Read": st.column_config.TextColumn(
                "Hierarchy Read",
                width="large"
            ),
            "Pct_Leader_or_Emerging": st.column_config.NumberColumn(
                "Leader / Emerging",
                format="%.0f%%"
            ),
            "Pct_Early_Entry_or_Building": st.column_config.NumberColumn(
                "Early / Building",
                format="%.0f%%"
            ),
            "Pct_New_Detection": st.column_config.NumberColumn(
                "New Detection",
                format="%.0f%%"
            ),
            "Pct_Structural_Caution": st.column_config.NumberColumn(
                "Structural Caution",
                format="%.0f%%"
            ),
        }
    )

    st.caption(
        "This section answers whether strength or caution is broad at the Asset Class or Sector level before drilling into individual peer groups."
    )

    st.divider()

    # --------------------------------------------------------
    # PEER GROUP INTELLIGENCE
    # --------------------------------------------------------

    st.subheader("5. Peer Group Intelligence")

    visible_peer_groups = peer_groups.copy()

    if selected_asset_class != "All":
        visible_peer_groups = visible_peer_groups[
            visible_peer_groups["Asset_Class"].astype(str).str.contains(
                selected_asset_class,
                regex=False,
                na=False
            )
        ]

    if selected_sector != "All":
        visible_peer_groups = visible_peer_groups[
            visible_peer_groups["Sector"].astype(str).str.contains(
                selected_sector,
                regex=False,
                na=False
            )
        ]

    if selected_peer_group != "All":
        visible_peer_groups = visible_peer_groups[
            visible_peer_groups["Peer_Group"] == selected_peer_group
        ]

    peer_group_cols = [
        c for c in [
            "Peer_Group",
            "Sector",
            "Peer_Group_Size",
            "Peer_Group_Read",
            "Pct_Leader_or_Emerging",
            "Pct_Early_Entry_or_Building",
            "Pct_New_Detection",
            "Pct_Structural_Caution",
            "Mean_Momentum_Score",
            "Mean_Acceleration_Score",
            "Mean_Trend_Score",
        ]
        if c in visible_peer_groups.columns
    ]

    peer_group_view = visible_peer_groups[peer_group_cols].copy()

    for col in [
        "Pct_Leader_or_Emerging",
        "Pct_Early_Entry_or_Building",
        "Pct_New_Detection",
        "Pct_Structural_Caution",
    ]:
        if col in peer_group_view.columns:
            peer_group_view[col] = peer_group_view[col] * 100

    st.dataframe(
        peer_group_view,
        width="stretch",
        hide_index=True,
        height=min(500, 90 + 34 * max(len(peer_group_view), 1)),
        column_config={
            "Peer_Group": st.column_config.TextColumn(
                "Peer Group",
                width="medium"
            ),
            "Sector": st.column_config.TextColumn(
                "Sector",
                width="medium"
            ),
            "Peer_Group_Size": st.column_config.NumberColumn(
                "Assets",
                format="%d"
            ),
            "Peer_Group_Read": st.column_config.TextColumn(
                "Group Read",
                width="large"
            ),
            "Pct_Leader_or_Emerging": st.column_config.NumberColumn(
                "Leader / Emerging",
                format="%.0f%%"
            ),
            "Pct_Early_Entry_or_Building": st.column_config.NumberColumn(
                "Early / Building",
                format="%.0f%%"
            ),
            "Pct_New_Detection": st.column_config.NumberColumn(
                "New Detection",
                format="%.0f%%"
            ),
            "Pct_Structural_Caution": st.column_config.NumberColumn(
                "Structural Caution",
                format="%.0f%%"
            ),
        }
    )

    st.divider()

    # --------------------------------------------------------
    # SELECTED INSTRUMENT
    # --------------------------------------------------------

    st.subheader("6. Selected Instrument — Vertical Confirmation")

    selected_vertical = vertical[
        vertical["Ticker"] == selected_ticker
    ]

    selected_hierarchy = hierarchy[
        hierarchy["Ticker"] == selected_ticker
    ]

    if selected_vertical.empty:
        st.info("No vertical hierarchy record is available for the selected instrument.")
    else:
        row = selected_vertical.iloc[-1]

        st.success(
            row.get(
                "Hierarchy_Path",
                selected_ticker
            )
        )

        x1, x2, x3, x4 = st.columns(4)

        x1.metric(
            "Vertical Read",
            row.get("Vertical_Hierarchy_Read", "N/A")
        )

        x2.metric(
            "Support Levels",
            int(row.get("Support_Level_Count"))
            if pd.notna(row.get("Support_Level_Count"))
            else "N/A"
        )

        x3.metric(
            "Caution Levels",
            int(row.get("Caution_Level_Count"))
            if pd.notna(row.get("Caution_Level_Count"))
            else "N/A"
        )

        x4.metric(
            "Peer Relative",
            row.get("Peer_Relative_Read", "N/A")
        )

        st.markdown("#### Hierarchy Ladder")

        ladder = pd.DataFrame(
            [
                {
                    "Level": "Asset Class",
                    "Name": row.get("Asset_Class", "N/A"),
                    "Current Read": row.get("Asset_Class_Read", "N/A"),
                },
                {
                    "Level": "Sector / Major Group",
                    "Name": row.get("Sector", "N/A"),
                    "Current Read": row.get("Sector_Read", "N/A"),
                },
                {
                    "Level": "Peer Group",
                    "Name": row.get("Peer_Group", "N/A"),
                    "Current Read": row.get("Peer_Group_Read", "N/A"),
                },
                {
                    "Level": "Instrument vs Peers",
                    "Name": row.get("Ticker", "N/A"),
                    "Current Read": row.get("Peer_Relative_Read", "N/A"),
                },
                {
                    "Level": "Instrument Lifecycle",
                    "Name": row.get("Ticker", "N/A"),
                    "Current Read": row.get("Decision_Support_State", "N/A"),
                },
            ]
        )

        st.dataframe(
            ladder,
            width="stretch",
            hide_index=True,
            column_config={
                "Level": st.column_config.TextColumn("Level", width="medium"),
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Current Read": st.column_config.TextColumn("Current Read", width="large"),
            }
        )

        st.info(
            row.get(
                "Vertical_Context",
                "Vertical context unavailable."
            )
        )

        st.markdown("#### Existing Walker Evidence")

        e1, e2, e3, e4 = st.columns(4)

        e1.metric(
            "Decision Support",
            row.get("Decision_Support_State", "N/A")
        )
        e2.metric(
            "Signal Window",
            row.get("Signal_Window", "N/A")
        )
        e3.metric(
            "Rotation State",
            row.get("Rotation_State", "N/A")
        )
        e4.metric(
            "Early Rotation",
            row.get("Early_Rotation_State", "N/A")
        )

    st.divider()

    # --------------------------------------------------------
    # SELECTED PEER GROUP MEMBER COMPARISON
    # --------------------------------------------------------

    st.subheader("7. Selected Peer Group — Member Comparison")

    if not selected_hierarchy.empty:
        selected_group_name = selected_hierarchy.iloc[0]["Peer_Group"]

        peer_members = vertical[
            vertical["Peer_Group"] == selected_group_name
        ].copy()

        member_cols = [
            c for c in [
                "Ticker",
                "Vertical_Hierarchy_Read",
                "Support_Level_Count",
                "Peer_Relative_Read",
                "Decision_Support_State",
                "Signal_Window",
                "Rotation_State",
                "Early_Rotation_State",
                "PeerPct_Momentum",
                "PeerPct_Acceleration",
                "PeerPct_Trend",
                "PeerPct_Rotation_Readiness",
                "PeerPct_Early_Rotation",
            ]
            if c in peer_members.columns
        ]

        members = peer_members[member_cols].copy()

        for col in [
            "PeerPct_Momentum",
            "PeerPct_Acceleration",
            "PeerPct_Trend",
            "PeerPct_Rotation_Readiness",
            "PeerPct_Early_Rotation",
        ]:
            if col in members.columns:
                members[col] = (
                    pd.to_numeric(members[col], errors="coerce") * 100
                )

        members = members.sort_values(
            ["Support_Level_Count", "Ticker"],
            ascending=[False, True],
            na_position="last"
        )

        st.write(
            f"**{selected_group_name}** — "
            f"{len(peer_members)} tracked instrument(s)"
        )

        st.dataframe(
            members,
            width="stretch",
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Vertical_Hierarchy_Read": st.column_config.TextColumn(
                    "Vertical Read",
                    width="large"
                ),
                "Support_Level_Count": st.column_config.NumberColumn(
                    "Support Levels",
                    format="%d"
                ),
                "Peer_Relative_Read": st.column_config.TextColumn(
                    "Peer Relative",
                    width="medium"
                ),
                "Decision_Support_State": st.column_config.TextColumn(
                    "Decision Support",
                    width="medium"
                ),
                "Signal_Window": st.column_config.TextColumn(
                    "Signal Window",
                    width="medium"
                ),
                "Rotation_State": st.column_config.TextColumn(
                    "Rotation",
                    width="small"
                ),
                "Early_Rotation_State": st.column_config.TextColumn(
                    "Early Rotation",
                    width="medium"
                ),
                "PeerPct_Momentum": st.column_config.NumberColumn(
                    "Momentum",
                    format="%.0f%%"
                ),
                "PeerPct_Acceleration": st.column_config.NumberColumn(
                    "Acceleration",
                    format="%.0f%%"
                ),
                "PeerPct_Trend": st.column_config.NumberColumn(
                    "Trend",
                    format="%.0f%%"
                ),
                "PeerPct_Rotation_Readiness": st.column_config.NumberColumn(
                    "Rotation",
                    format="%.0f%%"
                ),
                "PeerPct_Early_Rotation": st.column_config.NumberColumn(
                    "Early",
                    format="%.0f%%"
                ),
            }
        )

    st.divider()

    # --------------------------------------------------------
    # INTERPRETATION
    # --------------------------------------------------------

    st.subheader("8. How to Use Vertical Confirmation")

    rules = pd.DataFrame(
        [
            {
                "Pattern": "Broad multi-level confirmation",
                "Interpretation": "The asset, its peers, and broader sector/asset-class context are generally aligned."
            },
            {
                "Pattern": "Asset leads mixed peers",
                "Interpretation": "The instrument may be moving first. Treat that as interesting, but not yet broad confirmation."
            },
            {
                "Pattern": "Isolated strength / broader caution",
                "Interpretation": "The ticker looks stronger than the surrounding hierarchy. Investigate why before assuming the move represents durable capital flow."
            },
            {
                "Pattern": "Broader support / asset not active",
                "Interpretation": "The surrounding hierarchy is favorable, but the individual instrument has not yet produced its own activation."
            },
            {
                "Pattern": "Multi-level caution",
                "Interpretation": "Weakness or structural caution appears at more than one level of the hierarchy."
            },
        ]
    )

    st.dataframe(
        rules,
        width="stretch",
        hide_index=True,
        column_config={
            "Pattern": st.column_config.TextColumn("Pattern", width="medium"),
            "Interpretation": st.column_config.TextColumn(
                "Interpretation",
                width="large"
            ),
        }
    )

    st.warning(
        "Phase 36F is still descriptive. The next research task is to reconstruct these hierarchy features historically "
        "and test whether multi-level confirmation adds predictive value beyond the existing EMA20/ML framework."
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

    # --------------------------------------------------------
    # CURRENT LIFECYCLE BEACH
    # --------------------------------------------------------

    wb = wide_beach.copy()

    for col in [
        "Lifecycle_Priority", "ML_Daily_PctRank", "MA_Breadth_Ratio",
        "Price", "Distance_To_EMA20", "Distance_To_MA50",
        "Distance_To_MA200", "Days_Since_Price_EMA20_Cross"
    ]:
        if col in wb.columns:
            wb[col] = pd.to_numeric(wb[col], errors="coerce")

    market_data_through = (
        pd.to_datetime(wb["Market_Data_Through"], errors="coerce").max()
        if "Market_Data_Through" in wb.columns else pd.NaT
    )

    system_refresh = (
        wb["System_Refresh_Time"].dropna().iloc[-1]
        if "System_Refresh_Time" in wb.columns and not wb["System_Refresh_Time"].dropna().empty
        else "N/A"
    )

    st.subheader("Current Lifecycle Beach")
    st.caption(
        "Current-state view of the full universe: Early Detection → Confirming / Building → "
        "Leading → Mature / Extended → Weakening / Pullback → Below Structure. "
        "The stage labels and symbols carry the meaning; color is supplemental only."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Assets", wb["Ticker"].nunique())
    m2.metric(
        "Market Data Through",
        market_data_through.strftime("%Y-%m-%d") if pd.notna(market_data_through) else "N/A"
    )
    m3.metric("System Refresh", system_refresh)

    lifecycle_order = [
        "1 — EARLY DETECTION",
        "2 — CONFIRMING / BUILDING",
        "3 — LEADING",
        "4 — MATURE / EXTENDED",
        "5 — WEAKENING / PULLBACK",
        "6 — BELOW STRUCTURE",
    ]

    lifecycle_short = {
        "1 — EARLY DETECTION": "1. EARLY DETECTION",
        "2 — CONFIRMING / BUILDING": "2. CONFIRMING / BUILDING",
        "3 — LEADING": "3. LEADING",
        "4 — MATURE / EXTENDED": "4. MATURE / EXTENDED",
        "5 — WEAKENING / PULLBACK": "5. WEAKENING / PULLBACK",
        "6 — BELOW STRUCTURE": "6. BELOW STRUCTURE",
    }

    counts = wb["Lifecycle_Zone"].value_counts().reindex(lifecycle_order, fill_value=0)

    # --------------------------------------------------------
    # STEP 34B.1 — GRAPHICAL WIDE BEACH
    # Position, labels, counts, symbols, and borders carry the
    # meaning. Color is supplemental only.
    # --------------------------------------------------------

    total_assets = int(wb["Ticker"].nunique())
    constructive_count = int(
        counts.loc["1 — EARLY DETECTION"]
        + counts.loc["2 — CONFIRMING / BUILDING"]
        + counts.loc["3 — LEADING"]
    )
    mature_count = int(counts.loc["4 — MATURE / EXTENDED"])
    weak_count = int(
        counts.loc["5 — WEAKENING / PULLBACK"]
        + counts.loc["6 — BELOW STRUCTURE"]
    )

    constructive_pct = (constructive_count / total_assets * 100) if total_assets else 0.0
    weak_pct = (weak_count / total_assets * 100) if total_assets else 0.0

    b1, b2, b3 = st.columns(3)
    b1.metric(
        "Constructive Side · Stages 1–3",
        f"{constructive_count} / {total_assets}",
        f"{constructive_pct:.0f}% of universe",
        delta_color="off"
    )
    b2.metric(
        "Mature / Extended · Stage 4",
        f"{mature_count} / {total_assets}",
        "Transition zone",
        delta_color="off"
    )
    b3.metric(
        "Weak Side · Stages 5–6",
        f"{weak_count} / {total_assets}",
        f"{weak_pct:.0f}% of universe",
        delta_color="off"
    )

    if weak_count > constructive_count:
        st.warning(
            f"Current breadth is concentrated on the weak side of the lifecycle: "
            f"{weak_count} of {total_assets} assets ({weak_pct:.0f}%) are in "
            f"Weakening / Pullback or Below Structure, versus "
            f"{constructive_count} ({constructive_pct:.0f}%) in Early Detection through Leading. "
            f"This is descriptive breadth context, not a market-timing instruction."
        )
    else:
        st.info(
            f"Current breadth has {constructive_count} of {total_assets} assets "
            f"({constructive_pct:.0f}%) in Early Detection through Leading and "
            f"{weak_count} ({weak_pct:.0f}%) in Weakening / Pullback or Below Structure. "
            f"This is descriptive breadth context, not a market-timing instruction."
        )

    stage_meta = {
        "1 — EARLY DETECTION": ("①", "Fresh signal", "New lifecycle event"),
        "2 — CONFIRMING / BUILDING": ("②", "Building evidence", "Early confirmation"),
        "3 — LEADING": ("③", "Leadership", "Confirmed strength"),
        "4 — MATURE / EXTENDED": ("④", "Mature trend", "Watch extension"),
        "5 — WEAKENING / PULLBACK": ("⑤", "Losing momentum", "Review structure"),
        "6 — BELOW STRUCTURE": ("⑥", "Structural weakness", "Below key structure"),
    }

    def _html_escape(value):
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    beach_cards = []
    for zone in lifecycle_order:
        symbol, stage_line, interpretation = stage_meta[zone]
        tickers_here = (
            wb.loc[wb["Lifecycle_Zone"] == zone, "Ticker"]
            .dropna()
            .astype(str)
            .tolist()
        )
        ticker_html = "".join(
            f'<span class="wb-ticker">{_html_escape(ticker)}</span>'
            for ticker in tickers_here
        ) or '<span class="wb-empty">—</span>'

        beach_cards.append(
            f"""
            <div class="wb-stage">
                <div class="wb-stage-number">{symbol}</div>
                <div class="wb-stage-title">{_html_escape(lifecycle_short[zone])}</div>
                <div class="wb-stage-count">{len(tickers_here)}</div>
                <div class="wb-stage-line">{_html_escape(stage_line)}</div>
                <div class="wb-stage-note">{_html_escape(interpretation)}</div>
                <div class="wb-tickers">{ticker_html}</div>
            </div>
            """
        )

    st.markdown("#### Lifecycle Flow")
    st.caption(
        "Read left → right. Each asset occupies one current lifecycle stage. "
        "Ticker position and stage labels carry the meaning even without color."
    )

    st.markdown(
        """
<style>
.wb-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
    width: 100%;
    align-items: stretch;
    margin: 0.25rem 0 0.75rem 0;
}
.wb-stage {
    border: 2px solid rgba(49, 51, 63, 0.45);
    border-top-width: 7px;
    border-radius: 8px;
    padding: 10px 9px 12px 9px;
    min-height: 255px;
    background: rgba(250, 250, 250, 0.55);
}
.wb-stage:nth-child(1),
.wb-stage:nth-child(2),
.wb-stage:nth-child(3) {
    border-top-style: solid;
}
.wb-stage:nth-child(4) {
    border-top-style: double;
}
.wb-stage:nth-child(5),
.wb-stage:nth-child(6) {
    border-top-style: dashed;
}
.wb-stage-number {
    font-size: 1.35rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 5px;
}
.wb-stage-title {
    font-size: 0.73rem;
    font-weight: 800;
    min-height: 34px;
    line-height: 1.15;
}
.wb-stage-count {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
    margin-top: 5px;
}
.wb-stage-line {
    font-size: 0.72rem;
    font-weight: 700;
    margin-top: 4px;
}
.wb-stage-note {
    font-size: 0.67rem;
    opacity: 0.72;
    min-height: 30px;
    margin-bottom: 8px;
}
.wb-tickers {
    border-top: 1px solid rgba(49, 51, 63, 0.25);
    padding-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    align-content: flex-start;
}
.wb-ticker {
    display: inline-block;
    border: 1px solid rgba(49, 51, 63, 0.42);
    border-radius: 5px;
    padding: 2px 5px;
    font-size: 0.68rem;
    font-weight: 700;
    line-height: 1.2;
    background: rgba(255, 255, 255, 0.72);
}
.wb-empty {
    opacity: 0.55;
    font-size: 0.8rem;
}
@media (max-width: 1100px) {
    .wb-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
</style>
<div class="wb-grid">
"""
        + "".join(beach_cards)
        + "</div>",
        unsafe_allow_html=True
    )

    st.info(
        "Wide Beach is a lifecycle / structure view, not a BUY / SELL engine. "
        "An asset can retain strong prior ML evidence while its current technical lifecycle weakens."
    )

    st.divider()

    st.subheader("Current Wide Beach Detail")

    zone_filter = st.multiselect(
        "Lifecycle Zones",
        lifecycle_order,
        default=lifecycle_order,
        key="wide_beach_lifecycle_filter"
    )

    current_view = wb[wb["Lifecycle_Zone"].isin(zone_filter)].copy()
    current_view = current_view.sort_values(
        ["Lifecycle_Priority", "ML_Daily_PctRank", "Ticker"],
        ascending=[True, False, True],
        na_position="last"
    )

    current_cols = [c for c in [
        "Ticker", "Lifecycle_Zone", "Decision_Support_State", "Detection_State",
        "ML_Quality", "ML_Daily_PctRank", "Confirmation_State", "Rotation_State",
        "Structure_State", "Structure_History_Status", "MA_Breadth_Display",
        "EMA20_Position", "MA30_Position", "MA50_Position", "MA100_Position",
        "MA200_Position", "Distance_To_MA50"
    ] if c in current_view.columns]

    current_display = current_view[current_cols].copy()
    if "ML_Daily_PctRank" in current_display.columns:
        current_display["ML_Daily_PctRank"] = current_display["ML_Daily_PctRank"] * 100
    if "Distance_To_MA50" in current_display.columns:
        current_display["Distance_To_MA50"] = current_display["Distance_To_MA50"] * 100

    st.dataframe(
        current_display,
        width="stretch",
        hide_index=True,
        height=520,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Lifecycle_Zone": st.column_config.TextColumn("Lifecycle", width="medium"),
            "Decision_Support_State": st.column_config.TextColumn("Decision Support", width="medium"),
            "Detection_State": st.column_config.TextColumn("Detection", width="medium"),
            "ML_Quality": st.column_config.TextColumn("ML Quality", width="medium"),
            "ML_Daily_PctRank": st.column_config.NumberColumn("ML Daily Rank", format="%.1f%%"),
            "Confirmation_State": st.column_config.TextColumn("Confirmation", width="medium"),
            "Rotation_State": st.column_config.TextColumn("Rotation", width="small"),
            "Structure_State": st.column_config.TextColumn("Structure", width="medium"),
            "Structure_History_Status": st.column_config.TextColumn("History", width="medium"),
            "MA_Breadth_Display": st.column_config.TextColumn("MA Breadth", width="small"),
            "Distance_To_MA50": st.column_config.NumberColumn("% vs MA50", format="%.1f%%"),
        }
    )

    st.divider()

    st.subheader("Technology Complex — Current Lifecycle")
    st.caption(
        "Peer-context panel for XLK / DRAM / SOXX / SMH. It shows how the technology complex "
        "is behaving today without creating a new technology score."
    )

    tech_order = {"XLK": 1, "DRAM": 2, "SOXX": 3, "SMH": 4}
    tech = wb[wb["Ticker"].isin(tech_order)].copy()
    tech["_order"] = tech["Ticker"].map(tech_order)
    tech = tech.sort_values("_order")

    tech_cols = [c for c in [
        "Ticker", "Lifecycle_Zone", "Decision_Support_State", "Detection_State",
        "ML_Quality", "Confirmation_State", "Rotation_State", "Structure_State",
        "MA_Breadth_Display", "Distance_To_MA50"
    ] if c in tech.columns]
    tech_display = tech[tech_cols].copy()
    if "Distance_To_MA50" in tech_display.columns:
        tech_display["Distance_To_MA50"] = tech_display["Distance_To_MA50"] * 100

    st.dataframe(
        tech_display,
        width="stretch",
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Lifecycle_Zone": st.column_config.TextColumn("Lifecycle", width="medium"),
            "Decision_Support_State": st.column_config.TextColumn("Decision Support", width="medium"),
            "Detection_State": st.column_config.TextColumn("Detection", width="medium"),
            "ML_Quality": st.column_config.TextColumn("ML Quality", width="medium"),
            "Confirmation_State": st.column_config.TextColumn("Confirmation", width="medium"),
            "Rotation_State": st.column_config.TextColumn("Rotation", width="small"),
            "Structure_State": st.column_config.TextColumn("Structure", width="medium"),
            "MA_Breadth_Display": st.column_config.TextColumn("MA Breadth", width="small"),
            "Distance_To_MA50": st.column_config.NumberColumn("% vs MA50", format="%.1f%%"),
        }
    )

    st.divider()
    st.subheader("Historical MA Workbench")
    st.caption(
        "Use the historical controls below after the current lifecycle view identifies an asset or group worth investigating."
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
        "A page-by-page operating guide for turning Walker Analytics into a repeatable decision-support process. "
        "The system separates market context, hierarchy, early detection, ML quality, confirmation, trend structure, "
        "leadership, and position risk so that no single indicator is treated as an automatic trade instruction."
    )

    st.info(
        "Daily operating idea: Command Center tells you what matters now; Market Map shows where an asset sits and whether "
        "its move is supported across peers and broader levels; EMA20 detects possible new moves; ML ranks current early "
        "opportunities; Rotation Analysis confirms established leadership; MA structure and risk rules help manage positions after entry."
    )

    st.subheader("1. Recommended Daily Workflow")

    workflow = pd.DataFrame([
        {"Step": 1, "Page": "Command Center", "Question Answered": "What matters today?", "How to Use It": "Start here. Read the Morning Read, market-wide counts, current opportunity pipeline, technology complex, leadership, and risk watch before drilling down."},
        {"Step": 2, "Page": "Market Map", "Question Answered": "Where does this asset belong, and is its move supported?", "How to Use It": "Compare the asset with appropriate peers first, then move vertically through Asset Class → Sector → Peer Group → Instrument."},
        {"Step": 3, "Page": "Rotation Decision Support", "Question Answered": "Does this early opportunity deserve investigation?", "How to Use It": "Review Day 0–4 timing, current ML quality, confirmation, MA structure, early rotation state, and decision-support state."},
        {"Step": 4, "Page": "MA / EMA Radar", "Question Answered": "What is happening technically right now?", "How to Use It": "Verify EMA20 event timing, slope, distance from moving averages, broader MA structure, and recent cross history."},
        {"Step": 5, "Page": "Wide Beach", "Question Answered": "How did price and the moving averages get here?", "How to Use It": "Inspect exact historical price/MA relationships, compare peers on the same sessions, and identify which MA is relevant for structure or risk."},
        {"Step": 6, "Page": "Early Rotation", "Question Answered": "Where might capital be starting to move?", "How to Use It": "Use faster EMA20/MA30 evidence and acceleration to identify possible new flows before leadership is fully established."},
        {"Step": 7, "Page": "Rotation Analysis", "Question Answered": "Where is leadership already established?", "How to Use It": "Use momentum, acceleration, trend, and readiness to distinguish leaders, emerging assets, weakening assets, and laggards."},
        {"Step": 8, "Page": "Asset Explorer", "Question Answered": "What does this specific asset look like?", "How to Use It": "Drill into the individual asset after reviewing broader market, hierarchy, timing, and rotation context."},
        {"Step": 9, "Page": "Research Evidence", "Question Answered": "Why does Walker Analytics work this way?", "How to Use It": "Review the validated backtests, walk-forward ML findings, rejected hypotheses, stop research, and portfolio tradeoffs behind the operating rules."},
    ])

    st.dataframe(workflow, width="stretch", hide_index=True, height=390)

    st.divider()
    st.subheader("2. How the Pages Feed Each Other")
    st.markdown("""
**Command Center**  
↓  
**Market Map — Where does it belong and is strength broad or isolated?**  
↓  
**EMA20 Detection — Did something new happen?**  
↓  
**ML Quality — Was this historically a higher-quality type of early opportunity?**  
↓  
**Days 1–4 Confirmation — Is evidence developing?**  
↓  
**Peer + Vertical Hierarchy — Do peers, sector, and broader levels support the move?**  
↓  
**MA Structure — Is technical structure supportive?**  
↓  
**Rotation Analysis — Is leadership becoming established?**  
↓  
**Position / Risk Management — How much room should the trend receive?**
""")

    st.success("Key concept: the day number tells you WHEN to look. ML and hierarchy help tell you WHAT KIND of opportunity you are looking at.")

    st.divider()
    st.subheader("3. EMA20 Cross — Which Day Matters?")
    st.caption("Day numbers are trading sessions since the bullish EMA20 cross. The cross session itself is Day 0. The research supports a detection-and-confirmation window, not a magic buy day.")

    day_guide = pd.DataFrame([
        {"Day": "Day 0", "Role": "DETECT", "Interpretation": "The event just happened. Earliest warning that behavior may be changing.", "Focus": "Look. Do not treat the cross alone as proof."},
        {"Day": "Day 1", "Role": "VERIFY", "Interpretation": "The move survived one trading session.", "Focus": "Check EMA slope, current ML quality, hierarchy, MA structure, and rotation evidence."},
        {"Day": "Day 2", "Role": "INVESTIGATE", "Interpretation": "More evidence exists while the move is still close to the initiating event.", "Focus": "Strong candidates deserve deeper investigation."},
        {"Day": "Day 3", "Role": "PAY PARTICULAR ATTENTION", "Interpretation": "Day 3 had the strongest simple Early-Leader rate in the historical day-age sample.", "Focus": "Give it extra attention, but do not create a Day-3 automatic-buy rule."},
        {"Day": "Day 4", "Role": "LATE CONFIRMATION", "Interpretation": "Still inside the preferred Days 1–4 research window with more confirmation than Day 0.", "Focus": "Useful if quality remains strong and the asset has not become excessively extended."},
        {"Day": "Day 5", "Role": "LATE EARLY", "Interpretation": "Still fresh enough to monitor, but outside the preferred research entry window used in portfolio tests.", "Focus": "Treat as late-stage early evidence rather than a preferred new entry."},
        {"Day": "Day 6+", "Role": "MANAGE AS A TREND", "Interpretation": "The original EMA20 event is no longer fresh.", "Focus": "Shift emphasis toward leadership, hierarchy, pullbacks, MA structure, and position management."},
    ])
    st.dataframe(day_guide, width="stretch", hide_index=True, height=320)
    st.info("Historical Day-0 through Day-5 Early-Leader rates were approximately 13.1%, 13.8%, 14.1%, 14.7%, 14.5%, and 14.5%. The differences support a window, not a magic day.")

    st.divider()
    st.subheader("4. How to Use the Market Map")
    st.markdown("""
The Market Map adds two different kinds of context:

**Horizontal analysis — compare within the right role.**  
DRAM should be compared with semiconductor peers such as SOXX and SMH. XLK is a broader Technology sector ETF and should not be treated as the same kind of instrument. Future individual securities such as MU should primarily compete with individual-security peers.

**Vertical analysis — move through the hierarchy.**  
`Asset Class → Sector → Peer Group → Instrument`

The question is not just, “Is the ticker strong?” It is also, “Are the surrounding levels supporting the move?”
""")

    hierarchy_reads = pd.DataFrame([
        {"Read": "★★ BROAD MULTI-LEVEL CONFIRMATION", "Meaning": "The asset itself, its peers, its sector, and broader context are substantially aligned.", "How to Use It": "Strong contextual support. Still verify timing, extension, and risk."},
        {"Read": "★ STRONG HIERARCHICAL CONFIRMATION", "Meaning": "The asset is strong relative to peers and several broader levels are supportive.", "How to Use It": "Treat as stronger evidence than an isolated ticker move."},
        {"Read": "▲ MULTI-LEVEL SUPPORT", "Meaning": "Multiple levels are supportive, but not all evidence is at the strongest level.", "How to Use It": "Positive context; investigate the asset-level setup."},
        {"Read": "▲ ASSET LEADS MIXED PEERS", "Meaning": "The asset may be moving before its peer group broadly confirms.", "How to Use It": "Interesting early behavior, but broader confirmation is incomplete."},
        {"Read": "⚠ ISOLATED STRENGTH / BROADER CAUTION", "Meaning": "The ticker is stronger than the surrounding hierarchy.", "How to Use It": "Investigate why. Do not assume isolated strength represents durable capital flow."},
        {"Read": "● BROADER SUPPORT / ASSET NOT ACTIVE", "Meaning": "The surrounding group/sector is favorable, but the individual asset has not activated.", "How to Use It": "Watch for a future asset-level trigger."},
        {"Read": "▲ ASSET + SECTOR SUPPORT / NO PEER SET", "Meaning": "The asset and sector are supportive, but the peer group is too small for a meaningful peer comparison.", "How to Use It": "Use available context without manufacturing a peer result."},
        {"Read": "▼ MULTI-LEVEL CAUTION", "Meaning": "Weakness or structural caution exists at multiple levels.", "How to Use It": "Treat the broader environment as a headwind."},
        {"Read": "● MIXED HIERARCHY", "Meaning": "The levels do not agree strongly enough for a clear hierarchical conclusion.", "How to Use It": "Rely more heavily on asset-specific evidence and continue monitoring."},
    ])
    st.dataframe(hierarchy_reads, width="stretch", hide_index=True, height=430)
    st.warning("NO PEER COMPARISON YET is not a bearish signal. It means the current tracked universe does not contain enough comparable instruments in that peer group.")

    st.divider()
    st.subheader("5. How to Read ML Quality")
    st.markdown("""
Walker Analytics uses walk-forward Random Forest results as a **candidate-quality filter**, not a prediction of certainty.

**Current ML Rank** applies when the asset is in the model's current early-entry population.

**Prior Early-Window ML Rank** preserves useful historical context after an asset ages out of the early window. It should not be read as a current recommendation.

Example: a 92nd-percentile current ML rank means the setup ranked higher than most comparable historical early opportunities in that model run. It does **not** mean there is a 92% probability of profit.
""")

    st.divider()
    st.subheader("6. Early Rotation vs Rotation Analysis")
    st.markdown("""
**Early Rotation:** “Where might capital be starting to move?” It emphasizes faster EMA20/MA30 evidence, acceleration, and early-state transitions.

**Rotation Analysis:** “Where is leadership already established?” It emphasizes momentum, acceleration, trend health, readiness, and confirmed leadership states.

A strong system needs both. Early detection without confirmation creates false starts; leadership without early detection can identify the move only after much of it has already happened.
""")
    st.success("Leadership tells us where money already is. Early Rotation should tell us where it appears to be going next.")

    st.divider()
    st.subheader("7. Moving Averages and Position Management")
    ma_roles = pd.DataFrame([
        {"Reference": "EMA20", "Primary Job": "Early detection / timing", "Research Lesson": "Useful for finding possible new moves; too fast to serve every structural-risk job."},
        {"Reference": "MA30 / MA50", "Primary Job": "Intermediate trend / tighter risk context", "Research Lesson": "Can control losses faster, but tighter exits may truncate right-tail winners."},
        {"Reference": "MA100", "Primary Job": "Intermediate structural / earned-protection context", "Research Lesson": "Useful as part of earned progressive protection, not automatically best for every asset."},
        {"Reference": "MA200", "Primary Job": "Wider structural trend reference", "Research Lesson": "Often reduced drawdown and preserved long trends, but frequently sacrificed raw CAGR versus buy-and-hold."},
    ])
    st.dataframe(ma_roles, width="stretch", hide_index=True)
    st.markdown("""
**Current earned-protection research framework**

- After approximately **+5% peak gain** → MA100 can become the earned protection tier.
- After approximately **+10% peak gain** → MA50 can become the earned protection tier.
- After approximately **+20% peak gain** → MA30 can become the earned protection tier.

The **MA tier ratchets tighter**, but the actual dollar reference remains the **current day's value of that moving average**. The moving-average dollar price itself is not frozen.
""")
    st.warning("The dashboard's MA references are research and decision-support context. Actual order type, position size, account restrictions, gaps, slippage, and personal risk tolerance still matter.")

    st.divider()
    st.subheader("8. What Walker Analytics Does NOT Mean")
    does_not_mean = pd.DataFrame([
        {"Display / Observation": "92nd-percentile ML rank", "Does NOT Mean": "92% probability the trade makes money."},
        {"Display / Observation": "▲ NEW DETECTION", "Does NOT Mean": "BUY now."},
        {"Display / Observation": "★★ HIGH INTEREST", "Does NOT Mean": "Automatic portfolio entry."},
        {"Display / Observation": "● ESTABLISHED LEADER", "Does NOT Mean": "Buy regardless of extension or risk."},
        {"Display / Observation": "▼ STRUCTURAL CAUTION", "Does NOT Mean": "Automatic SELL."},
        {"Display / Observation": "▲ STRONG WITHIN PEERS", "Does NOT Mean": "The broader sector or market is also strong."},
        {"Display / Observation": "★★ BROAD MULTI-LEVEL CONFIRMATION", "Does NOT Mean": "Guaranteed continuation."},
        {"Display / Observation": "A new candidate ranks higher than a current holding", "Does NOT Mean": "Sell the holding and rotate automatically."},
        {"Display / Observation": "NO PEER COMPARISON YET", "Does NOT Mean": "Weak asset."},
    ])
    st.dataframe(does_not_mean, width="stretch", hide_index=True)

    st.divider()
    st.subheader("9. Practical Daily Checklist")
    checklist = pd.DataFrame([
        {"Order": 1, "Check": "Read the Command Center Morning Read.", "Why": "Understand today's broad situation before focusing on a ticker."},
        {"Order": 2, "Check": "Review New Detection / Early Watch / Investigate / High Interest counts.", "Why": "Know whether the market is producing new opportunities or mostly established trends."},
        {"Order": 3, "Check": "Open the Market Map for interesting tickers.", "Why": "Determine whether the move is peer-supported, sector-supported, isolated, or mixed."},
        {"Order": 4, "Check": "Check the EMA20 day number.", "Why": "Know whether the setup is detection, confirmation, late early, or established trend."},
        {"Order": 5, "Check": "Read Current ML Quality only if the asset is in the current early window.", "Why": "Avoid treating stale historical ML evidence as a current model opinion."},
        {"Order": 6, "Check": "Verify MA / EMA structure and distance.", "Why": "Separate an attractive setup from one that is excessively extended or structurally weak."},
        {"Order": 7, "Check": "Review Early Rotation and Rotation Analysis.", "Why": "Determine whether capital flow is just beginning or leadership is already established."},
        {"Order": 8, "Check": "Use Wide Beach when exact MA history matters.", "Why": "Inspect the actual historical relationship rather than relying only on a summary state."},
        {"Order": 9, "Check": "Use Asset Explorer for final ticker-level review.", "Why": "Bring the market, hierarchy, timing, and asset evidence together before making an independent decision."},
        {"Order": 10, "Check": "Manage existing positions separately from new-opportunity ranking.", "Why": "A new candidate does not automatically invalidate an existing successful trend."},
    ])
    st.dataframe(checklist, width="stretch", hide_index=True, height=410)
    st.success("Operating principle: detect early, compare appropriately, confirm broadly, manage risk separately, and use the research evidence to understand why each layer exists.")

    st.divider()
    st.subheader("10. Current Research Frontier")
    st.markdown("""
The hierarchy and peer-intelligence layers are currently **descriptive decision support**. The next research phase is to reconstruct these features historically and test whether:

1. **Peer-relative strength** improves future Early-Leader identification.
2. **Vertical hierarchy confirmation** adds predictive value beyond EMA20 and the existing ML feature set.
3. **Risk-On / Risk-Off regime context** adds independent information rather than duplicating what EMA20 and momentum already capture.

Only features that improve out-of-sample evidence should be allowed into the production ML model.
""")
    st.info("Research rule: useful-looking information can stay on the dashboard as context even if it does not earn a place in the predictive model.")


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
