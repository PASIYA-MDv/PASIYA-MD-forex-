# main.py
import os, logging
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from forex_analyzer import generate_signal_for_pair, fetch_candles
from database import save_signal, update_signal, find_pending_signals
from utils.messages import format_signal_msg, format_tp_hit_msg
from utils.logger import get_logger

logger = get_logger()

SIGNAL_INTERVAL = int(os.getenv('SIGNAL_INTERVAL_MIN', '15'))
GROUP_JID = os.getenv('GROUP_JID', 'group@whatsapp.net')
PAIRS = ['EURUSD','GBPUSD','USDJPY','AUDUSD','USDCAD']

def send_to_whatsapp(message, group_jid=GROUP_JID):
    # Placeholder: call Node Baileys sender or other method
    logger.info(f"[WhatsApp SEND] Group:{group_jid} Msg:{message[:120]}")
    return True

def dispatch_signal(signal):
    doc = {
        'pair': signal['pair'],
        'timeframe': signal.get('timeframe','15m'),
        'signal_type': signal['type'],
        'entry': float(signal['entry']),
        'tp': float(signal['tp']),
        'sl': float(signal['sl']),
        'status': 'PENDING',
        'timestamp': datetime.utcnow()
    }
    signal_id = save_signal(doc)
    msg = format_signal_msg(signal)
    send_to_whatsapp(msg)
    logger.info(f"Dispatched signal {signal_id} for {signal['pair']}")
    return signal_id

def check_tp_hits():
    pending = find_pending_signals(limit=100)
    if not pending:
        return
    for s in pending:
        try:
            df = fetch_candles(pair=s['pair'], interval='1m', limit=3)
            if df.empty:
                continue
            last_price = float(df.iloc[-1]['close'])
            tp = float(s['tp'])
            sl = float(s['sl'])
            hit = None
            if s['signal_type'] == 'BUY' and last_price >= tp:
                hit = 'TP'
            elif s['signal_type'] == 'SELL' and last_price <= tp:
                hit = 'TP'
            elif s['signal_type'] == 'BUY' and last_price <= sl:
                hit = 'SL'
            elif s['signal_type'] == 'SELL' and last_price >= sl:
                hit = 'SL'
            if hit:
                status = 'TP_HIT' if hit=='TP' else 'SL_HIT'
                update_signal(s['_id'], {'status': status, 'result_time': datetime.utcnow(), 'close_price': last_price})
                if hit=='TP':
                    send_to_whatsapp(format_tp_hit_msg(s))
        except Exception as e:
            logger.exception('Error checking TP/SL: %s', e)

def job_generate_signals():
    logger.info('Running signal generation job...')
    now = datetime.utcnow()
    if now.weekday() >= 5:
        logger.info('Weekend: skipping signal generation.')
        return
    for pair in PAIRS:
        try:
            signal = generate_signal_for_pair(pair=pair, timeframe='15m')
            if signal:
                dispatch_signal(signal)
        except Exception as e:
            logger.exception('Error generating for %s: %s', pair, e)

def job_check_hits():
    logger.info('Running TP/SL checker...')
    check_tp_hits()

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(job_generate_signals, 'interval', minutes=SIGNAL_INTERVAL, id='gen_signals')
    scheduler.add_job(job_check_hits, 'interval', minutes=1, id='check_hits')
    logger.info('Starting PASIYA-MD scheduler...')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Shutting down.')
