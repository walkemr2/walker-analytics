#!/usr/bin/env python
# coding: utf-8

# # Sector Flow Data Pipeline — 67 Assets + Moving Averages + EMA20
# 
# Post-crash consolidated master notebook.
# 
# This version combines:
# - the current OneDrive folder structure;
# - the 67-asset universe;
# - sector price and return exports;
# - 30 / 50 / 100 / 200-day moving averages;
# - above/below-MA flags;
# - percentage distance from each MA;
# - `moving_average_metrics.csv`;
# - `moving_average_latest.csv`;
# - `moving_average_wide.csv`;
# - refresh logging.
# 
# **Important improvement:** this version forward-fills only. It does **not** backfill prices before an ETF's inception date, which avoids creating artificial pre-launch history for newer ETFs such as DRAM.
# 

# In[1]:


# Optional install/update. Run only if yfinance is missing or behaving strangely.
# !pip install --upgrade yfinance pandas openpyxl


# In[2]:


import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime


# In[3]:


# ============================================================
# WALKER ANALYTICS WEB PROJECT — ONEDRIVE
# ============================================================

BASE_DIR = Path(
    r"C:\Users\matth\OneDrive\Desktop\04 Investing Stuff\1.1 Stock Trading\3.0 Web Rotation Dashboard"
)

RAW_DIR = BASE_DIR / "data_raw"
DATA_DIR = BASE_DIR / "data_processed"
ARCHIVE_DIR = BASE_DIR / "archive"
CHART_DIR = BASE_DIR / "charts"
CONFIG_DIR = BASE_DIR / "config"
SCRIPT_DIR = BASE_DIR / "scripts"
APP_DIR = BASE_DIR / "dashboard_app"
NOTEBOOK_DIR = BASE_DIR / "notebooks"
README_DIR = BASE_DIR / "README_notes"

PROJECT_DIRS = [
    RAW_DIR,
    DATA_DIR,
    ARCHIVE_DIR,
    CHART_DIR,
    CONFIG_DIR,
    SCRIPT_DIR,
    APP_DIR,
    NOTEBOOK_DIR,
    README_DIR,
]

for folder in PROJECT_DIRS:
    folder.mkdir(parents=True, exist_ok=True)

print("=" * 65)
print("WALKER ANALYTICS — WEB SANDBOX")
print("=" * 65)
print()
print("BASE_DIR:     ", BASE_DIR)
print("DATA_DIR:     ", DATA_DIR)
print("ARCHIVE_DIR:  ", ARCHIVE_DIR)
print("APP_DIR:      ", APP_DIR)
print()
print("IMPORTANT: This notebook is NOT writing to NoWiseDashboard.")
print("=" * 65)


# In[4]:


# =========================
# CORE MARKET INDEXES
# =========================
market_indexes = [
    "SPY",
    "VOO",  # Vanguard S&P 500 ETF
    "QQQ",
    "DIA",
    "IWM",
    "RSP"   # Equal-weight S&P 500; useful for breadth comparisons
]

# =========================
# SECTOR ETFs
# =========================
sector_etfs = [
    "XLK",   # Technology
    "XLE",   # Energy
    "XLF",   # Financials
    "XLV",   # Healthcare
    "XLY",   # Consumer Discretionary
    "XLI",   # Industrials
    "XLB",   # Materials
    "XLU",   # Utilities
    "XLP",   # Consumer Staples
    "XLC",   # Communication Services
    "XLRE",  # Real Estate

    # Energy sub-sectors
    "XOP",   # Oil & Gas Exploration & Production
    "OIH",   # Oil Services
    "AMLP",  # Midstream / MLPs

    # Financial sub-sectors
    "KRE",   # Regional Banks
    "KBE",   # Banks
    "KBWD",  # High-dividend Financials

    # Healthcare sub-sectors
    "XBI",   # Biotech
    "IBB",   # Biotech
    "PPH",   # Pharmaceuticals

    # Consumer / Real Estate sub-sectors
    "PEJ",   # Leisure & Entertainment / Hospitality
    "VNQ",   # Broad REITs
    "REZ"    # Residential / Specialized REITs
]

# =========================
# MACRO / DEFENSIVE
# =========================
macro_etfs = [
    "GLD",
    "SLV",
    "USO",
    "PDBC",
    "TLT",
    "IEF",
    "SHY",
    "TIP",
    "UUP",
    "VIXY"
]

# =========================
# CRYPTO / ALTERNATIVE
# =========================
alternative_assets = [
    "IBIT",
    "ETHE",

    # Commodity / alternative exposures
    "UNG",   # Natural Gas
    "CPER",  # Copper
    "DBA",   # Agriculture basket
    "CORN",  # Corn
    "WEAT"   # Wheat
]

# =========================
# THEMATIC / EMERGING
# =========================
thematic_etfs = [
    "DRAM",
    "SOXX",
    "SMH",
    "BOTZ",
    "AIQ",

    # Technology themes
    "CIBR",  # Cybersecurity
    "SKYY",  # Cloud Computing
    "IGV",   # Software
    "SRVR",  # Data Centers / Digital Infrastructure

    # Financial / Healthcare themes
    "IAI",   # Broker-Dealers & Securities Exchanges
    "ARKG",  # Genomics

    # Industrial themes
    "ITA",   # Aerospace & Defense
    "PAVE",  # U.S. Infrastructure Development
    "AIRR",  # American Industrial Renaissance

    # Materials / electrification themes
    "SLX",   # Steel
    "COPX",  # Copper Miners
    "LITP",  # Lithium Miners
    "BATT",  # Battery Technology / Materials

    # Consumer themes
    "BETZ",  # Sports Betting & Gaming
    "AWAY",  # Travel Technology
    "ONLN"   # Online Retail
]

# =========================
# FINAL MASTER LIST
# =========================
tickers = (
    market_indexes
    + sector_etfs
    + macro_etfs
    + alternative_assets
    + thematic_etfs
)

# Remove duplicates and sort alphabetically for stable Excel output
tickers = sorted(list(set(tickers)))

print("Ticker Count:", len(tickers))
print(tickers)

# Optional category counts for a quick configuration check
print("\nCategory counts:")
print("Market indexes:", len(market_indexes))
print("Sector ETFs:", len(sector_etfs))
print("Macro ETFs:", len(macro_etfs))
print("Alternative assets:", len(alternative_assets))
print("Thematic ETFs:", len(thematic_etfs))


# In[5]:


# ============================================================
# DOWNLOAD DAILY ADJUSTED PRICE DATA
# ============================================================
raw_data = yf.download(
    tickers=tickers,
    period="18mo",
    interval="1d",
    auto_adjust=True,
    group_by="ticker",
    progress=False,
    threads=True
)

print("Raw data shape:", raw_data.shape)
print("Raw data column type:", type(raw_data.columns))
print("Raw data date range:", raw_data.index.min(), "to", raw_data.index.max())
raw_data.tail()


# In[6]:


def extract_close_prices(raw, symbols):
    """Extract adjusted Close prices from yfinance output regardless of column layout."""
    prices = pd.DataFrame(index=raw.index)
    failed = []

    for symbol in symbols:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                lvl0 = list(raw.columns.get_level_values(0))
                lvl1 = list(raw.columns.get_level_values(1))

                if symbol in lvl0 and "Close" in lvl1:
                    prices[symbol] = raw[(symbol, "Close")]
                elif "Close" in lvl0 and symbol in lvl1:
                    prices[symbol] = raw[("Close", symbol)]
                else:
                    raise KeyError(f"{symbol} not found in MultiIndex yfinance result")
            else:
                if "Close" in raw.columns:
                    prices[symbol] = raw["Close"]
                else:
                    raise KeyError("Close column not found")
        except Exception as exc:
            failed.append(symbol)
            print(f"Problem extracting {symbol}: {exc}")

    prices = prices.dropna(how="all")
    return prices, failed


price_data, failed_tickers = extract_close_prices(raw_data, tickers)

print("Initial extracted tickers:", len(price_data.columns))
print("Initial failed tickers:", failed_tickers)


# In[7]:


# ============================================================
# FALLBACK DOWNLOADS + PRICE CLEANUP
# ============================================================
if failed_tickers:
    print("Attempting individual fallback downloads...")

    still_failed = []

    for symbol in failed_tickers:
        try:
            single = yf.download(
                tickers=symbol,
                period="18mo",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False
            )

            if isinstance(single.columns, pd.MultiIndex):
                # yfinance can occasionally return a MultiIndex even for one ticker.
                if ("Close", symbol) in single.columns:
                    close_series = single[("Close", symbol)]
                elif (symbol, "Close") in single.columns:
                    close_series = single[(symbol, "Close")]
                else:
                    close_series = None
            else:
                close_series = single["Close"] if "Close" in single.columns else None

            if close_series is not None and not close_series.dropna().empty:
                price_data[symbol] = close_series
                print(f"Recovered {symbol} with individual download")
            else:
                still_failed.append(symbol)
                print(f"Still missing {symbol}: no Close data returned")

        except Exception as exc:
            still_failed.append(symbol)
            print(f"Still missing {symbol}: {exc}")

    failed_tickers = still_failed

available_tickers = [t for t in tickers if t in price_data.columns]
price_data = price_data[available_tickers]

# Fill only gaps AFTER a ticker has begun trading.
# Do NOT use bfill(): backfilling creates artificial pre-inception prices
# for newer ETFs and corrupts moving-average history.
price_data = price_data.ffill()

price_data.index = pd.to_datetime(price_data.index).date
price_data.index.name = "Date"

print("Available tickers:", len(available_tickers))
print("Failed tickers after fallback:", failed_tickers)
print("Missing price values (includes legitimate pre-inception blanks):",
      int(price_data.isna().sum().sum()))
print("Latest price date:", price_data.index.max())
price_data.tail()


# In[8]:


# ============================================================
# EXPORT PRICE HISTORY
# ============================================================
price_file = DATA_DIR / "sector_prices.csv"
price_data.to_csv(price_file, index=True)

print(f"Saved: {price_file}")
print("Price export rows:", len(price_data))
print("Price export tickers:", len(price_data.columns))
print("VOO exported in prices:", "VOO" in price_data.columns)


# In[9]:


# ============================================================
# CALCULATE + EXPORT LATEST RETURNS
# ============================================================
return_windows = {
    "1W%": 5,
    "2W%": 10,
    "1M%": 21,
    "3M%": 63,
    "6M%": 126,
    "9M%": 189,
    "12M%": 252
}

latest_returns = pd.DataFrame(index=available_tickers)

for label, days in return_windows.items():
    latest_returns[label] = ((price_data.iloc[-1] / price_data.shift(days).iloc[-1]) - 1) * 100

latest_returns = latest_returns.round(2)
latest_returns.index.name = "Ticker"

returns_file = DATA_DIR / "sector_returns.csv"
latest_returns.to_csv(returns_file, index=True)

print(f"Saved: {returns_file}")
print("Return export rows:", len(latest_returns))
print("Missing return values:", int(latest_returns.isna().sum().sum()))
latest_returns.tail()


# In[10]:


# ============================================================
# MOVING AVERAGE + EMA ENGINE
# ============================================================
MA_WINDOWS = [30, 50, 100, 200]
EMA_WINDOWS = [20]

# Simple moving averages
ma_frames = {}
for window in MA_WINDOWS:
    ma_frames[f"MA{window}"] = price_data.rolling(
        window=window,
        min_periods=window
    ).mean()

# Exponential moving averages
ema_frames = {}
for window in EMA_WINDOWS:
    ema_frames[f"EMA{window}"] = price_data.ewm(
        span=window,
        adjust=False,
        min_periods=window
    ).mean()

records = []

for ticker in available_tickers:
    tmp = pd.DataFrame({
        "Date": price_data.index,
        "Ticker": ticker,
        "Price": price_data[ticker].values,
        "EMA20": ema_frames["EMA20"][ticker].values,
        "MA30": ma_frames["MA30"][ticker].values,
        "MA50": ma_frames["MA50"][ticker].values,
        "MA100": ma_frames["MA100"][ticker].values,
        "MA200": ma_frames["MA200"][ticker].values,
    })

    # EMA20 status and excursion
    tmp["AboveEMA20"] = [
        "" if pd.isna(ema) or pd.isna(price)
        else ("Yes" if price > ema else "No")
        for price, ema in zip(tmp["Price"], tmp["EMA20"])
    ]

    tmp["Pct_Above_EMA20"] = (
        (tmp["Price"] - tmp["EMA20"]) / tmp["EMA20"]
    )

    # Existing simple moving-average status and excursion
    for window in MA_WINDOWS:
        ma_col = f"MA{window}"
        above_col = f"Above{window}"
        pct_col = f"Pct_Above_{window}"

        tmp[above_col] = [
            "" if pd.isna(ma) or pd.isna(price)
            else ("Yes" if price > ma else "No")
            for price, ma in zip(tmp["Price"], tmp[ma_col])
        ]

        tmp[pct_col] = (tmp["Price"] - tmp[ma_col]) / tmp[ma_col]

    records.append(tmp)

moving_average_metrics = pd.concat(records, ignore_index=True)

metric_numeric_cols = [
    "Price",
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

moving_average_metrics[metric_numeric_cols] = (
    moving_average_metrics[metric_numeric_cols].round(6)
)

ma_metrics_file = DATA_DIR / "moving_average_metrics.csv"
moving_average_metrics.to_csv(ma_metrics_file, index=False)

latest_date = price_data.index.max()
moving_average_latest = moving_average_metrics[
    moving_average_metrics["Date"] == latest_date
].copy()

moving_average_latest = moving_average_latest.sort_values("Ticker")

ma_latest_file = DATA_DIR / "moving_average_latest.csv"
moving_average_latest.to_csv(ma_latest_file, index=False)

print(f"Saved: {ma_metrics_file}")
print(f"Saved: {ma_latest_file}")
print("Moving average latest rows:", len(moving_average_latest))
print("EMA20 included:", "EMA20" in moving_average_latest.columns)
moving_average_latest.head()


# In[11]:


# ============================================================
# WIDE MOVING AVERAGE + EMA EXPORT
# Used by Excel MA_Chart_View and historical MA analysis
# ============================================================
wide_parts = [pd.DataFrame({"Date": price_data.index})]

for ticker in available_tickers:
    block = pd.DataFrame({
        ticker: price_data[ticker].values,
        f"{ticker}_EMA20": ema_frames["EMA20"][ticker].values,
        f"{ticker}_30": ma_frames["MA30"][ticker].values,
        f"{ticker}_50": ma_frames["MA50"][ticker].values,
        f"{ticker}_100": ma_frames["MA100"][ticker].values,
        f"{ticker}_200": ma_frames["MA200"][ticker].values,
    })

    # EMA20 status and excursion
    block[f"{ticker}_AboveEMA20"] = [
        "" if pd.isna(ema) or pd.isna(price)
        else ("Yes" if price > ema else "No")
        for price, ema in zip(block[ticker], block[f"{ticker}_EMA20"])
    ]

    block[f"{ticker}_Pct_Above_EMA20"] = (
        (block[ticker] - block[f"{ticker}_EMA20"])
        / block[f"{ticker}_EMA20"]
    )

    # Existing simple moving-average status and excursion
    for window in MA_WINDOWS:
        ma_col = f"{ticker}_{window}"

        block[f"{ticker}_Above{window}"] = [
            "" if pd.isna(ma) or pd.isna(price)
            else ("Yes" if price > ma else "No")
            for price, ma in zip(block[ticker], block[ma_col])
        ]

        block[f"{ticker}_Pct_Above_{window}"] = (
            (block[ticker] - block[ma_col]) / block[ma_col]
        )

    wide_parts.append(block)

moving_average_wide = pd.concat(wide_parts, axis=1).round(6)

ma_wide_file = DATA_DIR / "moving_average_wide.csv"
moving_average_wide.to_csv(ma_wide_file, index=False)

print(f"Saved: {ma_wide_file}")
print("Wide MA/EMA rows:", len(moving_average_wide))
print("Wide MA/EMA columns:", len(moving_average_wide.columns))
print("EMA20 wide columns present:",
      any(str(c).endswith("_EMA20") for c in moving_average_wide.columns))


# In[12]:


# ============================================================
# REFRESH / HEALTH LOG
# ============================================================
refresh_log = pd.DataFrame([{
    "Refresh_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "Ticker_Count_Configured": len(tickers),
    "Ticker_Count_Exported": len(available_tickers),
    "Price_Rows": len(price_data),
    "Start_Date": price_data.index.min(),
    "End_Date": price_data.index.max(),
    "Failed_Tickers": ", ".join(failed_tickers),
    "VOO_In_Prices": "VOO" in price_data.columns,
    "VOO_In_Returns": "VOO" in latest_returns.index,
    "Missing_Price_Values": int(price_data.isna().sum().sum()),
    "Missing_Return_Values": int(latest_returns.isna().sum().sum()),
    "MA_Metrics_Rows": len(moving_average_metrics),
    "MA_Latest_Rows": len(moving_average_latest),
    "MA_Wide_Columns": len(moving_average_wide.columns),
    "Status": "Success" if not failed_tickers else "Success_With_Failed_Tickers"
}])

log_file = DATA_DIR / "web_refresh_log.csv"
refresh_log.to_csv(log_file, index=False)

print(f"Saved: {log_file}")
print("Web pipeline refresh completed successfully.")
refresh_log


# In[13]:


# ============================================================
# WALKER ANALYTICS WEB PIPELINE — FINAL FILE CHECK
# ============================================================

expected_data_files = [
    "sector_prices.csv",
    "sector_returns.csv",
    "moving_average_metrics.csv",
    "moving_average_latest.csv",
    "moving_average_wide.csv",
    "web_refresh_log.csv",
]

print("=" * 65)
print("WALKER ANALYTICS WEB PIPELINE — OUTPUT CHECK")
print("=" * 65)

all_files_ok = True

for name in expected_data_files:
    p = DATA_DIR / name

    if p.exists():
        print(
            "OK   ",
            p.name,
            "|",
            f"{p.stat().st_size:,}",
            "bytes"
        )
    else:
        print("MISS ", p.name)
        all_files_ok = False

print()
print("Output directory:")
print(DATA_DIR)
print()

if all_files_ok:
    print("SUCCESS — All expected web data files were created.")
else:
    print("WARNING — One or more expected files are missing.")

print()
print("Production NoWiseDashboard files were NOT targeted by this pipeline.")

