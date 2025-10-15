# forex_analyzer.py
import os
import time
import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from dotenv import load_dotenv

load_dotenv()
FCS_BASE = os.getenv("FCS_BASE", "https://fcsapi.com")
FCS_API_KEY = os.getenv("FCS_API_KEY")

if not FCS_API_KEY:
    raise Exception("FCS_API_KEY missing")

def fetch_candles(pair="EURUSD", interval="1m", limit=200):
    """
    Fetch candles from FCS API (example). Endpoint params may vary — check FCS docs.
    pair: like "EURUSD"
    interval: "1m","5m","15m","1h"
    """
    url = f"{FCS_BASE}/market/candles"
    params = {
        "symbol": pair,
        "resolution": interval,
        "limit": limit,
        "api_key": FCS_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    # Expected: data["candles"] or similar — adapt if FCS returns different shape
    # Try common shape:
    if "candles" in data:
        df = pd.DataFrame(data["candles"])
    elif "values" in data:
        df = pd.DataFrame(data["values"])
    else:
        # Attempt to parse known fields
        df = pd.DataFrame(data)
    # Ensure columns: close, open, high, low, time
    # Convert to numeric
    for col in ["close","open","high","low","time"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def make_indicators(df):
    # Assume df ordered oldest->newest
    if df.empty or "close" not in df.columns:
        return df
    close = df["close"].astype(float)
    # EMA 8 & 21
    ema8 = EMAIndicator(close, window=8).ema_indicator()
    ema21 = EMAIndicator(close, window=21).ema_indicator()
    rsi = RSIIndicator(close, window=14).rsi()
    df["ema8"] = ema8
    df["ema21"] = ema21
    df["rsi"] = rsi
    return df

def generate_signal_for_pair(pair="EURUSD", timeframe="15m"):
    """
    Simple rule-based signal:
    - If EMA8 > EMA21 and RSI between 30-70 -> BUY with entry = last close, TP = entry + X pips, SL = entry - Y pips
    - If EMA8 < EMA21 -> SELL analogously
    """
    # fetch recent candles — use smaller resolution for more timely signals
    resolution_map = {"1m":"1m","5m":"5m","15m":"15m","1h":"60m"}
    res = resolution_map.get(timeframe, "15m")
    df = fetch_candles(pair=pair, interval=res, limit=200)
    df = make_indicators(df)
    if df.empty:
        return None
    last = df.iloc[-1]
    entry = float(last["close"])
    ema8 = float(last.get("ema8", np.nan))
    ema21 = float(last.get("ema21", np.nan))
    rsi = float(last.get("rsi", np.nan) if not np.isnan(last.get("rsi", np.nan)) else 50)
    # pip size guess for major pairs
    pip = 0.0001
    # Decide
    if np.isnan(ema8) or np.isnan(ema21):
        return None
    direction = None
    if ema8 > ema21 and rsi < 75:
        direction = "BUY"
    elif ema8 < ema21 and rsi > 25:
        direction = "SELL"
    else:
        return None
    # Define simple TP/SL (could be dynamic)
    tp_pips = 10  # aim for 10 pips by default (adjustable)
    sl_pips = 15
    if pair.upper().startswith("XAU") or pair.upper().startswith("GOLD"):
        pip = 0.01
        tp_pips = 30
        sl_pips = 50
    if direction == "BUY":
        tp = round(entry + tp_pips * pip, 6)
        sl = round(entry - sl_pips * pip, 6)
    else:
        tp = round(entry - tp_pips * pip, 6)
        sl = round(entry + sl_pips * pip, 6)
    signal = {
        "pair": pair,
        "timeframe": timeframe,
        "type": direction,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "indicator": {"ema8": ema8, "ema21": ema21, "rsi": rsi},
    }
    return signal
