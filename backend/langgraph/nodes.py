# backend/langgraph/nodes.py
# 🔥 FAST VERSION - With Smart Response Merging

import json
import copy
import asyncio
import re
from typing import Dict, List, Any
from backend.langgraph.state import AgentState
from backend.core.controller_agent import controller_agent
from backend.core.llm_provider import llm_provider
from agents.guardrail_agent.agent import guardrail_agent
from agents.assistant_agent.agent import assistant_agent
from agents.diet_agent.agent import diet_agent
from agents.drug_agent.agent import drug_agent
from agents.risk_agent.agent import risk_agent
from agents.medical_research_agent.agent import medical_research_agent


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_patient_context(state: Dict) -> Dict:
    ctx = state.get("patient_context", {})
    if isinstance(ctx, str):
        try:
            return json.loads(ctx)
        except:
            return {}
    return ctx


def get_extracted_entities(state: Dict) -> Dict:
    entities = state.get("extracted_entities", {})
    if isinstance(entities, str):
        try:
            return json.loads(entities)
        except:
            return {}
    return entities


def update_state(state: Dict, updates: Dict) -> Dict:
    new_state = dict(state)
    for key, value in updates.items():
        if isinstance(value, (dict, list)):
            new_state[key] = copy.deepcopy(value)
        else:
            new_state[key] = value
    return new_state


# ============================================================
# NODE 0: Extract entities (FAST - no LLM)
# ============================================================
def extract_entities_node(state: AgentState) -> AgentState:
    """Fast extraction using medical_extractor (regex only)"""
    from backend.core.medical_extractor import medical_extractor
    
    try:
        structured_data = medical_extractor.extract(state["question"])
        if not structured_data:
            structured_data = {}
    except Exception as e:
        print(f"⚠️ Extraction warning (non-critical): {e}")
        structured_data = {}
    
    return update_state(state, {"extracted_entities": structured_data})


# ============================================================
# NODE 1: Controller (FAST - rule-based, no LLM)
# ============================================================
def controller_node(state: AgentState) -> AgentState:
    """Rule-based routing - NO LLM CALL"""
    try:
        patient_ctx = get_patient_context(state)
        
        result = controller_agent.plan(
            question=state["question"],
            context=patient_ctx
        )
        
        selected = result.get("agents", [])
        
        valid = {"risk", "drug", "diet", "research", "assistant"}
        selected = [a for a in selected if a in valid]
        
        print(f"🎮 FAST CONTROLLER → {selected}")
        
    except Exception as e:
        print(f"⚠️ Controller error: {e}")
        selected = ["assistant"]
    
    return update_state(state, {"selected_agents": selected})


# ============================================================
# NODE 2: Guardrail (safety critical - keeps LLM)
# ============================================================
def guardrail_node(state: AgentState) -> AgentState:
    """Safety check - keeps LLM for accuracy"""
    try:
        patient_ctx = get_patient_context(state)
        
        guard = guardrail_agent.detect_treatment_decision(
            question=state["question"],
            context=patient_ctx
        )
        
        blocked = guard != "NONE"
        
    except Exception as e:
        print(f"⚠️ Guardrail error: {e}")
        blocked = False
        guard = ""
    
    if blocked:
        return {
            "guardrail_blocked": True,
            "final_response": guard,
            "executed_agents": ["GuardrailAgent"]
        }
    
    return {"guardrail_blocked": False}


# ============================================================
# NODE 3a: Risk Agent (Async)
# ============================================================
async def risk_node_async(state: AgentState) -> str:
    """Async version for parallel execution"""
    try:
        entities = get_extracted_entities(state)
        patient_ctx = get_patient_context(state)
        
        symptoms = entities.get("symptoms", [])
        if isinstance(symptoms, str):
            try:
                symptoms = json.loads(symptoms)
            except:
                symptoms = []
        
        symptom = symptoms[0] if symptoms else state["question"]
        
        response = risk_agent.analyze_symptom(
            question=state["question"],
            symptom=symptom,
            context=patient_ctx,
            memory_context=state.get("conversation_memory", "")
        )
        
        return response if response else "Unable to assess risk at this time."
        
    except Exception as e:
        print(f"⚠️ Risk agent error: {e}")
        return "Unable to assess risk at this time."


# ============================================================
# NODE 3b: Drug Agent (Async)
# ============================================================
async def drug_node_async(state: AgentState) -> str:
    """Async version for parallel execution"""
    try:
        patient_ctx = get_patient_context(state)
        
        drugs = patient_ctx.get("medications", [])
        all_drug_names = []
        for d in drugs:
            if isinstance(d, dict):
                name = d.get('name', '')
                if name:
                    all_drug_names.append(name)
            elif isinstance(d, str):
                all_drug_names.append(d)
        
        question = state["question"].lower()
        drugs_to_fetch = []
        
        name_only_keywords = ["what medicine", "list my med", "which medicine", "name my med", "what am i taking"]
        is_name_only = any(kw in question for kw in name_only_keywords)
        
        if is_name_only:
            drugs_to_fetch = []
        else:
            for drug in all_drug_names:
                if drug.lower() in question:
                    drugs_to_fetch.append(drug)
            
            if not drugs_to_fetch and all_drug_names:
                detail_keywords = ["side effect", "disadvantage", "interaction", "when", "how", "take", "dose"]
                if any(kw in question for kw in detail_keywords):
                    drugs_to_fetch = all_drug_names
        
        response = drug_agent.handle_drug_question(
            context=patient_ctx,
            question=state["question"],
            drugs=drugs_to_fetch,
            memory_context=state.get("conversation_memory", "")
        )
        
        return response if response else "Please consult your pharmacist."
        
    except Exception as e:
        print(f"⚠️ Drug agent error: {e}")
        return "Please consult your pharmacist."


# ============================================================
# NODE 3c: Diet Agent (Async)
# ============================================================
async def diet_node_async(state: AgentState) -> str:
    """Async version for parallel execution"""
    try:
        patient_ctx = get_patient_context(state)
        
        response = diet_agent.handle_diet_question(
            context=patient_ctx,
            question=state["question"],
            memory_context=state.get("conversation_memory", "")
        )
        
        return response if response else "Unable to provide diet advice at this time."
        
    except Exception as e:
        print(f"⚠️ Diet agent error: {e}")
        return "Unable to provide diet advice at this time."


# ============================================================
# NODE 3d: Assistant Agent (Async)
# ============================================================
async def assistant_node_async(state: AgentState) -> str:
    """Async version for parallel execution"""
    try:
        patient_ctx = get_patient_context(state)
        
        response = assistant_agent.handle_question(
            context=patient_ctx,
            question=state["question"],
            memory_context=state.get("conversation_memory", "")
        )
        
        return response if response else "How can I help you today?"
        
    except Exception as e:
        print(f"⚠️ Assistant agent error: {e}")
        return "How can I help you today?"


# ============================================================
# NODE 3e: Research Agent (Async)
# ============================================================
async def research_node_async(state: AgentState) -> str:
    """Async version for parallel execution"""
    try:
        patient_ctx = get_patient_context(state)
        
        response = medical_research_agent.research_medical_question(
            question=state["question"],
            context=patient_ctx,
            memory_context=state.get("conversation_memory", "")
        )
        
        return response if response else "Unable to provide medical information at this time."
        
    except Exception as e:
        print(f"⚠️ Research agent error: {e}")
        return "Unable to provide medical information at this time."


# ============================================================
# ORCHESTRATOR NODE - Runs all selected agents in parallel
# ============================================================
async def orchestrator_node(state: AgentState) -> AgentState:
    """
    🔥 KEY OPTIMIZATION: Run all selected agents in TRUE parallel
    Uses asyncio.gather() for concurrent execution
    """
    if state.get("guardrail_blocked", False):
        return {}
    
    selected_agents = state.get("selected_agents", ["assistant"])
    
    # Map agent names to async functions
    agent_map = {
        "risk": risk_node_async,
        "drug": drug_node_async,
        "diet": diet_node_async,
        "research": research_node_async,
        "assistant": assistant_node_async,
    }
    
    # Build list of tasks for selected agents
    tasks = []
    agent_names = []
    for agent in selected_agents:
        if agent in agent_map:
            tasks.append(agent_map[agent](state))
            agent_names.append(agent)
    
    if not tasks:
        return {"agent_responses": [], "executed_agents": []}
    
    # 🔥 RUN ALL IN PARALLEL
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    responses = []
    executed = []
    for agent_name, result in zip(agent_names, results):
        if isinstance(result, Exception):
            print(f"⚠️ {agent_name} failed: {result}")
            responses.append(f"Unable to get {agent_name} advice at this time.")
        else:
            responses.append(result)
        executed.append(f"{agent_name.capitalize()}Agent")
    
    return {
        "agent_responses": responses,
        "executed_agents": executed
    }


# ============================================================
# NODE 4: Combine responses (SMART MERGE)
# ============================================================
def combine_node(state: AgentState) -> AgentState:
    """Smart combine - merges multiple agent responses into ONE natural response"""
    responses = state.get("agent_responses", [])
    agents = state.get("executed_agents", [])
    
    # Remove duplicates from agents list
    unique_agents = []
    seen = set()
    for agent in agents:
        if agent not in seen:
            seen.add(agent)
            unique_agents.append(agent)
    
    if not responses:
        combined = "I understand. How can I help you with your health today?"
    elif len(responses) == 1:
        combined = responses[0]
    else:
        # Multiple agents - smart merge
        combined = _smart_merge_responses(responses, unique_agents)
    
    return {
        "final_response": combined,
        "executed_agents": unique_agents
    }


def _smart_merge_responses(responses: list, agents: list) -> str:
    """Smart merge multiple responses into ONE natural response"""
    
    if len(responses) == 1:
        return responses[0]
    
    # Clean each response - remove duplicate greetings and redundant info
    cleaned = []
    for idx, resp in enumerate(responses):
        if not resp:
            continue
        
        lines = resp.strip().split('\n')
        filtered = []
        greeting_found = False
        
        for line in lines:
            # Skip duplicate greetings after first one
            if re.match(r'^(Hey|Hello|Hi)\s+\w+[!:]', line.strip()):
                if not greeting_found and idx == 0:
                    filtered.append(line)
                    greeting_found = True
                else:
                    continue  # Skip duplicate greetings
            else:
                # Skip "I'm sorry to hear" if not first response
                if 'sorry to hear' in line.lower() and idx > 0:
                    continue
                filtered.append(line)
        
        cleaned.append('\n'.join(filtered).strip())
    
    if len(cleaned) == 1:
        return cleaned[0]
    
    # Try LLM merge for best results
    try:
        llm = llm_provider.get_chat_llm()
        
        merge_prompt = f"""Merge these TWO responses into ONE natural, flowing response.

RULES:
- Keep ONE greeting only (use patient's name once at the beginning)
- Remove ALL duplicate information
- Create a SINGLE coherent response that flows naturally
- Do NOT show two separate answers
- Do NOT add labels like "Risk Assessment" or "Medication Expert"
- Keep the tone warm and helpful
- Remove any redundant warnings
- Combine similar advice into one paragraph

RESPONSE A:
{cleaned[0]}

RESPONSE B:
{cleaned[1] if len(cleaned) > 1 else ''}

Return ONLY the merged response, nothing else.
Make it sound like ONE expert talking, not two different people.
The response should be 3-4 short paragraphs maximum."""

        merged = llm.invoke(merge_prompt).content.strip()
        
        if len(merged) > 50:
            return merged
            
    except Exception as e:
        print(f"⚠️ Smart merge failed: {e}")
    
    # Fallback: clean simple merge
    if len(cleaned) >= 2:
        # Take first response, remove its greeting if second has one
        first = cleaned[0]
        second = cleaned[1]
        
        # Remove greeting from second response
        second = re.sub(r'^(Hey|Hello|Hi)\s+\w+[!:]', '', second).strip()
        second = re.sub(r'^\n+', '', second)
        
        # Remove first line if it's just a greeting and first already has greeting
        first_lines = first.split('\n')
        if len(first_lines) > 1 and re.match(r'^(Hey|Hello|Hi)', first_lines[0]):
            first = '\n'.join(first_lines[1:]).strip()
        
        return first + "\n\n" + second
    
    return "\n\n".join(cleaned)


# ----------------     WITH REFLECTION (KEPT as requested)     ----------------

# import json
# import copy
# import asyncio
# from typing import Dict, List, Any
# from backend.langgraph.state import AgentState
# from backend.core.controller_agent import controller_agent
# from agents.guardrail_agent.agent import guardrail_agent
# from agents.assistant_agent.agent import assistant_agent
# from agents.diet_agent.agent import diet_agent
# from agents.drug_agent.agent import drug_agent
# from agents.risk_agent.agent import risk_agent
# from agents.medical_research_agent.agent import medical_research_agent
# from agents.reflection_agent.agent import reflection_agent


# # ============================================================
# # HELPER FUNCTIONS
# # ============================================================
# def get_patient_context(state: Dict) -> Dict:
#     ctx = state.get("patient_context", {})
#     if isinstance(ctx, str):
#         try:
#             return json.loads(ctx)
#         except:
#             return {}
#     return ctx


# def get_extracted_entities(state: Dict) -> Dict:
#     entities = state.get("extracted_entities", {})
#     if isinstance(entities, str):
#         try:
#             return json.loads(entities)
#         except:
#             return {}
#     return entities


# def update_state(state: Dict, updates: Dict) -> Dict:
#     new_state = dict(state)
#     for key, value in updates.items():
#         if isinstance(value, (dict, list)):
#             new_state[key] = copy.deepcopy(value)
#         else:
#             new_state[key] = value
#     return new_state


# # ============================================================
# # NODE 0: Extract entities (FAST - no LLM)
# # ============================================================
# def extract_entities_node(state: AgentState) -> AgentState:
#     """Fast extraction using medical_extractor (regex only)"""
#     from backend.core.medical_extractor import medical_extractor
    
#     try:
#         # Medical extractor now uses regex (no LLM)
#         structured_data = medical_extractor.extract(state["question"])
#         if not structured_data:
#             structured_data = {}
#     except Exception as e:
#         print(f"⚠️ Extraction warning (non-critical): {e}")
#         structured_data = {}
    
#     return update_state(state, {"extracted_entities": structured_data})


# # ============================================================
# # NODE 1: Controller (FAST - rule-based, no LLM)
# # ============================================================
# def controller_node(state: AgentState) -> AgentState:
#     """Rule-based routing - NO LLM CALL"""
#     try:
#         patient_ctx = get_patient_context(state)
        
#         # Controller now uses keyword routing (no LLM)
#         result = controller_agent.plan(
#             question=state["question"],
#             context=patient_ctx
#         )
        
#         selected = result.get("agents", [])
        
#         # Validate agent names
#         valid = {"risk", "drug", "diet", "research", "assistant"}
#         selected = [a for a in selected if a in valid]
        
#         print(f"🎮 FAST CONTROLLER → {selected}")
        
#     except Exception as e:
#         print(f"⚠️ Controller error: {e}")
#         selected = ["assistant"]
    
#     return update_state(state, {"selected_agents": selected})


# # ============================================================
# # NODE 2: Guardrail (keeps LLM - safety critical)
# # ============================================================
# def guardrail_node(state: AgentState) -> AgentState:
#     """Safety check - keeps LLM for accuracy"""
#     try:
#         patient_ctx = get_patient_context(state)
        
#         guard = guardrail_agent.detect_treatment_decision(
#             question=state["question"],
#             context=patient_ctx
#         )
        
#         blocked = guard != "NONE"
        
#     except Exception as e:
#         print(f"⚠️ Guardrail error: {e}")
#         blocked = False
#         guard = ""
    
#     if blocked:
#         return {
#             "guardrail_blocked": True,
#             "final_response": guard,
#             "executed_agents": ["GuardrailAgent"]
#         }
    
#     return {"guardrail_blocked": False}


# # ============================================================
# # NODE 3a: Risk Agent (Async)
# # ============================================================
# async def risk_node_async(state: AgentState) -> str:
#     """Async version for parallel execution"""
#     try:
#         entities = get_extracted_entities(state)
#         patient_ctx = get_patient_context(state)
        
#         symptoms = entities.get("symptoms", [])
#         if isinstance(symptoms, str):
#             try:
#                 symptoms = json.loads(symptoms)
#             except:
#                 symptoms = []
        
#         symptom = symptoms[0] if symptoms else state["question"]
        
#         response = risk_agent.analyze_symptom(
#             question=state["question"],
#             symptom=symptom,
#             context=patient_ctx,
#             memory_context=state.get("conversation_memory", "")
#         )
        
#         return response if response else "Unable to assess risk at this time."
        
#     except Exception as e:
#         print(f"⚠️ Risk agent error: {e}")
#         return "Unable to assess risk at this time."


# def risk_node(state: AgentState) -> AgentState:
#     """Sync wrapper - for backward compatibility"""
#     return {"agent_responses": [], "executed_agents": []}  # Handled by orchestrator


# # ============================================================
# # NODE 3b: Drug Agent (Async)
# # ============================================================
# async def drug_node_async(state: AgentState) -> str:
#     """Async version for parallel execution"""
#     try:
#         patient_ctx = get_patient_context(state)
        
#         drugs = patient_ctx.get("medications", [])
#         all_drug_names = []
#         for d in drugs:
#             if isinstance(d, dict):
#                 name = d.get('name', '')
#                 if name:
#                     all_drug_names.append(name)
#             elif isinstance(d, str):
#                 all_drug_names.append(d)
        
#         question = state["question"].lower()
#         drugs_to_fetch = []
        
#         name_only_keywords = ["what medicine", "list my med", "which medicine", "name my med", "what am i taking"]
#         is_name_only = any(kw in question for kw in name_only_keywords)
        
#         if is_name_only:
#             drugs_to_fetch = []
#         else:
#             for drug in all_drug_names:
#                 if drug.lower() in question:
#                     drugs_to_fetch.append(drug)
            
#             if not drugs_to_fetch and all_drug_names:
#                 detail_keywords = ["side effect", "disadvantage", "interaction", "when", "how", "take", "dose"]
#                 if any(kw in question for kw in detail_keywords):
#                     drugs_to_fetch = all_drug_names
        
#         response = drug_agent.handle_drug_question(
#             context=patient_ctx,
#             question=state["question"],
#             drugs=drugs_to_fetch,
#             memory_context=state.get("conversation_memory", "")
#         )
        
#         return response if response else "Please consult your pharmacist."
        
#     except Exception as e:
#         print(f"⚠️ Drug agent error: {e}")
#         return "Please consult your pharmacist."


# def drug_node(state: AgentState) -> AgentState:
#     """Sync wrapper"""
#     return {"agent_responses": [], "executed_agents": []}


# # ============================================================
# # NODE 3c: Diet Agent (Async)
# # ============================================================
# async def diet_node_async(state: AgentState) -> str:
#     """Async version for parallel execution"""
#     try:
#         patient_ctx = get_patient_context(state)
        
#         response = diet_agent.handle_diet_question(
#             context=patient_ctx,
#             question=state["question"],
#             memory_context=state.get("conversation_memory", "")
#         )
        
#         return response if response else "Unable to provide diet advice at this time."
        
#     except Exception as e:
#         print(f"⚠️ Diet agent error: {e}")
#         return "Unable to provide diet advice at this time."


# def diet_node(state: AgentState) -> AgentState:
#     """Sync wrapper"""
#     return {"agent_responses": [], "executed_agents": []}


# # ============================================================
# # NODE 3d: Assistant Agent (Async)
# # ============================================================
# async def assistant_node_async(state: AgentState) -> str:
#     """Async version for parallel execution"""
#     try:
#         patient_ctx = get_patient_context(state)
        
#         response = assistant_agent.handle_question(
#             context=patient_ctx,
#             question=state["question"],
#             memory_context=state.get("conversation_memory", "")
#         )
        
#         return response if response else "How can I help you today?"
        
#     except Exception as e:
#         print(f"⚠️ Assistant agent error: {e}")
#         return "How can I help you today?"


# def assistant_node(state: AgentState) -> AgentState:
#     """Sync wrapper"""
#     return {"agent_responses": [], "executed_agents": []}


# # ============================================================
# # NODE 3e: Research Agent (Async)
# # ============================================================
# async def research_node_async(state: AgentState) -> str:
#     """Async version for parallel execution"""
#     try:
#         patient_ctx = get_patient_context(state)
        
#         response = medical_research_agent.research_medical_question(
#             question=state["question"],
#             context=patient_ctx,
#             memory_context=state.get("conversation_memory", "")
#         )
        
#         return response if response else "Unable to provide medical information at this time."
        
#     except Exception as e:
#         print(f"⚠️ Research agent error: {e}")
#         return "Unable to provide medical information at this time."


# def research_node(state: AgentState) -> AgentState:
#     """Sync wrapper"""
#     return {"agent_responses": [], "executed_agents": []}


# # ============================================================
# # ORCHESTRATOR NODE - Runs all selected agents in parallel
# # ============================================================
# async def orchestrator_node(state: AgentState) -> AgentState:
#     """
#     🔥 KEY OPTIMIZATION: Run all selected agents in TRUE parallel
#     Uses asyncio.gather() for concurrent execution
#     """
#     if state.get("guardrail_blocked", False):
#         return {}
    
#     selected_agents = state.get("selected_agents", ["assistant"])
    
#     # Map agent names to async functions
#     agent_map = {
#         "risk": risk_node_async,
#         "drug": drug_node_async,
#         "diet": diet_node_async,
#         "research": research_node_async,
#         "assistant": assistant_node_async,
#     }
    
#     # Build list of tasks for selected agents
#     tasks = []
#     agent_names = []
#     for agent in selected_agents:
#         if agent in agent_map:
#             tasks.append(agent_map[agent](state))
#             agent_names.append(agent)
    
#     if not tasks:
#         return {"agent_responses": [], "executed_agents": []}
    
#     # 🔥 RUN ALL IN PARALLEL
#     results = await asyncio.gather(*tasks, return_exceptions=True)
    
#     # Process results
#     responses = []
#     executed = []
#     for agent_name, result in zip(agent_names, results):
#         if isinstance(result, Exception):
#             print(f"⚠️ {agent_name} failed: {result}")
#             responses.append(f"Unable to get {agent_name} advice at this time.")
#         else:
#             responses.append(result)
#         executed.append(f"{agent_name.capitalize()}Agent")
    
#     return {
#         "agent_responses": responses,
#         "executed_agents": executed
#     }


# # ============================================================
# # NODE 5: Combine responses
# # ============================================================
# def combine_node(state: AgentState) -> AgentState:
#     """Combine multiple agent responses into one"""
#     responses = state.get("agent_responses", [])
    
#     agents = state.get("executed_agents", [])
#     unique_agents = []
#     seen = set()
#     for agent in agents:
#         if agent not in seen:
#             seen.add(agent)
#             unique_agents.append(agent)
    
#     if not responses:
#         combined = "I understand. How can I help you with your health today?"
#     else:
#         # Simple join - can add formatting here if needed
#         combined = "\n\n".join(responses)
    
#     return {
#         "final_response": combined,
#         "executed_agents": unique_agents
#     }


# # ============================================================
# # NODE 6: Reflection (KEPT as requested)
# # ============================================================
# def reflection_node(state: AgentState) -> AgentState:
#     """Quality check - kept as requested"""
#     final_response = state.get("final_response", "")
    
#     # Skip reflection for very short responses
#     if len(final_response.split()) < 10:
#         return {}
    
#     try:
#         patient_ctx = get_patient_context(state)
        
#         verified = reflection_agent.verify_response(
#             question=state["question"],
#             draft_answer=final_response,
#             context=patient_ctx,
#             memory_context=state.get("conversation_memory", "")
#         )
        
#         if not verified:
#             verified = final_response
            
#     except Exception as e:
#         print(f"⚠️ Reflection error: {e}")
#         verified = final_response
    
#     if verified != final_response:
#         return {"final_response": verified}
    
#     return {}