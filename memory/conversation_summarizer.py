# ============================================================
# memory/conversation_summarizer.py
# ============================================================

from backend.core.llm_provider import llm_provider


class ConversationSummarizer:

    def __init__(self):
        # ✅ FIX: use summary model (not main chat model)
        self.llm = llm_provider.get_summary_llm()

    def summarize(self, previous_summary: str, old_messages: str) -> str:

        # ✅ TOKEN CONTROL (VERY IMPORTANT)
        old_messages = old_messages[-2000:]

        prompt = f"""Compress this medical conversation into a 2-3 sentence memory summary.

Keep only: symptoms reported, medications mentioned, diagnoses, doctor advice.
Drop: explanations, greetings, repeated info.

Previous summary: {previous_summary or 'None'}

Messages to compress:
{old_messages}

Return ONLY the updated summary, no preamble."""

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()

        # ✅ FAIL-SAFE (rate limit / API error)
        except Exception as e:
            print("⚠️ Summarizer failed:", str(e))
            return previous_summary or ""


# Singleton
conversation_summarizer = ConversationSummarizer()