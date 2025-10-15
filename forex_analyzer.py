# forex_analyzer.py
import os, requests, pandas as pd, numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from dotenv import load_dotenv

load_dotenv()
FCS_BASE = os.getenv('FCS_BASE', 'https://fcsapi.com')
FCS_API_KEY = os.getenv('FCS_API_KEY')
if not FCS_API_KEY:
    raise Exception('FCS_API_KEY not set')

def fetch_candles(pair='EURUSD', interval='1m', limit=200):
    # Adjust to actual FCS endpoint if different
    url = f"{FCS_BASE}/market/candles"
    params = {'symbol': pair, 'resolution': interval, 'limit': limit, 'api_key': FCS_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    # Flexible parsing
    if isinstance(data, dict) and 'candles' in data:
        df = pd.DataFrame(data['candles'])
    elif isinstance(data, dict) and 'values' in data:
        df = pd.DataFrame(data['values'])
    else:
        df = pd.DataFrame(data)
    # normalize columns
    for col in ['close','open','high','low','time']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def make_indicators(df):
    if df.empty or 'close' not in df.columns:
        return df
    close = df['close'].astype(float)
    ema8 = EMAIndicator(close, window=8).ema_indicator()
    ema21 = EMAIndicator(close, window=21).ema_indicator()
    rsi = RSIIndicator(close, window=14).rsi()
    df['ema8'] = ema8
    df['ema21'] = ema21
    df['rsi'] = rsi
    return df

def generate_signal_for_pair(pair='EURUSD', timeframe='15m'):
    res_map = {'1m':'1m','5m':'5m','15m':'15m','1h':'60m'}
    res = res_map.get(timeframe, '15m')
    df = fetch_candles(pair=pair, interval=res, limit=200)
    df = make_indicators(df)
    if df.empty or 'close' not in df.columns:
        return None
    last = df.iloc[-1]
    entry = float(last['close'])
    ema8 = float(last.get('ema8', np.nan))
    ema21 = float(last.get('ema21', np.nan))
    rsi = float(last.get('rsi', np.nan) if not np.isnan(last.get('rsi', np.nan)) else 50)
    pip = 0.0001
    if np.isnan(ema8) or np.isnan(ema21):
        return None
    direction = None
    if ema8 > ema21 and rsi < 75:
        direction = 'BUY'
    elif ema8 < ema21 and rsi > 25:
        direction = 'SELL'
    else:
        return None
    tp_pips = 10
    sl_pips = 15
    if pair.upper().startswith('XAU') or pair.upper().startswith('GOLD'):
        pip = 0.01
        tp_pips = 30
        sl_pips = 50
    if direction == 'BUY':
        tp = round(entry + tp_pips * pip, 6)
        sl = round(entry - sl_pips * pip, 6)
    else:
        tp = round(entry - tp_pips * pip, 6)
        sl = round(entry + sl_pips * pip, 6)
    signal = {
        'pair': pair,
        'timeframe': timeframe,
        'type': direction,
        'entry': entry,
        'tp': tp,
        'sl': sl,
        'indicator': {'ema8': ema8, 'ema21': ema21, 'rsi': rsi},
    }
    return signal
