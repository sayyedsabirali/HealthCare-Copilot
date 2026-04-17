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
3. [Core Components](#core-components)
4. [Agents & Tools](#agents--tools)
5. [Skills](#skills)
6. [How it works](#how-it-works)
7. [Data Model](#data-model)
8. [Environment Variables](#environment-variables)

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

PatientCare Copilot is a patient-aware AI assistant that uses uploaded medical records and MongoDB patient profiles to deliver context-aware health answers. The browser UI is simple; the main value is the backend reasoning engine and multi-agent workflow.

---

## Core Components

- `backend/langgraph/` — routes questions through the workflow and specialist agents.
- `backend/core/` — extracts medical context and builds patient-aware prompts.
- `agents/` — specialist modules for diet, drugs, risk, research, and general assistance.
- `tools/` — data lookups and external knowledge sources.
- `database/` — MongoDB persistence for patients, uploads, and medical text.
- `memory/` — stores conversational memory and summaries.

---

## Agents & Tools

- `DietAgent` — nutrition and meal guidance based on patient history.
- `DrugAgent` — medication questions, interactions, and side effect checks.
- `RiskAgent` — symptom risk assessment and triage recommendations.
- `MedicalResearchAgent` — evidence-based clinical knowledge and guideline lookup.
- `AssistantAgent` — fallback health advice and general consumer response.
- `GuardrailAgent` — safety checks for treatment-change or prescription requests.

- `tools/nutrition_tool.py` — USDA food and nutrition lookup.
- `tools/drug_interaction_tool.py` — medication label and interaction lookup.
- `tools/symptom_checker_tool.py` — symptom-to-condition search.
- `tools/medical_guideline_tool.py` — guideline and clinical topic lookup.

---

## Skills Demonstrated

- Generative AI
- LangGraph
- MongoDB
- Prompt engineering
- Context building
- Medical entity extraction
- Multi-agent orchestration
- Tool integration
- Safety guardrails
- Conversational memory

---

## How it works

1. Patient data and medical uploads are stored in MongoDB.
2. A question is analyzed for clinical entities and intent.
3. The controller selects the right agents.
4. Guardrails block unsafe treatment requests.
5. Selected agents run in parallel and return their findings.
6. The system combines those findings into one clear answer.

---

## Data Model

- `users` stores authentication and patient links.
- `patients` stores patient profiles, medications, notes, and care details.
- `medical_texts` stores uploaded documents and extracted facts.
- `medical_reports` stores parsed report metadata.
- `medical_images` stores OCR-extracted text from images.

---

## Environment Variables

Required:

- `MONGO_URI`
- `DATABASE_NAME`
- `OPENAI_API_KEY`

Optional:

- `USDA_API_KEY`
- `ANTHROPIC_API_KEY`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_ENDPOINT`
- `LANGSMITH_TRACING`
- `LLM_PROVIDER`

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
