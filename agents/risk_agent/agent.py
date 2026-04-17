from backend.core.llm_provider import llm_provider
from tools.symptom_checker_tool import symptom_checker_tool
import json


class RiskAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def analyze_symptom(
        self,
        question: str,
        symptom: str,
        context: dict = None,
        memory_context: str = "",
    ):
        context = context or {}
        
        # Tool use: Get possible conditions for symptom
        symptom_data = None
        if symptom and symptom != question:
            print(f"🔍 Checking symptom: {symptom}")
            symptom_data = symptom_checker_tool.search_symptom(symptom)
        
        context_str = json.dumps(context, indent=2, default=str)
        symptom_str = json.dumps(symptom_data, indent=2, default=str) if symptom_data else "Use your medical knowledge"

        prompt = f"""You are a caring, experienced doctor doing a quick risk check for your patient.

--- PATIENT ---
{context_str}

--- PAST CONVERSATION ---
{memory_context if memory_context else "New chat"}

--- SYMPTOM INFO (if available) ---
{symptom_str}

--- USER QUESTION ---
{question}

--- YOUR ONLY RULE ---
Write like you're talking to a patient in your clinic. Be honest but not scary. Make it easy to read.

Just be:
- Calm and reassuring
- Clear about risk level (High/Moderate/Low)
- Specific to THIS patient's condition
- Practical about what to do next

If it's an emergency → say it clearly and tell them to go to ER.
If it's moderate → recommend doctor visit soon.
If it's low → reassure and give home care tips.

Use their name. Keep paragraphs short. Be helpful, not alarming.

Return ONLY your response."""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ RiskAgent error: {e}")
            return "I'm unable to assess your symptoms right now. Please see a doctor if you're concerned."


# Instance
risk_agent = RiskAgent()