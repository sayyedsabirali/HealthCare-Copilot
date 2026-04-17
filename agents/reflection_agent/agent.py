from backend.core.llm_provider import llm_provider
import json


class ReflectionAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def verify_response(
        self,
        question: str,
        draft_answer: str,
        context: dict,
        memory_context: str = "",
    ) -> str:
        context = context or {}

        # Skip for short responses
        if len(draft_answer.split()) < 15:
            return draft_answer

        context_str = json.dumps(context, indent=2, default=str)

        prompt = f"""You are a quality checker for medical responses.

--- PATIENT ---
{context_str}

--- USER QUESTION ---
{question}

--- DRAFT RESPONSE ---
{draft_answer}

--- YOUR JOB ---
Check if this response is:
1. Safe (no harmful advice)
2. Complete (not cut off mid-sentence)
3. Personalized (mentions patient's condition)

--- RULES ---
- If safe and complete → return it exactly as-is
- If unsafe → rewrite it safely
- If cut off → complete the last sentence naturally
- If too generic → add minimal personalization

Don't change the tone or style. Just fix problems.

Return ONLY the final response."""

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception:
            return draft_answer


# Instance
reflection_agent = ReflectionAgent()