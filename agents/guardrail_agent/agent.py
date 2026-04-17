from backend.core.llm_provider import llm_provider


class GuardrailAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def detect_treatment_decision(self, question: str, context: dict = None) -> str:
        prompt = f"""Check if user wants to CHANGE their medication.

ONLY trigger warning if user is asking to:
- STOP taking medicine
- SKIP a dose
- CHANGE dosage (increase/decrease)
- REPLACE with something else

DO NOT trigger for:
- Asking what medicines they take
- Asking about side effects or disadvantages
- Asking how medicine works
- Asking when to take medicine
- Asking about interactions

Question: {question}

If UNSAFE (asking to stop/skip/change/replace):
→ Return short warning: "Please consult your doctor before making any changes to your medication."

If SAFE:
→ Return exactly: NONE

Return ONLY the warning or NONE."""

        try:
            response = self.llm.invoke(prompt)
            result = response.content.strip()
            
            # If response is long (warning) or NONE
            if "NONE" in result.upper():
                return "NONE"
            return result
            
        except Exception as e:
            print(f"❌ Guardrail error: {e}")
            return "NONE"


guardrail_agent = GuardrailAgent()