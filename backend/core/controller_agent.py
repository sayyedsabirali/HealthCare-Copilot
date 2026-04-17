# backend/core/controller_agent.py
# 🔥 FAST VERSION - No LLM, pure rule-based routing

class ControllerAgent:
    def __init__(self):
        pass  # No LLM needed

    def _keyword_route(self, question: str) -> list:
        q = question.lower().strip()
        
        # ============================================================
        # FAST PATH: Direct returns (no further checks)
        # ============================================================
        
        # Greetings
        if q in ["hi", "hello", "hey", "hii", "hiii", "namaste", "good morning", "good evening"]:
            return ["assistant"]
        
        # Personal info questions
        if any(w in q for w in ["my name", "who am i", "my age", "how old"]):
            return ["assistant"]
        
        # List medications
        if any(w in q for w in ["what medicine", "list my med", "my medications", "what am i taking"]):
            return ["assistant"]
        
        # ============================================================
        # MULTI-AGENT ROUTING (can trigger multiple)
        # ============================================================
        agents = []
        
        # Risk/Symptom detection (medical urgency)
        risk_keywords = [
            "pain", "ache", "chest", "headache", "dizzy", "fever", 
            "nausea", "vomiting", "breathing", "sweating", "faint",
            "bleeding", "seizure", "unconscious", "heart attack",
            "stroke", "difficulty breathing", "shortness of breath"
        ]
        if any(kw in q for kw in risk_keywords):
            agents.append("risk")
        
        # Drug/Medication questions
        drug_keywords = [
            "side effect", "interaction", "dosage", "dose", 
            "when to take", "how to take", "medicine", "medication",
            "pill", "tablet", "prescription", "overdose"
        ]
        common_drugs = ["metformin", "aspirin", "atorvastatin", "clopidogrel", 
                        "metoprolol", "ramipril", "insulin", "lisinopril"]
        
        if any(kw in q for kw in drug_keywords) or any(drug in q for drug in common_drugs):
            agents.append("drug")
        
        # Diet/Nutrition questions
        diet_keywords = [
            "eat", "food", "meal", "diet", "breakfast", "lunch", "dinner",
            "snack", "nutrition", "calorie", "recipe", "cook", "hungry",
            "thirsty", "water", "drink", "sugar", "salt", "fat", "protein"
        ]
        if any(kw in q for kw in diet_keywords):
            agents.append("diet")
        
        # Research/General medical knowledge
        research_keywords = [
            "what is", "how does", "explain", "difference between",
            "hba1c", "cholesterol", "blood pressure", "diabetes",
            "hypertension", "treatment for", "causes of", "symptoms of"
        ]
        if not agents and any(kw in q for kw in research_keywords):
            agents.append("research")
        
        # ============================================================
        # FALLBACK: Assistant for everything else
        # ============================================================
        if not agents:
            return ["assistant"]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_agents = []
        for a in agents:
            if a not in seen:
                seen.add(a)
                unique_agents.append(a)
        
        print(f"⚡ FAST ROUTING → {unique_agents}")
        return unique_agents

    def plan(self, question: str, context: dict = None) -> dict:
        """Main entry point - NO LLM CALL"""
        agents = self._keyword_route(question)
        return {"agents": agents}


# Singleton instance
controller_agent = ControllerAgent()