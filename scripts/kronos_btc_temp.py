import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

# Exact official Kronos repository is cloned by the workflow into ./Kronos
sys.path.insert(0, str(Path("Kronos").resolve()))
from model import Kronos, KronosTokenizer, KronosPredictor

# TradingView historical data via tvdatafeed (read-only, no indicators/analysis).
from tvDatafeed import TvDatafeed, Interval

SYMBOL = "BTCUSDT"
EXCHANGE = "BINANCE"
INTERVAL_NAME = "1h"
LOOKBACK = 360
PRED_LEN = 24
SEED = 42

OUT = Path("results")
OUT.mkdir(exist_ok=True)

np.random.seed(SEED)
torch.manual_seed(SEED)

# Fetch a few extra bars so the currently-forming candle can be removed.
tv = TvDatafeed()
raw = tv.get_hist(
    symbol=SYMBOL,
    exchange=EXCHANGE,
    interval=Interval.in_1_hour,
    n_bars=LOOKBACK + 4,
    extended_session=False,
)
if raw is None or raw.empty:
    raise RuntimeError("TradingView returned no BTCUSDT history.")

# Auto-detect and normalize the columns required by Kronos.
df = raw.copy()
df.columns = [str(c).strip().lower() for c in df.columns]
aliases = {
    "open": ["open", "o"],
    "high": ["high", "h"],
    "low": ["low", "l"],
    "close": ["close", "c"],
    "volume": ["volume", "vol", "v"],
}
detected = {}
for canonical, choices in aliases.items():
    hit = next((c for c in choices if c in df.columns), None)
    if hit is None:
        raise ValueError(f"TradingView data missing required column for {canonical}: {list(df.columns)}")
    detected[canonical] = hit

if not isinstance(df.index, pd.DatetimeIndex):
    # Fallback time-column detection, though tvdatafeed normally uses the index.
    time_candidates = [c for c in df.columns if c in ("time", "timestamp", "datetime", "date")]
    if not time_candidates:
        raise ValueError("Could not detect a timestamp column/index in TradingView data.")
    df.index = pd.to_datetime(df[time_candidates[0]], utc=False)

df.index = pd.to_datetime(df.index)
if df.index.tz is not None:
    df.index = df.index.tz_convert("UTC").tz_localize(None)

df = df.rename(columns={v: k for k, v in detected.items()})
df = df[["open", "high", "low", "close", "volume"]].copy()
for c in ["open", "high", "low", "close", "volume"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Chronological integrity.
df = df.sort_index()
duplicate_count = int(df.index.duplicated(keep="last").sum())
if duplicate_count:
    df = df[~df.index.duplicated(keep="last")]

nan_count = int(df.isna().sum().sum())
if nan_count:
    raise ValueError(f"TradingView data contains {nan_count} NaN values after normalization.")

# Remove any still-forming hourly bar. GitHub-hosted runner clock is UTC.
now_utc = pd.Timestamp.now(tz="UTC").tz_localize(None)
if len(df) and df.index[-1] + pd.Timedelta(hours=1) > now_utc:
    df = df.iloc[:-1]

if len(df) < LOOKBACK:
    raise ValueError(f"Only {len(df)} closed TradingView bars available; need {LOOKBACK}.")

df = df.tail(LOOKBACK).copy()

diffs = df.index.to_series().diff().dropna()
bad_gaps = diffs[diffs != pd.Timedelta(hours=1)]
gap_count = int(len(bad_gaps))
if gap_count:
    samples = [str(x) for x in bad_gaps.iloc[:5].tolist()]
    raise ValueError(f"Detected {gap_count} non-1h gaps in TradingView BTC data: {samples}")

# Sanity checks for OHLC geometry.
invalid_ohlc = (
    (df["high"] < df[["open", "close", "low"]].max(axis=1)) |
    (df["low"] > df[["open", "close", "high"]].min(axis=1))
)
if invalid_ohlc.any():
    raise ValueError(f"Detected {int(invalid_ohlc.sum())} invalid OHLC rows.")

# Official Kronos BTC-demo model family/configuration: Kronos-mini + Tokenizer-2k.
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-2k")
model = Kronos.from_pretrained("NeoQuasar/Kronos-mini")
tokenizer.eval()
model.eval()
predictor = KronosPredictor(model, tokenizer, device="cpu", max_context=2048)

x_df = df.reset_index(drop=True)[["open", "high", "low", "close", "volume"]]
x_timestamp = pd.Series(df.index)
forecast_start = df.index[-1] + pd.Timedelta(hours=1)
y_timestamp = pd.Series(pd.date_range(forecast_start, periods=PRED_LEN, freq="1h"))

t0 = time.time()
with torch.no_grad():
    pred_df = predictor.predict(
        df=x_df,
        x_timestamp=x_timestamp,
        y_timestamp=y_timestamp,
        pred_len=PRED_LEN,
        T=1.0,
        top_p=0.95,
        sample_count=30,
        verbose=False,
    )
elapsed = round(time.time() - t0, 3)

# Enforce only candlestick geometry after model averaging (no technical analysis).
# If averaging causes a wick to sit inside the body, expand it to enclose body.
pred_df = pred_df.copy()
pred_df["high"] = pred_df[["high", "open", "close"]].max(axis=1)
pred_df["low"] = pred_df[["low", "open", "close"]].min(axis=1)
pred_df["volume"] = pred_df["volume"].clip(lower=0)

# Save a compact combined file: recent Actual + all Kronos Forecast.
plot_actual = df.tail(120).copy()
rows = []
for ts, row in plot_actual.iterrows():
    rows.append({
        "type": "Actual",
        "timestamp": ts.isoformat(),
        "open": float(row.open), "high": float(row.high), "low": float(row.low),
        "close": float(row.close), "volume": float(row.volume),
    })
for ts, row in pred_df.iterrows():
    rows.append({
        "type": "Kronos Forecast",
        "timestamp": pd.Timestamp(ts).isoformat(),
        "open": float(row.open), "high": float(row.high), "low": float(row.low),
        "close": float(row.close), "volume": float(row.volume),
    })
pd.DataFrame(rows).to_csv(OUT / "BTC_Kronos_Result.csv", index=False)

metadata = {
    "asset": "BTCUSDT",
    "tradingview_symbol": "BINANCE:BTCUSDT",
    "data_source": "TradingView",
    "interval": INTERVAL_NAME,
    "model": "NeoQuasar/Kronos-mini",
    "tokenizer": "NeoQuasar/Kronos-Tokenizer-2k",
    "official_kronos_revision": "67b630e67f6a18c9e9be918d9b4337c960db1e9a",
    "input_candles": LOOKBACK,
    "predicted_candles": PRED_LEN,
    "history_start": df.index[0].isoformat(),
    "history_end": df.index[-1].isoformat(),
    "forecast_start": y_timestamp.iloc[0].isoformat(),
    "forecast_end": y_timestamp.iloc[-1].isoformat(),
    "last_actual_close": float(df["close"].iloc[-1]),
    "forecast_final_close": float(pred_df["close"].iloc[-1]),
    "parameters": {"T": 1.0, "top_p": 0.95, "sample_count": 30, "seed": SEED},
    "validation": {
        "detected_columns": detected,
        "sorted_ascending": bool(df.index.is_monotonic_increasing),
        "duplicates_removed": duplicate_count,
        "non_1h_gaps": gap_count,
        "nan_values": nan_count,
        "invalid_ohlc_rows": int(invalid_ohlc.sum()),
    },
    "inference_seconds": elapsed,
}
(OUT / "BTC_Kronos_Metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(json.dumps(metadata, indent=2))
