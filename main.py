# main.py
import os
import time
import json
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
from forex_analyzer import generate_signal_for_pair
from database import save_signal, update_signal, find_pending_signals
from utils.messages import format_signal_msg, format_tp_hit_msg

SIGNAL_INTERVAL = int(os.getenv("SIGNAL_INTERVAL_MIN", "15"))
GROUP_JID = os.getenv("GROUP_JID", "(oyaage_jid_daanna)")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Colombo")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PASIYA-MD")

PAIRS = ["EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD"]  # customize

def send_to_whatsapp(message, group_jid=GROUP_JID):
    """
    Placeholder function to send a message to WhatsApp group.
    Options:
      - Implement a Node.js Baileys/whatsapp-web.js script and call via subprocess
      - Use Twilio WhatsApp API (paid)
      - Use WhatsApp Cloud API (Facebook business)
      - Use Selenium to automate web.whatsapp (fragile)
    For now, we log & save to DB. Replace this body with actual sender integration.
    """
    logger.info(f"Sending to WhatsApp Group {group_jid}: {message[:120]}...")
    # Example: call node sender
    # import subprocess, shlex
    # subprocess.Popen(["node","./whatsapp_sender/send_whatsapp.js", group_jid, message])
    return True

def dispatch_signal(signal):
    doc = {
        "pair": signal["pair"],
        "timeframe": signal.get("timeframe","15m"),
        "signal_type": signal["type"],
        "entry": float(signal["entry"]),
        "tp": float(signal["tp"]),
        "sl": float(signal["sl"]),
        "status": "PENDING",
        "timestamp": datetime.utcnow()
    }
    signal_id = save_signal(doc)
    # send formatted message
    msg = format_signal_msg(signal)
    send_to_whatsapp(msg)
    logger.info(f"Dispatched signal {signal_id} for {signal['pair']}")
    return signal_id

def check_tp_hits():
    """Check pending signals and verify if TP hit via latest price."""
    pending = find_pending_signals(limit=100)
    if not pending:
        return
    for s in pending:
        pair = s["pair"]
        # fetch latest price (use FCS quick quote endpoint)
        try:
            from forex_analyzer import fetch_candles
            df = fetch_candles(pair=pair, interval="1m", limit=3)
            if df.empty:
                continue
            last_price = float(df.iloc[-1]["close"])
            tp = float(s["tp"])
            sl = float(s["sl"])
            # check
            hit = None
            if s["signal_type"] == "BUY" and last_price >= tp:
                hit = "TP"
            elif s["signal_type"] == "SELL" and last_price <= tp:
                hit = "TP"
            elif s["signal_type"] == "BUY" and last_price <= sl:
                hit = "SL"
            elif s["signal_type"] == "SELL" and last_price >= sl:
                hit = "SL"
            if hit:
                status = "TP_HIT" if hit=="TP" else "SL_HIT"
                update_signal(s["_id"], {"status": status, "result_time": datetime.utcnow(), "close_price": last_price})
                # notify group
                if hit=="TP":
                    send_to_whatsapp(format_tp_hit_msg(s))
        except Exception as e:
            logger.exception("check_tp_hits error: %s", e)

def job_generate_signals():
    logger.info("Running signal generation job...")
    # Only run Mon-Fri
    now = datetime.utcnow()
    # basic weekday check (0=Mon,6=Sun)
    if now.weekday() >= 5:
        logger.info("Market probably closed (weekend). Skipping.")
        return
    for pair in PAIRS:
        try:
            signal = generate_signal_for_pair(pair=pair, timeframe="15m")
            if signal:
                dispatch_signal(signal)
        except Exception as e:
            logger.exception("Error generating signal for %s: %s", pair, e)

def job_check_hits():
    logger.info("Running TP/SL checker...")
    check_tp_hits()

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Generate signals every SIGNAL_INTERVAL minutes
    scheduler.add_job(job_generate_signals, 'interval', minutes=SIGNAL_INTERVAL, id='gen_signals')
    # Check TP hits more frequently (every minute)
    scheduler.add_job(job_check_hits, 'interval', minutes=1, id='check_hits')
    logger.info("Starting PASIYA-MD scheduler...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down.")
