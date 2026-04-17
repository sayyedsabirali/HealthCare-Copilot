from backend.core.llm_provider import llm_provider
from tools.medical_guideline_tool import medical_guideline_tool
import json


class MedicalResearchAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def research_medical_question(
        self,
        question: str,
        context: dict = None,
        memory_context: str = "",
    ) -> str:
        context = context or {}
        
        # 🔥 TOOL USE: Get medical guidelines
        print(f"🔍 Researching: {question}")
        guideline_data = medical_guideline_tool.search_medical_guidelines(question)
        
        context_str = json.dumps(context, indent=2, default=str)
        guideline_str = json.dumps(guideline_data, indent=2, default=str) if guideline_data else "Use your medical knowledge"

        prompt = f"""You are an expert medical research assistant.

--- PATIENT CONTEXT ---
{context_str}

--- CONVERSATION MEMORY ---
{memory_context if memory_context else "None"}

--- MEDICAL GUIDELINES (FROM MEDLINE/PUBMED) ---
{guideline_str}

--- USER QUESTION ---
{question}

--- INSTRUCTIONS ---
1. USE THE GUIDELINE DATA ABOVE if available
2. Provide information relevant to THIS patient
3. Reference medical sources when possible

--- OUTPUT STYLE ---
- Conversational, like a doctor explaining to a patient
- 70-130 words
- Clear and simple

Return ONLY the response.
"""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ MedicalResearchAgent error: {e}")
            return "I'm unable to provide medical information right now. Please consult your doctor."


# Instance
medical_research_agent = MedicalResearchAgent()