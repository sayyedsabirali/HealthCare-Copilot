# backend/core/context_builder.py

from database.patient_repository import patient_repository
from database.mongo_client import db
from datetime import datetime
import json
import re

medical_texts = db["medical_texts"]


# ─────────────────────────────────────────────────────────────
# SAFE PARSER
# ─────────────────────────────────────────────────────────────
def _parse_structured(raw) -> dict:
    if not raw:
        return {}

    if isinstance(raw, dict):
        if "raw_output" not in raw:
            return raw
        raw = raw["raw_output"]

    raw = re.sub(r"```(?:json)?", "", str(raw)).replace("```", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────
# MERGE ENGINE
# ─────────────────────────────────────────────────────────────
def _merge_structured_into_context(context: dict, sd: dict) -> dict:

    PRIORITY_FIELDS = [
        "symptoms",
        "summary",
        "recovery_status",
        "follow_up",
        "vitals",
        "lab_results"
    ]

    def normalize_item(item):
        if isinstance(item, dict):
            return json.dumps(item, sort_keys=True)
        return str(item)

    def normalize_med(m):
        if isinstance(m, dict):
            return m.get("name", "").lower()
        return str(m).lower()

    def merge_lists(existing, new, key=None):
        if key == "medications":
            existing_set = set(normalize_med(x) for x in existing)
            for item in new:
                med_key = normalize_med(item)
                if med_key not in existing_set:
                    existing.append(item)
                    existing_set.add(med_key)
        else:
            existing_set = set(normalize_item(x) for x in existing)
            for item in new:
                k = normalize_item(item)
                if k not in existing_set:
                    existing.append(item)
                    existing_set.add(k)
        return existing

    def merge_dicts(d1, d2):
        for k, v in d2.items():
            if isinstance(v, dict) and isinstance(d1.get(k), dict):
                d1[k] = merge_dicts(d1[k], v)
            elif v:
                d1[k] = v
        return d1

    for key, value in sd.items():

        if not value:
            continue

        if key in PRIORITY_FIELDS:
            context[key] = value
            continue

        if key not in context:
            context[key] = value
            continue

        if isinstance(context[key], dict) and isinstance(value, dict):
            context[key] = merge_dicts(context[key], value)
            continue

        if isinstance(context[key], list):
            if isinstance(value, list):
                context[key] = merge_lists(context[key], value, key)
            else:
                context[key] = merge_lists(context[key], [value], key)
            continue

        if key in ["follow_up", "summary"]:
            context[key] = value
        elif context[key] in [None, "", [], {}]:
            context[key] = value

    return context


# ─────────────────────────────────────────────────────────────
# CONTEXT BUILDER
# ─────────────────────────────────────────────────────────────
class ContextBuilder:

    def build_patient_context(self, patient_id: str, memory: str = None) -> dict:

        context = {
            "patient_info": {
                "name": None,
                "age": None,
                "gender": None,
                "history": []
            },

            "chief_complaints": [],
            "symptoms": [],
            "diagnosis": [],
            "risk_factors": [],
            "procedures": [],
            "hospital_course": [],
            "emergency_signs": [],

            "vitals": {},
            "lab_results": {},

            "medications": [],

            "doctor_instructions": [],
            "diet_recommendations": [],
            "activity_restrictions": [],

            "follow_up": "",
            "summary": None,

            "timeline": {},
            "recovery_status": None,

            "context_version": "v2",
            "last_updated": datetime.utcnow().isoformat()
        }

        # ── Load base patient data ──
        patient = patient_repository.get_patient(patient_id)

        if patient:
            pi = patient.get("patient_info", {})

            context["patient_info"]["name"] = pi.get("name")
            context["patient_info"]["age"] = pi.get("age")
            context["patient_info"]["gender"] = pi.get("gender")
            context["patient_info"]["history"] = pi.get("history", [])

            context["diagnosis"] = patient.get("diagnosis", [])
            context["medications"] = patient.get("medications", [])
            context["diet_recommendations"] = patient.get("diet_recommendations", [])
            context["activity_restrictions"] = patient.get("activity_restrictions", [])
            context["doctor_instructions"] = patient.get("doctor_instructions", [])
            context["symptoms"] = patient.get("symptoms", [])
            context["chief_complaints"] = patient.get("chief_complaints", [])  # ✅ ADD

        # ── Enrich from recent documents ──
        recent_texts = list(
            medical_texts
            .find({"patient_id": patient_id})
            .sort("created_at", -1)
            .limit(5)
        )

        for i, doc in enumerate(recent_texts):
            structured_data = _parse_structured(doc.get("structured_data", {}))

            if not structured_data:
                continue

            structured_data["_recency_rank"] = i   # ✅ ADD

            if i == 0:
                structured_data["priority"] = "latest"

            context = _merge_structured_into_context(context, structured_data)

        # ── Inject MEMORY (🔥 KEY FIX) ──
        if memory:
            context["conversation_memory"] = memory

        # ── Auto summary ──
        if not context.get("summary"):
            diagnosis = ", ".join(context["diagnosis"]) if context["diagnosis"] else "no major conditions"
            symptoms = ", ".join(context["symptoms"]) if context["symptoms"] else "no active symptoms"

            context["summary"] = f"Patient with {diagnosis}, currently experiencing {symptoms}."

        print("✅ FINAL PATIENT CONTEXT:", context)

        return context


# ─────────────────────────────────────────────────────────────
# INSTANCE
# ─────────────────────────────────────────────────────────────
context_builder = ContextBuilder()