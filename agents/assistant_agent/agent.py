from backend.core.llm_provider import llm_provider
import json


class AssistantAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def handle_question(
        self,
        context: dict,
        question: str,
        memory_context: str = "",
    ):
        context = context or {}
        q = question.lower().strip()
        
        # 🔥 Only hardcoded part - greetings
        if len(q) < 15 and any(g in q for g in ["hi", "hello", "hey", "hii", "namaste", "good morning"]):
            return "Hello! 👋 How can I help you with your health today?"  # ✅ Single response
        
        # Rest of the code...
        prompt = f"""Answer this question naturally using the patient data.

Patient: {context.get('patient_info', {}).get('name', 'Unknown')}
Age: {context.get('patient_info', {}).get('age', 'Unknown')}
Medical history: {context.get('diagnosis', [])}
Medications: {[m.get('name') for m in context.get('medications', []) if m.get('name')]}

Question: {question}

Be helpful, warm, and short (2-3 sentences). Use the patient's name if available.

Return ONLY your response."""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ AssistantAgent error: {e}")
            return "How can I help you today?"


assistant_agent = AssistantAgent()