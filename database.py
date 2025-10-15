# database.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/pasiya_md_test')
client = MongoClient(MONGO_URI)
db = client.get_database("pasiya_md_db")
signals_col = db.get_collection("signals")

def save_signal(doc):
    result = signals_col.insert_one({**doc, "created_at": datetime.utcnow()})
    return str(result.inserted_id)

def update_signal(signal_id, update_fields):
    from bson import ObjectId
    return signals_col.update_one({"_id": ObjectId(signal_id)}, {"$set": update_fields})

def find_pending_signals(limit=50):
    return list(signals_col.find({"status":"PENDING"}).sort("created_at", -1).limit(limit))
