# PASIYA-MD-forex-
# PASIYA-MD FOREX SIGNAL BOT (Heroku-ready)
Auto Forex market signal WhatsApp bot core (Python) + MongoDB logging + FCS API integration.

## Quick start
1. Copy `.env.example` to `.env` and fill values (or set config vars on Heroku).
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure MongoDB is reachable (local or Atlas).
4. Setup WhatsApp sender (see whatsapp_sender/send_whatsapp.js) and scan QR if using Baileys.
5. Run: `python main.py`
