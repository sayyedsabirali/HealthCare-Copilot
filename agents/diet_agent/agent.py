from backend.core.llm_provider import llm_provider
from tools.nutrition_tool import nutrition_tool
import json


class DietAgent:
    def __init__(self):
        self.llm = llm_provider.get_chat_llm()

    def handle_diet_question(
        self,
        context: dict,
        question: str,
        memory_context: str = "",
    ):
        context = context or {}
        
        # Tool use
        food = self._extract_food(question)
        nutrition_info = None
        if food:
            print(f"🔍 Fetching nutrition for: {food}")
            nutrition_info = nutrition_tool.get_food_nutrition(food)
        
        context_str = json.dumps(context, indent=2, default=str)
        nutrition_str = json.dumps(nutrition_info, indent=2, default=str) if nutrition_info else "Not available"

        prompt = f"""You are a warm, expert dietitian talking to your patient.

--- PATIENT ---
{context_str}

--- PAST CONVERSATION ---
{memory_context if memory_context else "New chat"}

--- NUTRITION INFO (if available) ---
{nutrition_str}

--- USER QUESTION ---
{question}

--- YOUR ONLY RULE ---
Write like you're talking to a friend. Make it easy to read. Use line breaks naturally.

That's it. No templates. No forced format.

Just be:
- Warm and helpful
- Clear and simple
- Personal (use their name)
- Practical (real foods they can eat)

If listing things → use bullet points or numbers naturally.
If giving a warning → make it clear.
If answering yes/no → say it first.

Don't write huge blocks of text. Keep paragraphs short.

Return ONLY your response."""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"❌ DietAgent error: {e}")
            return "I'm unable to provide diet advice right now. Please consult a dietitian."
    
    def _extract_food(self, question: str) -> str | None:
        prompt = f"""Extract the primary food name from this question. 
Return ONLY the food name in singular form, or NONE.

Question: {question}"""
        try:
            food = self.llm.invoke(prompt).content.strip().lower()
            if food in ("none", "", "n/a"):
                return None
            return food
        except Exception:
            return None


# Instance
diet_agent = DietAgent()