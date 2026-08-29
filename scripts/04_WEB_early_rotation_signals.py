#!/usr/bin/env python
# coding: utf-8

# # Walker Analytics — Early Rotation Signals
# 
# **Notebook:** `04_WEB_early_rotation_signals_(08-22-2026).ipynb`
# 
# Purpose: create a **fast / early-stage rotation layer** that is intentionally separate from the slower confirmation model in Notebook 03.
# 
# Inputs:
# - `moving_average_wide.csv`
# - `sector_returns.csv`
# - `web_rotation_snapshot.csv`
# 
# Output:
# - `web_early_rotation_snapshot.csv`
# 
# This layer emphasizes:
# - Price vs. EMA20
# - Price vs. MA30
# - EMA20 vs. MA30
# - EMA20 and MA30 slope
# - recent EMA20/MA30 crosses
# - short-term momentum
# - acceleration
# 
# It is designed to identify **developing setups earlier**, before full trend confirmation is present.
# 

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(
    r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard"
)

DATA_DIR = BASE_DIR / "data_processed"

MA_WIDE_FILE = DATA_DIR / "moving_average_wide.csv"
RETURNS_FILE = DATA_DIR / "sector_returns.csv"
ROTATION_FILE = DATA_DIR / "web_rotation_snapshot.csv"
OUTPUT_FILE = DATA_DIR / "web_early_rotation_snapshot.csv"

print("=" * 72)
print("WALKER ANALYTICS — EARLY ROTATION SIGNALS")
print("=" * 72)
print("Output:", OUTPUT_FILE)
print("This notebook does NOT target the production NoWiseDashboard.")


# In[2]:


for f in [MA_WIDE_FILE, RETURNS_FILE, ROTATION_FILE]:
    if not f.exists():
        raise FileNotFoundError(f"Required input file not found: {f}")
    print("OK:", f.name, "|", f"{f.stat().st_size:,}", "bytes")


# In[3]:


ma = pd.read_csv(MA_WIDE_FILE)
returns = pd.read_csv(RETURNS_FILE)
rotation = pd.read_csv(ROTATION_FILE)

date_col = ma.columns[0]
ma[date_col] = pd.to_datetime(ma[date_col])

# Normalize returns
returns = returns.rename(columns={
    "1W%": "Return_1W",
    "2W%": "Return_2W",
    "1M%": "Return_1M",
    "3M%": "Return_3M",
    "6M%": "Return_6M",
    "9M%": "Return_9M",
    "12M%": "Return_12M",
})

print("MA wide shape:", ma.shape)
print("Returns shape:", returns.shape)
print("Rotation shape:", rotation.shape)


# In[4]:


# Identify tickers from the plain-price columns.
# Every ticker has a price column named exactly like the ticker,
# while derived columns contain underscores.
tickers = [
    c for c in ma.columns
    if c != date_col and "_" not in str(c)
]

print("Tickers found:", len(tickers))
print(tickers[:15])


# In[5]:


def pct_rank(series):
    s = pd.to_numeric(series, errors="coerce")
    return s.rank(pct=True, method="average") * 100

records = []

for ticker in tickers:
    price_col = ticker
    ema20_col = f"{ticker}_EMA20"
    ma30_col = f"{ticker}_30"

    if not all(c in ma.columns for c in [price_col, ema20_col, ma30_col]):
        continue

    df = ma[[date_col, price_col, ema20_col, ma30_col]].dropna(subset=[price_col]).copy()

    if len(df) < 10:
        continue

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = latest[price_col]
    ema20 = latest[ema20_col]
    ma30 = latest[ma30_col]

    # 5-trading-day slope approximation
    ema20_5ago = df[ema20_col].iloc[-6] if len(df) >= 6 else np.nan
    ma30_5ago = df[ma30_col].iloc[-6] if len(df) >= 6 else np.nan

    ema20_slope_5d = (
        (ema20 / ema20_5ago - 1) * 100
        if pd.notna(ema20) and pd.notna(ema20_5ago) and ema20_5ago != 0
        else np.nan
    )

    ma30_slope_5d = (
        (ma30 / ma30_5ago - 1) * 100
        if pd.notna(ma30) and pd.notna(ma30_5ago) and ma30_5ago != 0
        else np.nan
    )

    dist_ema20 = (
        (price / ema20 - 1) * 100
        if pd.notna(price) and pd.notna(ema20) and ema20 != 0
        else np.nan
    )

    dist_ma30 = (
        (price / ma30 - 1) * 100
        if pd.notna(price) and pd.notna(ma30) and ma30 != 0
        else np.nan
    )

    ema20_vs_ma30 = (
        (ema20 / ma30 - 1) * 100
        if pd.notna(ema20) and pd.notna(ma30) and ma30 != 0
        else np.nan
    )

    price_cross_ema20_today = (
        pd.notna(prev[price_col]) and pd.notna(prev[ema20_col]) and
        pd.notna(price) and pd.notna(ema20) and
        prev[price_col] <= prev[ema20_col] and price > ema20
    )

    price_cross_ma30_today = (
        pd.notna(prev[price_col]) and pd.notna(prev[ma30_col]) and
        pd.notna(price) and pd.notna(ma30) and
        prev[price_col] <= prev[ma30_col] and price > ma30
    )

    ema20_cross_ma30_today = (
        pd.notna(prev[ema20_col]) and pd.notna(prev[ma30_col]) and
        pd.notna(ema20) and pd.notna(ma30) and
        prev[ema20_col] <= prev[ma30_col] and ema20 > ma30
    )

    records.append({
        "Ticker": ticker,
        "Price": price,
        "EMA20": ema20,
        "MA30": ma30,
        "Pct_Above_EMA20": dist_ema20,
        "Pct_Above_MA30": dist_ma30,
        "EMA20_vs_MA30_Pct": ema20_vs_ma30,
        "EMA20_Slope_5D_Pct": ema20_slope_5d,
        "MA30_Slope_5D_Pct": ma30_slope_5d,
        "Above_EMA20": bool(pd.notna(price) and pd.notna(ema20) and price > ema20),
        "Above_MA30": bool(pd.notna(price) and pd.notna(ma30) and price > ma30),
        "EMA20_Above_MA30": bool(pd.notna(ema20) and pd.notna(ma30) and ema20 > ma30),
        "Price_Cross_EMA20_Today": price_cross_ema20_today,
        "Price_Cross_MA30_Today": price_cross_ma30_today,
        "EMA20_Cross_MA30_Today": ema20_cross_ma30_today,
    })

early = pd.DataFrame(records)

print("Early-signal rows:", len(early))
early.head()


# In[6]:


# Merge short-term returns and acceleration from Notebook 03.
return_cols = [c for c in ["Ticker", "Return_1W", "Return_2W", "Return_1M"] if c in returns.columns]
early = early.merge(returns[return_cols], on="Ticker", how="left")

rotation_cols = [
    c for c in [
        "Ticker",
        "Acceleration_Score",
        "Momentum_Score",
        "Trend_Score",
        "Rotation_Readiness_Score",
        "Rotation_State"
    ]
    if c in rotation.columns
]

early = early.merge(rotation[rotation_cols], on="Ticker", how="left")

print("Merged columns:", list(early.columns))


# In[7]:


# Build component scores.
# These are intentionally fast-signal oriented rather than confirmation oriented.

early["EMA20_Slope_Score"] = pct_rank(early["EMA20_Slope_5D_Pct"])
early["MA30_Slope_Score"] = pct_rank(early["MA30_Slope_5D_Pct"])
early["EMA20_Expansion_Score"] = pct_rank(early["Pct_Above_EMA20"])
early["Return_1W_Score"] = pct_rank(early["Return_1W"])
early["Return_1M_Score"] = pct_rank(early["Return_1M"])

# Structural fast-trend score
early["Fast_Trend_Score"] = (
    early["Above_EMA20"].astype(int) * 35
    + early["Above_MA30"].astype(int) * 25
    + early["EMA20_Above_MA30"].astype(int) * 20
    + (early["EMA20_Slope_5D_Pct"] > 0).astype(int) * 10
    + (early["MA30_Slope_5D_Pct"] > 0).astype(int) * 10
)

# Cross bonus: gives extra credit to fresh transitions.
early["Fresh_Cross_Bonus"] = (
    early["Price_Cross_EMA20_Today"].astype(int) * 5
    + early["Price_Cross_MA30_Today"].astype(int) * 7
    + early["EMA20_Cross_MA30_Today"].astype(int) * 8
)

# Early Rotation Score
early["Early_Rotation_Score"] = (
    early["Fast_Trend_Score"] * 0.30
    + early["EMA20_Slope_Score"] * 0.15
    + early["MA30_Slope_Score"] * 0.10
    + early["Return_1W_Score"] * 0.15
    + early["Return_1M_Score"] * 0.10
    + early["Acceleration_Score"].fillna(50) * 0.20
    + early["Fresh_Cross_Bonus"]
)

early["Early_Rotation_Score"] = early["Early_Rotation_Score"].clip(upper=100)

early["Early_Rotation_Rank"] = (
    early["Early_Rotation_Score"]
    .rank(ascending=False, method="min")
    .astype("Int64")
)


# In[8]:


# Classification states.
# "EXTENDED" is intentionally separated from "EARLY ENTRY" because
# strong expansion can mean the signal is no longer early.

def classify_early(row):
    score = row["Early_Rotation_Score"]
    dist = row["Pct_Above_EMA20"]
    accel = row.get("Acceleration_Score", np.nan)

    if pd.isna(score):
        return "NO SIGNAL"

    if pd.notna(dist) and dist >= 8:
        return "EXTENDED"

    if (
        row["Above_EMA20"]
        and row["Above_MA30"]
        and score >= 70
        and (pd.isna(accel) or accel >= 55)
    ):
        return "EARLY ENTRY"

    if row["Above_EMA20"] and score >= 60:
        return "BUILDING"

    if (
        pd.notna(dist)
        and -2 <= dist <= 2
        and row["EMA20_Slope_5D_Pct"] > 0
    ):
        return "EARLY WATCH"

    return "NO SIGNAL"

early["Early_Rotation_State"] = early.apply(classify_early, axis=1)

state_order = ["EARLY ENTRY", "BUILDING", "EARLY WATCH", "EXTENDED", "NO SIGNAL"]

print(early["Early_Rotation_State"].value_counts())


# In[9]:


# Final sort and export
preferred = [
    "Ticker",
    "Price",
    "EMA20",
    "MA30",
    "Pct_Above_EMA20",
    "Pct_Above_MA30",
    "EMA20_vs_MA30_Pct",
    "EMA20_Slope_5D_Pct",
    "MA30_Slope_5D_Pct",
    "Above_EMA20",
    "Above_MA30",
    "EMA20_Above_MA30",
    "Price_Cross_EMA20_Today",
    "Price_Cross_MA30_Today",
    "EMA20_Cross_MA30_Today",
    "Return_1W",
    "Return_1M",
    "Acceleration_Score",
    "Momentum_Score",
    "Early_Rotation_Score",
    "Early_Rotation_Rank",
    "Early_Rotation_State",
    "Rotation_Readiness_Score",
    "Rotation_State",
]

cols = [c for c in preferred if c in early.columns]

early = early[cols].sort_values(
    ["Early_Rotation_Score", "Ticker"],
    ascending=[False, True]
).reset_index(drop=True)

early.to_csv(OUTPUT_FILE, index=False)

print("=" * 72)
print("EARLY ROTATION EXPORT COMPLETE")
print("=" * 72)
print("Saved:", OUTPUT_FILE)
print("Rows:", len(early))
print("Columns:", len(early.columns))
print("\nTop 15 early-rotation candidates:")
print(
    early[
        [
            "Ticker",
            "Early_Rotation_Score",
            "Early_Rotation_Rank",
            "Early_Rotation_State",
            "Pct_Above_EMA20",
            "EMA20_Slope_5D_Pct",
            "Acceleration_Score"
        ]
    ]
    .head(15)
    .to_string(index=False)
)

