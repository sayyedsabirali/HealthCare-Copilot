from fastapi import APIRouter, Depends
from pydantic import BaseModel

from memory.chat_memory import chat_memory
from backend.auth.auth_dependency import get_current_user
from backend.core.agent_executor import run_agentic_flow  # This now imports LangGraph version
from backend.core.context_builder import context_builder

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    debug: bool = False


# ✅ Changed 'def' to 'async def'
@router.post("/chat")
async def chat(request: ChatRequest, user=Depends(get_current_user)):

    patient_id = user["patient_id"]
    question   = request.question.strip()

    # ❌ Prevent empty queries (IMPORTANT)
    if not question:
        return {"response": "Please enter a valid question.", "agents": []}

    # ✅ Save user message
    chat_memory.save_user_message(patient_id, question)

    # ✅ Build memory context
    memory_context = chat_memory.build_memory_context(patient_id)

    print("===== CHAT MEMORY CONTEXT =====")
    print(memory_context)

    # ✅ Build patient context (WITH MEMORY 🔥)
    patient_context = context_builder.build_patient_context(
        patient_id,
        memory=memory_context
    )

    print("===== PATIENT CONTEXT =====")
    print(patient_context)

    try:
        # ✅ Run agent pipeline (ADDED 'await')
        result = await run_agentic_flow(
            patient_id=patient_id,
            question=question,
            context=patient_context,
            memory_context=memory_context
        )

        response = result.get("response", "") if isinstance(result, dict) else str(result)
        agents   = result.get("agents", [])   if isinstance(result, dict) else []

    except Exception as e:
        print("❌ AGENT EXECUTION ERROR:", e)
        response = "Something went wrong while processing your request. Please try again."
        agents = []

    # ✅ Save AI response
    chat_memory.save_ai_message(patient_id, response)

    # ✅ Debug mode
    if request.debug:
        return {
            "response": response,
            "agents": agents,
            "patient_context": patient_context,
            "memory_context": memory_context
        }

    return {
        "response": response,
        "agents": agents
    }