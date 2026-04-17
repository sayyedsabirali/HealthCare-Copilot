# PatientCare Copilot

PatientCare Copilot is a personalized health AI assistant built to understand each patient from their own medical data. Users can register, upload clinical files such as discharge summaries and medical notes, and the system stores that data in MongoDB. When a patient asks a question, the engine answers using the patient's profile, upload history, and conversation memory.

This repo is centered on a backend-first AI engine, not just a frontend demo. It includes:

- A core AI engine in `backend/langgraph/` that routes questions through specialized health agents.
- `backend/core/` modules for patient context building, medical entity extraction, reasoning, and LLM orchestration.
- MongoDB-backed patient profiles, document uploads, and structured medical history.
- `memory/` for chat memory, summaries, and personalized conversational context.
- A simple browser frontend in `index.html` and an optional Streamlit entrypoint in `frontend.py` for accessing the backend.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [What is this project?](#what-is-this-project)
3. [Main Components](#main-components)
4. [Why this project exists](#why-this-project-exists)
5. [Workflow (what happens)](#workflow-what-happens)
6. [How it works](#how-it-works)
7. [Backend and UI](#backend-and-ui)
8. [Frontend Usage](#frontend-usage)
9. [Agent list](#agent-list)
10. [Key files you should care about](#key-files-you-should-care-about)
11. [In short](#in-short)
12. [Agent Pipeline](#agent-pipeline)

---

## Getting Started

### 1. Create a Python environment

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

Create a `.env` file at the repo root and provide the required variables (see [Environment Variables](#environment-variables)).

### 4. Start MongoDB

Ensure MongoDB is running and reachable from the value you set for `MONGO_URI`.

### 5. Start the backend

```bash
uvicorn backend.main:app --reload
```

### 6. Open the browser UI

Open `index.html` in your browser and use the app UI. The frontend expects the backend at `http://localhost:8000` by default.

---

## What is this project?

PatientCare Copilot is more than a simple web UI or generic chatbot. It is a patient-aware AI reasoning system that:

- lets users register and upload medical records, discharge summaries, and clinical notes,
- stores and retrieves patient data from MongoDB,
- builds a personalized medical context for each patient,
- routes questions to the right specialist agents,
- combines multiple expert responses into one safe and coherent answer.

The browser UI is a lightweight access layer. The main value is the backend engine that answers health questions using patient-specific data and multi-agent reasoning.

---

## Main Components

- `backend/langgraph/` — the workflow engine that controls the agent execution.
- `backend/core/` — the logic for extracting medical facts, building patient context, and calling LLMs.
- `agents/` — specialized health agents for diet, drugs, risk, research, and general assistance.
- `tools/` — external data integrations used by agents.
- `database/` — MongoDB persistence for patients and document history.
- `memory/` — chat memory and summarization for conversational context.

---

## Skills

- Generative AI
- LangGraph orchestration
- LangSmith tracing
- Patient-aware context
- Medical entity extraction
- Multi-agent reasoning
- Parallel execution
- Tool augmentation

---

## Why this project exists

Because real health questions need more than one answer source.
This system is designed to:

- understand the patient,
- extract medical context,
- choose the right specialist agent(s),
- and return a safe, combined response.

It is meant to be a smart backend engine for health-related chat and document reasoning.

---

## Workflow (what happens)

The heart of the project is the LangGraph workflow. It runs in this order:

1. `extract` — extract clinical entities from the question.
2. `controller` — decide which agents should answer.
3. `guardrail` — check for unsafe or treatment-change requests.
4. `orchestrator` — run the selected agents in parallel.
5. `combine` — merge agent outputs into one final response.

This is the printed workflow the app uses.

---

## How it works

1. A user asks a health question.
2. The system loads patient context from MongoDB.
3. It adds recent chat memory and uploaded medical text.
4. LangGraph runs the workflow above.
5. Agents may call external tools and then answer.
6. The system merges agent answers and returns a single result.

---

## Backend and UI

The backend is a FastAPI service, and `index.html` is a simple browser interface. They are only the entry points.

The main value is the AI reasoning engine in:

- `backend/langgraph/`
- `backend/core/`
- `agents/`
- `tools/`

The frontend/API are just how you send questions into the workflow and get answers back.

---

## Frontend Usage

The repository includes a minimal browser SPA in `index.html` and an optional Streamlit interface in `frontend.py`. These are meant to provide simple access to the core AI engine, but they are not the main focus of the project.

- `index.html` is configured to call `http://localhost:8000` by default. Update the `BASE` constant if your backend runs elsewhere.
- `frontend.py` is optional and can be launched with `streamlit run frontend.py`.

The primary product is the LangGraph/agent/tool core, not the UI.

---

## Agent Pipeline

This is the main functional layer of the project.

### Workflow Nodes

1. `extract_entities_node`
   - Uses `backend.core.medical_extractor` to parse the incoming question and extract medical entities, symptoms, and medications.
   - Keeps the extraction fast and deterministic by relying on regex matching instead of expensive LLM calls.

2. `controller_node`
   - Runs a rule-based planner in `backend.core.controller_agent`.
   - Routes questions to one or more specialist agents based on medical keywords and intent patterns.
   - Supports multi-agent execution when queries span symptoms, drugs, diet, and clinical knowledge.

3. `guardrail_node`
   - Uses `agents.guardrail_agent.agent.GuardrailAgent` to detect unsafe requests such as medication changes, dose adjustments, or treatment decisions.
   - If a query is blocked, the workflow stops early and returns a safety warning instead of consulting the other agents.

4. `orchestrator_node`
   - Executes selected agents in parallel using `asyncio.gather()`.
   - This accelerates multi-agent queries by running risk, drug, diet, research, and assistant logic simultaneously.
   - The node collects responses and executed agent labels.

5. `combine_node`
   - Merges multiple agent outputs into a single natural-language response.
   - Uses a smart LLM merge prompt when there are two or more responses.
   - Deduplicates greetings and redundant text so the final answer feels like one expert.

### Agent Specializations

- `AssistantAgent` — general-purpose health assistant and fallback responder.
- `DietAgent` — nutrition coaching and meal guidance, enriched by USDA nutrition tool data.
- `DrugAgent` — medication questions, side effects, and interactions, enriched by FDA drug label tool data.
- `RiskAgent` — symptom risk assessment and triage guidance, enriched by NLM symptom lookup.
- `MedicalResearchAgent` — evidence-based medical knowledge using MedlinePlus/PubMed guideline searches.
- `GuardrailAgent` — safety enforcement for medication/treatment change requests.

### Tool Integrations

Each agent may consult an external tool before generating a response:

- `tools/nutrition_tool.py` — USDA food nutrition search.
- `tools/drug_interaction_tool.py` — FDA drug label lookup.
- `tools/symptom_checker_tool.py` — symptom-to-condition search.
- `tools/medical_guideline_tool.py` — guideline and PubMed topic lookups.

If tool data is available, the agent includes it in the LLM prompt to improve accuracy and relevance.

### Core Context Building

The AI engine uses `backend/core/context_builder.py` to assemble:

- patient profile fields from MongoDB,
- recent structured clinical facts from uploaded documents,
- an auto-generated summary when explicit summary data is missing,
- and current conversation memory from `memory/chat_memory.py`.

This context is passed into agent prompts to make responses patient-specific and clinically grounded.

---

## Data Model and Storage

### MongoDB Collections

- `users`
  - Stores auth records with `email`, hashed `password`, and `patient_id`.

- `patients`
  - Stores patient profile data, clinical fields, medications, diet recommendations, doctor instructions, and timestamps.

- `medical_texts`
  - Stores extracted structured data and original raw text from text uploads.

- `medical_reports`
  - Stores parsed PDF report metadata, extracted text, and structured metadata.

- `medical_images`
  - Stores OCR-extracted image text and structured metadata.

### Patient Profile Flow

- Uploads and text extraction results are synced into `patients` via `backend/api/upload.py`.
- `backend/core/context_builder.py` merges patient data, uploaded document summaries, and chat memory into a single context for AI reasoning.
- The `patient_id` stored in the JWT ties every request to one patient record.

---

## Agent Pipeline

### Purpose

The system uses a specialist agent architecture so each query is routed to the best medical reasoning module.

### Workflow Steps

1. `extract_entities_node`
   - Uses `backend.core.medical_extractor` to extract symptoms, medications, and patient info from text.

2. `controller_node`
   - Uses `backend.core.controller_agent` keyword routing to select one or more agents.
   - Agents include `risk`, `drug`, `diet`, `research`, or `assistant`.

3. `guardrail_node`
   - Uses `agents.guardrail_agent` to detect unsafe treatment or prescription decisions.
   - If blocked, the workflow ends with a safety response.

4. `orchestrator_node`
   - Runs selected agents in parallel using `asyncio.gather()`.
   - This improves response performance for multi-agent queries.

5. `combine_node`
   - Merges one or more agent outputs into a single natural-language response.
   - Uses a smart merge prompt via LLM if multiple responses arrive.

### Agent Types

- `assistant_agent` — general health conversation and fallback responses.
- `diet_agent` — nutrition and meal guidance.
- `drug_agent` — medication questions, interactions, and side effects.
- `risk_agent` — symptom urgency and risk assessment.
- `medical_research_agent` — medical explanation and clinical knowledge.
- `guardrail_agent` — safety enforcement for risky or medical decision queries.

---

## Environment Variables

The app uses `pydantic-settings` to load `.env` values.

Required variables:

- `MONGO_URI` — MongoDB connection string.
- `DATABASE_NAME` — database name.
- `USDA_API_KEY` — configured but not currently enforced in code.
- `OPENAI_API_KEY` — required if `LLM_PROVIDER=openai`.

Optional variables:

- `ANTHROPIC_API_KEY` — if `LLM_PROVIDER=anthropic`.
- `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`, `LANGSMITH_TRACING`
- `LLM_PROVIDER` — default is `openai`.

Example `.env`:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=ai_health_copilot
OPENAI_API_KEY=sk-xxxx
USDA_API_KEY=your-usda-key
LLM_PROVIDER=openai
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=patientcare-copilot
```
