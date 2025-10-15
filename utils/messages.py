# utils/messages.py
from datetime import datetime
import os
OWNER = os.getenv('OWNER_NUMBER', '94784548818')
ADMIN = os.getenv('ADMIN_NUMBER', '947666359869')

def format_signal_msg(signal):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = (
        f"NOW SIGNAL TIME 🔥\n"
        f"POWERED_BY PASIYA-MD\n\n"
        f"💸 *FOREX SIGNAL*\n"
        f"Pair: {signal['pair']}\n"
        f"Type: {signal['type']}\n"
        f"Entry: {signal['entry']}\n"
        f"TP: {signal['tp']}\n"
        f"SL: {signal['sl']}\n"
        f"Timeframe: {signal.get('timeframe','M15')}\n\n"
        f"⏱ Sent by PASIYA-MD at {t}\n"
        f"OWNER: {OWNER}  ADMIN: {ADMIN}"
    )
    return msg

def format_tp_hit_msg(signal):
    t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"✅ TP HIT 🎯\nPOWERED_BY PASIYA-MD\nPair: {signal['pair']} TP: {signal['tp']}\nTime: {t}"
