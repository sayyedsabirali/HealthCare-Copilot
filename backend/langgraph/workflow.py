# backend/langgraph/workflow.py
# 🔥 FASTEST VERSION - No reflection node

from langgraph.graph import StateGraph, END
from backend.langgraph.state import AgentState
from backend.langgraph.nodes import (
    extract_entities_node,
    controller_node,
    guardrail_node,
    orchestrator_node,
    combine_node
)


def build_fastest_graph():
    """
    FASTEST graph (no reflection):
    Extract → Controller → Guardrail → Orchestrator (parallel) → Combine → END
    """
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("extract", extract_entities_node)
    workflow.add_node("controller", controller_node)
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("combine", combine_node)
    
    # Set entry point
    workflow.set_entry_point("extract")
    
    # Sequential edges
    workflow.add_edge("extract", "controller")
    workflow.add_edge("controller", "guardrail")
    
    # After guardrail, either END or orchestrator
    def after_guardrail(state: AgentState):
        if state.get("guardrail_blocked", False):
            return END
        return "orchestrator"
    
    workflow.add_conditional_edges(
        "guardrail",
        after_guardrail,
        {END: END, "orchestrator": "orchestrator"}
    )
    
    # Orchestrator → Combine → END
    workflow.add_edge("orchestrator", "combine")
    workflow.add_edge("combine", END)
    
    return workflow


def get_agent_graph():
    """Returns compiled graph"""
    workflow = build_fastest_graph()
    return workflow.compile()


async def run_agent_graph(
    patient_id: str,
    question: str,
    patient_context: dict,
    conversation_memory: str,
    thread_id: str = None
) -> dict:
    """
    Main entry point for running the agent graph
    """
    graph = get_agent_graph()
    
    initial_state = {
        "patient_id": patient_id,
        "question": question,
        "patient_context": patient_context or {},
        "conversation_memory": conversation_memory or "",
        "extracted_entities": {},
        "selected_agents": [],
        "agent_responses": [],
        "executed_agents": [],
        "final_response": "",
        "guardrail_blocked": False,
        "needs_human_review": False,
        "retry_count": 0
    }
    
    final_state = await graph.ainvoke(initial_state)
    
    # Remove duplicate agents
    agents = final_state.get("executed_agents", [])
    unique_agents = []
    seen = set()
    for agent in agents:
        if agent not in seen:
            seen.add(agent)
            unique_agents.append(agent)
    
    return {
        "response": final_state.get("final_response", "Unable to generate response."),
        "agents": unique_agents,
        "guardrail_blocked": final_state.get("guardrail_blocked", False)
    }


# OLD VERSION WITH REFLECTION - SLOWEST

# from langgraph.graph import StateGraph, END
# from backend.langgraph.state import AgentState
# from backend.langgraph.nodes import (
#     extract_entities_node,
#     controller_node,
#     guardrail_node,
#     orchestrator_node,  # NEW - runs agents in parallel
#     combine_node,
#     reflection_node
# )


# def build_fast_graph():
#     """
#     FAST optimized graph:
#     - Extract → Controller → Guardrail → Orchestrator (parallel) → Combine → Reflection → END
#     """
#     workflow = StateGraph(AgentState)
    
#     # Add all nodes
#     workflow.add_node("extract", extract_entities_node)
#     workflow.add_node("controller", controller_node)
#     workflow.add_node("guardrail", guardrail_node)
#     workflow.add_node("orchestrator", orchestrator_node)  # 🔥 KEY: Parallel execution
#     workflow.add_node("combine", combine_node)
#     workflow.add_node("reflection", reflection_node)
    
#     # Set entry point
#     workflow.set_entry_point("extract")
    
#     # Sequential edges
#     workflow.add_edge("extract", "controller")
#     workflow.add_edge("controller", "guardrail")
    
#     # After guardrail, either END or orchestrator
#     def after_guardrail(state: AgentState):
#         if state.get("guardrail_blocked", False):
#             return END
#         return "orchestrator"
    
#     workflow.add_conditional_edges(
#         "guardrail",
#         after_guardrail,
#         {END: END, "orchestrator": "orchestrator"}
#     )
    
#     # Orchestrator → Combine → Reflection → END
#     workflow.add_edge("orchestrator", "combine")
#     workflow.add_edge("combine", "reflection")
#     workflow.add_edge("reflection", END)
    
#     return workflow


# def get_agent_graph():
#     """Returns compiled graph"""
#     workflow = build_fast_graph()
#     return workflow.compile()


# async def run_agent_graph(
#     patient_id: str,
#     question: str,
#     patient_context: dict,
#     conversation_memory: str,
#     thread_id: str = None
# ) -> dict:
#     """
#     Main entry point for running the agent graph
#     """
#     graph = get_agent_graph()
    
#     initial_state = {
#         "patient_id": patient_id,
#         "question": question,
#         "patient_context": patient_context or {},
#         "conversation_memory": conversation_memory or "",
#         "extracted_entities": {},
#         "selected_agents": [],
#         "agent_responses": [],
#         "executed_agents": [],
#         "final_response": "",
#         "guardrail_blocked": False,
#         "needs_human_review": False,
#         "retry_count": 0
#     }
    
#     final_state = await graph.ainvoke(initial_state)
    
#     # Remove duplicate agents
#     agents = final_state.get("executed_agents", [])
#     unique_agents = []
#     seen = set()
#     for agent in agents:
#         if agent not in seen:
#             seen.add(agent)
#             unique_agents.append(agent)
    
#     return {
#         "response": final_state.get("final_response", "Unable to generate response."),
#         "agents": unique_agents,
#         "guardrail_blocked": final_state.get("guardrail_blocked", False)
#     }