# ============================================================
# memory/chat_memory.py
# ============================================================
from memory.memory_repository import memory_repository
from memory.conversation_summarizer import conversation_summarizer


class ChatMemory:

    def save_user_message(self, patient_id: str, message: str):
        memory_repository.save_message(patient_id, "user", message)

    def save_ai_message(self, patient_id: str, message: str):
        memory_repository.save_message(patient_id, "assistant", message)

    def build_memory_context(self, patient_id: str) -> str:
        messages = memory_repository.get_recent_messages(patient_id, limit=15)
        summary  = memory_repository.get_summary(patient_id)

        # ── Summarize older messages (keep only last 5 fresh) ──────
        if len(messages) > 5:
            old_messages = messages[:-5]
            old_text = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['message']}"
                for m in old_messages
            )
            new_summary = conversation_summarizer.summarize(summary, old_text)
            memory_repository.save_summary(patient_id, new_summary)
            summary = new_summary

        # ── Build recent conversation text ─────────────────────────
        recent_messages = messages[-5:]
        recent_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['message']}"
            for m in recent_messages
        )

        return f"""Conversation Summary:
{summary or 'No summary yet.'}

Recent Conversation:
{recent_text or 'No messages yet.'}"""


chat_memory = ChatMemory()