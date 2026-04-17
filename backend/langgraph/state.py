from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator


class AgentState(TypedDict, total=False):
    # ==========================================
    # INPUT STATE (Single value - no reducer needed)
    # ==========================================
    patient_id: str
    question: str
    patient_context: Dict[str, Any]
    conversation_memory: str
    
    # ==========================================
    # PROCESSING STATE
    # ==========================================
    extracted_entities: Dict[str, Any]
    selected_agents: List[str]
    
    # 🔥 CRITICAL FIX: Add reducers for parallel updates
    agent_responses: Annotated[List[str], operator.add]
    executed_agents: Annotated[List[str], operator.add]
    
    # Individual agent responses
    risk_response: Optional[str]
    drug_response: Optional[str]
    diet_response: Optional[str]
    research_response: Optional[str]
    assistant_response: Optional[str]
    
    # ==========================================
    # FINAL OUTPUT STATE
    # ==========================================
    final_response: str
    
    # ==========================================
    # SAFETY & GUARDRAILS
    # ==========================================
    guardrail_blocked: bool
    guardrail_reason: Optional[str]
    needs_human_review: bool
    
    # ==========================================
    # METADATA & DEBUGGING
    # ==========================================
    thread_id: Optional[str]
    error: Optional[str]
    retry_count: int