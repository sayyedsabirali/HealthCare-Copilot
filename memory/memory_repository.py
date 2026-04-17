# ============================================================
# memory/memory_repository.py
# ============================================================
from database.mongo_client import db
from datetime import datetime


class MemoryRepository:

    def __init__(self):
        self.collection = db["chat_memory"]

    def save_message(self, patient_id: str, role: str, message: str):
        self.collection.insert_one({
            "patient_id": patient_id,
            "role":       role,        # "user" or "assistant"
            "message":    message,
            "type":       "message",   # ← explicit type so summaries are excluded
            "timestamp":  datetime.utcnow(),
        })

    def get_recent_messages(self, patient_id: str, limit: int = 15) -> list:
        """Return only message documents (type='message'), newest-first reversed."""
        messages = list(
            self.collection.find(
                {"patient_id": patient_id, "type": "message"}   # ← filter out summaries
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
        return messages[::-1]   # chronological order

    def get_summary(self, patient_id: str) -> str:
        doc = self.collection.find_one(
            {"patient_id": patient_id, "type": "summary"}
        )
        return doc.get("summary", "") if doc else ""

    def save_summary(self, patient_id: str, summary: str):
        self.collection.update_one(
            {"patient_id": patient_id, "type": "summary"},
            {"$set": {"summary": summary, "updated_at": datetime.utcnow()}},
            upsert=True,
        )


memory_repository = MemoryRepository()
