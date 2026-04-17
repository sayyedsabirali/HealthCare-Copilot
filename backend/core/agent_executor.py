from backend.langgraph.workflow import run_agent_graph


async def run_agentic_flow(
    patient_id: str,
    question: str,
    context: dict = None,
    memory_context: str = ""
) -> dict:
    context = context or {}
    
    result = await run_agent_graph(
        patient_id=patient_id,
        question=question,
        patient_context=context,
        conversation_memory=memory_context
    )
    
    return result