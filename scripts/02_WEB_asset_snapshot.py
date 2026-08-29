#!/usr/bin/env python
# coding: utf-8

# # Walker Analytics — Web Asset Snapshot
# Creates `web_asset_snapshot.csv` from the web project's existing `sector_returns.csv` and `moving_average_latest.csv`.
# 
# This notebook does **not** download data and does **not** target the production `NoWiseDashboard`.

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard")
DATA_DIR = BASE_DIR / "data_processed"
OUTPUT_FILE = DATA_DIR / "web_asset_snapshot.csv"

print("=" * 70)
print("WALKER ANALYTICS — WEB ASSET SNAPSHOT")
print("=" * 70)
print("DATA_DIR:", DATA_DIR)
print("This notebook does NOT target NoWiseDashboard.")


# In[2]:


RETURNS_FILE = DATA_DIR / "sector_returns.csv"
MA_FILE = DATA_DIR / "moving_average_latest.csv"

for f in [RETURNS_FILE, MA_FILE]:
    if not f.exists():
        raise FileNotFoundError(f"Required input file not found: {f}")
    print("OK:", f.name, "|", f"{f.stat().st_size:,}", "bytes")


# In[3]:


returns = pd.read_csv(RETURNS_FILE)
ma = pd.read_csv(MA_FILE)

print("Returns shape:", returns.shape)
print("MA latest shape:", ma.shape)
print("\nReturn columns:", list(returns.columns))
print("\nMA columns:", list(ma.columns))


# In[4]:


def normalize_ticker(df):
    df = df.copy()
    if "Ticker" in df.columns:
        pass
    else:
        candidates = [c for c in df.columns if str(c).lower() in {"ticker","symbol","index","unnamed: 0"}]
        df = df.rename(columns={(candidates[0] if candidates else df.columns[0]): "Ticker"})
    df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    return df

returns = normalize_ticker(returns)
ma = normalize_ticker(ma)

# Support common return-column names from the current pipeline.
aliases = {
    "1W":"Return_1W", "2W":"Return_2W", "1M":"Return_1M",
    "3M":"Return_3M", "6M":"Return_6M", "9M":"Return_9M", "12M":"Return_12M",
    "1W_Return":"Return_1W", "2W_Return":"Return_2W", "1M_Return":"Return_1M",
    "3M_Return":"Return_3M", "6M_Return":"Return_6M", "9M_Return":"Return_9M",
    "12M_Return":"Return_12M"
}
for old, new in aliases.items():
    if old in returns.columns and new not in returns.columns:
        returns = returns.rename(columns={old:new})

wanted_returns = ["Ticker","Return_1W","Return_2W","Return_1M","Return_3M","Return_6M","Return_9M","Return_12M"]
returns_web = returns[[c for c in wanted_returns if c in returns.columns]].copy()

wanted_ma = [
    "Ticker","Price","EMA20","MA30","MA50","MA100","MA200",
    "AboveEMA20","Above30","Above50","Above100","Above200",
    "Pct_Above_EMA20","Pct_Above_30","Pct_Above_50","Pct_Above_100","Pct_Above_200"
]
ma_web = ma[[c for c in wanted_ma if c in ma.columns]].copy()

print("Return fields:", list(returns_web.columns))
print("MA fields:", list(ma_web.columns))


# In[5]:


snapshot = ma_web.merge(returns_web, on="Ticker", how="left", validate="one_to_one")

def boolish(v):
    if pd.isna(v): return np.nan
    if isinstance(v, (bool, np.bool_)): return bool(v)
    t = str(v).strip().lower()
    if t in {"true","1","yes","y"}: return True
    if t in {"false","0","no","n"}: return False
    return np.nan

major_flags = [c for c in ["Above30","Above50","Above100","Above200"] if c in snapshot.columns]
for c in major_flags:
    snapshot[c] = snapshot[c].map(boolish)

snapshot["Major_MAs_Above"] = snapshot[major_flags].sum(axis=1, min_count=1) if major_flags else np.nan

def trend_label(n):
    if pd.isna(n): return "Insufficient Data"
    if n >= 4: return "Strong Uptrend"
    if n == 3: return "Uptrend"
    if n == 2: return "Mixed"
    if n == 1: return "Downtrend"
    return "Strong Downtrend"

snapshot["Trend_Structure"] = snapshot["Major_MAs_Above"].apply(trend_label)

preferred = [
    "Ticker","Price","Return_1W","Return_2W","Return_1M","Return_3M","Return_6M","Return_9M","Return_12M",
    "EMA20","MA30","MA50","MA100","MA200","AboveEMA20","Above30","Above50","Above100","Above200",
    "Pct_Above_EMA20","Pct_Above_30","Pct_Above_50","Pct_Above_100","Pct_Above_200",
    "Major_MAs_Above","Trend_Structure"
]
ordered = [c for c in preferred if c in snapshot.columns]
snapshot = snapshot[ordered + [c for c in snapshot.columns if c not in ordered]].sort_values("Ticker").reset_index(drop=True)

print("Snapshot shape:", snapshot.shape)
print(snapshot["Trend_Structure"].value_counts(dropna=False))
snapshot.head(10)


# In[6]:


if snapshot.empty:
    raise ValueError("Web asset snapshot is empty.")
if snapshot["Ticker"].duplicated().any():
    raise ValueError("Duplicate tickers found in web asset snapshot.")

snapshot.to_csv(OUTPUT_FILE, index=False)

print("=" * 70)
print("WEB ASSET SNAPSHOT EXPORT COMPLETE")
print("=" * 70)
print("Saved:", OUTPUT_FILE)
print("Rows:", len(snapshot))
print("Columns:", len(snapshot.columns))
print("Size:", f"{OUTPUT_FILE.stat().st_size:,}", "bytes")
print("SUCCESS — ready for the future Streamlit app.")


# # import sys
# print(sys.executable)

# In[7]:


import sys
print(sys.executable)

