from backend.core.llm_provider import llm_provider
from tools.drug_interaction_tool import drug_interaction_tool
import json


class DrugAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def handle_drug_question(
        self,
        context: dict,
        question: str,
        drugs: list,
        drug_data: dict = None,
        memory_context: str = "",
    ):
        context = context or {}
        
        # 🔥 FIX: Extract drug names from list (handle both strings and dicts)
        drug_names = []
        if drugs:
            for d in drugs:
                if isinstance(d, str):
                    drug_names.append(d)
                elif isinstance(d, dict):
                    name = d.get('name', '')
                    if name:
                        drug_names.append(name)
        
        # Tool use: Fetch drug info if not provided
        if not drug_data and drug_names:
            print(f"🔍 Fetching drug info for: {drug_names}")
            drug_data = drug_interaction_tool.check_interaction(drug_names)
        
        context_str = json.dumps(context, indent=2, default=str)
        
        drug_info_str = "No drug information available"
        if drug_data:
            drug_info_str = json.dumps(drug_data, indent=2, default=str)

        prompt = f"""You are a friendly, expert pharmacist talking to your patient.

--- PATIENT ---
{context_str}

--- PAST CONVERSATION ---
{memory_context if memory_context else "New chat"}

--- DRUG INFO (if available) ---
{drug_info_str}

--- DRUG NAMES FROM RECORD ---
{drug_names if drug_names else 'No medications found in record'}

--- USER QUESTION ---
{question}

--- YOUR ONLY RULE ---
Write like you're talking to a friend. Make it easy to read. Use line breaks naturally.

Just be:
- Warm and helpful
- Clear and simple
- Personal (use their name)
- Honest about risks (but not scary)

If they ask "what medicine I am taking" → list the drug names from the record above.
If they ask about side effects → explain common ones.
If there's an interaction → explain it clearly.

Return ONLY your response."""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ DrugAgent error: {e}")
            # Fallback: at least give drug names if available
            if drug_names:
                return f"Based on your medical records, you are taking: {', '.join(drug_names)}. Please consult your doctor for detailed information about side effects and interactions."
            return "I'm unable to provide medication advice right now. Please consult your pharmacist or doctor."


# Instance
drug_agent = DrugAgent()