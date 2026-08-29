#!/usr/bin/env python
# coding: utf-8

# # Walker Analytics — Rotation Analytics Layer
# 
# **Notebook:** `03_WEB_rotation_analytics_(08-22-2026).ipynb`
# 
# Purpose: build the first web-facing rotation analytics layer from the existing web project outputs.
# 
# Inputs:
# - `sector_returns.csv`
# - `web_asset_snapshot.csv`
# 
# Output:
# - `web_rotation_snapshot.csv`
# 
# This notebook is part of the **Walker Analytics web project only** and does **not** target the operational `NoWiseDashboard`.
# 

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(
    r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard"
)

DATA_DIR = BASE_DIR / "data_processed"

RETURNS_FILE = DATA_DIR / "sector_returns.csv"
ASSET_FILE = DATA_DIR / "web_asset_snapshot.csv"
OUTPUT_FILE = DATA_DIR / "web_rotation_snapshot.csv"

print("=" * 72)
print("WALKER ANALYTICS — ROTATION ANALYTICS")
print("=" * 72)
print("DATA_DIR:", DATA_DIR)
print("OUTPUT:", OUTPUT_FILE)
print()
print("This notebook does NOT target the production NoWiseDashboard.")


# In[2]:


required_files = [RETURNS_FILE, ASSET_FILE]

for f in required_files:
    if not f.exists():
        raise FileNotFoundError(f"Required input file not found: {f}")
    print("OK:", f.name, "|", f"{f.stat().st_size:,}", "bytes")


# In[3]:


returns = pd.read_csv(RETURNS_FILE)
asset = pd.read_csv(ASSET_FILE)

print("sector_returns.csv shape:", returns.shape)
print("web_asset_snapshot.csv shape:", asset.shape)
print("\nReturn columns:")
print(list(returns.columns))
print("\nAsset snapshot columns:")
print(list(asset.columns))


# In[4]:


def normalize_ticker(df):
    df = df.copy()

    if "Ticker" not in df.columns:
        candidates = [
            c for c in df.columns
            if str(c).lower() in {"ticker", "symbol", "index", "unnamed: 0"}
        ]
        source = candidates[0] if candidates else df.columns[0]
        df = df.rename(columns={source: "Ticker"})

    df["Ticker"] = (
        df["Ticker"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return df


returns = normalize_ticker(returns)
asset = normalize_ticker(asset)

# Normalize return column names from either common pipeline convention.
aliases = {
    # Current sector_returns.csv naming convention
    "1W%": "Return_1W",
    "2W%": "Return_2W",
    "1M%": "Return_1M",
    "3M%": "Return_3M",
    "6M%": "Return_6M",
    "9M%": "Return_9M",
    "12M%": "Return_12M",

    # Alternate supported conventions
    "1W": "Return_1W",
    "2W": "Return_2W",
    "1M": "Return_1M",
    "3M": "Return_3M",
    "6M": "Return_6M",
    "9M": "Return_9M",
    "12M": "Return_12M",
    "1W_Return": "Return_1W",
    "2W_Return": "Return_2W",
    "1M_Return": "Return_1M",
    "3M_Return": "Return_3M",
    "6M_Return": "Return_6M",
    "9M_Return": "Return_9M",
    "12M_Return": "Return_12M",
}

for old, new in aliases.items():
    if old in returns.columns and new not in returns.columns:
        returns = returns.rename(columns={old: new})

print("Normalized return columns:")
print(list(returns.columns))


# In[5]:


# Select the return fields available in the current pipeline.
return_fields = [
    "Return_1W",
    "Return_2W",
    "Return_1M",
    "Return_3M",
    "Return_6M",
    "Return_9M",
    "Return_12M",
]

available_return_fields = [
    c for c in return_fields
    if c in returns.columns
]

if len(available_return_fields) < 3:
    raise ValueError(
        "Not enough return horizons were found to build the rotation model. "
        f"Found: {available_return_fields}"
    )

returns_web = returns[
    ["Ticker"] + available_return_fields
].copy()

print("Using return fields:", available_return_fields)


# In[6]:


# Merge return data with the current web asset snapshot.
rotation = asset.merge(
    returns_web,
    on="Ticker",
    how="left",
    suffixes=("", "_returns")
)

# If the asset snapshot already contains return columns, preserve those and
# fill missing values from sector_returns.csv.
for c in available_return_fields:
    alt = f"{c}_returns"

    if c in rotation.columns and alt in rotation.columns:
        rotation[c] = rotation[c].combine_first(rotation[alt])
        rotation = rotation.drop(columns=[alt])

    elif c not in rotation.columns and alt in rotation.columns:
        rotation = rotation.rename(columns={alt: c})

print("Merged rotation table shape:", rotation.shape)


# In[7]:


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def percentile_score(series):
    """
    Convert values into a 0-100 cross-sectional percentile score.
    Higher raw value -> higher score.
    """
    s = pd.to_numeric(series, errors="coerce")
    return s.rank(pct=True, method="average") * 100


def safe_col(df, name):
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(np.nan, index=df.index)


# ------------------------------------------------------------
# Momentum score
# ------------------------------------------------------------
# Weight the model toward persistent intermediate-term strength
# while retaining responsiveness to recent performance.
momentum_components = []

weights = {
    "Return_1W": 0.10,
    "Return_2W": 0.10,
    "Return_1M": 0.20,
    "Return_3M": 0.25,
    "Return_6M": 0.20,
    "Return_9M": 0.10,
    "Return_12M": 0.05,
}

active_weights = {
    k: v for k, v in weights.items()
    if k in rotation.columns
}

weight_sum = sum(active_weights.values())

for col, weight in active_weights.items():
    normalized_weight = weight / weight_sum
    rotation[f"{col}_PctScore"] = percentile_score(rotation[col])
    momentum_components.append(
        rotation[f"{col}_PctScore"] * normalized_weight
    )

rotation["Momentum_Score"] = sum(momentum_components)

# Rank 1 = strongest.
rotation["Momentum_Rank"] = (
    rotation["Momentum_Score"]
    .rank(ascending=False, method="min")
    .astype("Int64")
)


# In[8]:


# ------------------------------------------------------------
# Acceleration score
# ------------------------------------------------------------
# Concept:
#   recent strength relative to intermediate strength
#   + shorter horizon improvement relative to longer horizon
#
# Positive values indicate improving momentum; negative values indicate
# deceleration. Then convert cross-sectionally into 0-100.

r1w = safe_col(rotation, "Return_1W")
r2w = safe_col(rotation, "Return_2W")
r1m = safe_col(rotation, "Return_1M")
r3m = safe_col(rotation, "Return_3M")
r6m = safe_col(rotation, "Return_6M")

accel_raw = pd.Series(0.0, index=rotation.index)
accel_weight = pd.Series(0.0, index=rotation.index)

def add_accel_component(component, weight):
    global accel_raw, accel_weight
    valid = component.notna()
    accel_raw.loc[valid] += component.loc[valid] * weight
    accel_weight.loc[valid] += weight

add_accel_component(r1w - (r1m / 4.0), 0.30)
add_accel_component(r2w - (r1m / 2.0), 0.25)
add_accel_component(r1m - (r3m / 3.0), 0.25)
add_accel_component((r3m / 3.0) - (r6m / 6.0), 0.20)

rotation["Acceleration_Raw"] = np.where(
    accel_weight > 0,
    accel_raw / accel_weight,
    np.nan
)

rotation["Acceleration_Score"] = percentile_score(
    rotation["Acceleration_Raw"]
)

rotation["Acceleration_Rank"] = (
    rotation["Acceleration_Score"]
    .rank(ascending=False, method="min")
    .astype("Int64")
)


# In[9]:


# ------------------------------------------------------------
# Trend score from MA / EMA positioning
# ------------------------------------------------------------

trend_flag_map = {
    "AboveEMA20": 15,
    "Above30": 15,
    "Above50": 20,
    "Above100": 20,
    "Above200": 30,
}

def boolish(v):
    if pd.isna(v):
        return np.nan

    if isinstance(v, (bool, np.bool_)):
        return bool(v)

    t = str(v).strip().lower()

    if t in {"true", "1", "yes", "y"}:
        return True

    if t in {"false", "0", "no", "n"}:
        return False

    return np.nan


trend_score = pd.Series(0.0, index=rotation.index)
trend_weight = pd.Series(0.0, index=rotation.index)

for col, weight in trend_flag_map.items():

    if col not in rotation.columns:
        continue

    vals = rotation[col].map(boolish)
    valid = vals.notna()

    trend_score.loc[valid] += vals.loc[valid].astype(float) * weight
    trend_weight.loc[valid] += weight

rotation["Trend_Score"] = np.where(
    trend_weight > 0,
    (trend_score / trend_weight) * 100,
    np.nan
)


# In[10]:


# ------------------------------------------------------------
# Rotation Readiness
# ------------------------------------------------------------
# Momentum = existing leadership
# Acceleration = improving / deteriorating rate
# Trend = structural confirmation

rotation["Rotation_Readiness_Score"] = (
    rotation["Momentum_Score"] * 0.45
    + rotation["Acceleration_Score"] * 0.30
    + rotation["Trend_Score"] * 0.25
)

rotation["Rotation_Readiness_Rank"] = (
    rotation["Rotation_Readiness_Score"]
    .rank(ascending=False, method="min")
    .astype("Int64")
)


# In[11]:


# ------------------------------------------------------------
# Rotation state classification
# ------------------------------------------------------------

def classify_state(row):

    momentum = row.get("Momentum_Score", np.nan)
    accel = row.get("Acceleration_Score", np.nan)
    trend = row.get("Trend_Score", np.nan)
    readiness = row.get("Rotation_Readiness_Score", np.nan)

    if any(pd.isna(v) for v in [momentum, accel, trend, readiness]):
        return "WATCH"

    # Established leaders: strong momentum and confirmed trend.
    if momentum >= 70 and trend >= 80 and readiness >= 70:
        return "LEADER"

    # Emerging candidates: acceleration is strong enough to identify
    # improvement before they necessarily rank as established leaders.
    if accel >= 70 and trend >= 60 and readiness >= 60:
        return "EMERGING"

    # Weakening: momentum is still respectable but acceleration has faded.
    if momentum >= 55 and accel <= 35:
        return "WEAKENING"

    # Lagging: weak momentum plus weak structural trend.
    if momentum <= 35 and trend <= 40:
        return "LAGGING"

    return "WATCH"


rotation["Rotation_State"] = rotation.apply(
    classify_state,
    axis=1
)


# In[12]:


# ------------------------------------------------------------
# Final presentation order
# ------------------------------------------------------------

preferred = [
    "Ticker",
    "Price",
    "Return_1W",
    "Return_2W",
    "Return_1M",
    "Return_3M",
    "Return_6M",
    "Return_9M",
    "Return_12M",
    "Momentum_Score",
    "Momentum_Rank",
    "Acceleration_Raw",
    "Acceleration_Score",
    "Acceleration_Rank",
    "Trend_Score",
    "Trend_Structure",
    "Rotation_Readiness_Score",
    "Rotation_Readiness_Rank",
    "Rotation_State",
    "EMA20",
    "MA30",
    "MA50",
    "MA100",
    "MA200",
    "Pct_Above_EMA20",
    "Pct_Above_30",
    "Pct_Above_50",
    "Pct_Above_100",
    "Pct_Above_200",
]

ordered = [
    c for c in preferred
    if c in rotation.columns
]

extras = [
    c for c in rotation.columns
    if c not in ordered
    and not c.endswith("_PctScore")
]

rotation = rotation[
    ordered + extras
].copy()

rotation = rotation.sort_values(
    ["Rotation_Readiness_Score", "Momentum_Score"],
    ascending=[False, False]
).reset_index(drop=True)

rotation.head(15)


# In[13]:


# ------------------------------------------------------------
# Quality checks and model summary
# ------------------------------------------------------------

if rotation.empty:
    raise ValueError("Rotation snapshot is empty.")

if rotation["Ticker"].duplicated().any():
    dupes = rotation.loc[
        rotation["Ticker"].duplicated(),
        "Ticker"
    ].tolist()

    raise ValueError(
        f"Duplicate tickers found in rotation snapshot: {dupes}"
    )

print("Assets:", rotation["Ticker"].nunique())

print("\nRotation states:")
print(
    rotation["Rotation_State"]
    .value_counts(dropna=False)
)

print("\nTop 10 by Rotation Readiness:")
display_cols = [
    c for c in [
        "Ticker",
        "Momentum_Score",
        "Acceleration_Score",
        "Trend_Score",
        "Rotation_Readiness_Score",
        "Rotation_Readiness_Rank",
        "Rotation_State",
    ]
    if c in rotation.columns
]

print(
    rotation[display_cols]
    .head(10)
    .to_string(index=False)
)


# In[14]:


# Export the web-facing rotation snapshot.
rotation.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 72)
print("ROTATION ANALYTICS EXPORT COMPLETE")
print("=" * 72)
print("Saved:", OUTPUT_FILE)
print("Rows:", len(rotation))
print("Columns:", len(rotation.columns))
print("Size:", f"{OUTPUT_FILE.stat().st_size:,}", "bytes")
print()
print("SUCCESS — web_rotation_snapshot.csv is ready for Streamlit.")

