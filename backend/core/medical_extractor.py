# # backend/core/medical_extractor.py

# from backend.core.llm_provider import llm_provider
# import json
# import re


# class MedicalExtractor:

#     def __init__(self):
#         self.llm = llm_provider.get_chat_llm()

#     # ── Rule-based extraction (critical fields) ─────────────────────────────
#     def extract_patient_info(self, text: str):
#         info = {}

#         name   = re.search(r"Patient\s*Name[:\-]?\s*(.+)",           text, re.IGNORECASE)
#         age    = re.search(r"\b(\d{1,3})[\s-]*year[\s-]*old",        text, re.IGNORECASE)
#         age2   = re.search(r"Age[:\-]?\s*(\d+)",                     text, re.IGNORECASE)
#         gender = re.search(r"\b(Male|Female|Other)\b",               text, re.IGNORECASE)
#         gender2= re.search(r"Gender[:\-]?\s*(Male|Female|Other)",    text, re.IGNORECASE)

#         if name:
#             info["name"] = name.group(1).strip()
#         if age:
#             info["age"] = int(age.group(1))
#         elif age2:
#             info["age"] = int(age2.group(1))
#         if gender2:
#             info["gender"] = gender2.group(1).capitalize()
#         elif gender:
#             info["gender"] = gender.group(1).capitalize()

#         return info

#     # ── Merge rule-based patient_info with LLM patient_info ─────────────────
#     def merge_patient_info(self, llm_info: dict, rule_info: dict) -> dict:
#         merged = dict(llm_info) if llm_info else {}
#         # Rule-based values win for name/age/gender (more reliable for structured fields)
#         for key in ("name", "age", "gender"):
#             if rule_info.get(key):
#                 merged[key] = rule_info[key]
#         return merged

#     # ── Normalize output to a single consistent UI schema ───────────────────
#     def normalize(self, data: dict, patient_info: dict = None) -> dict:
#         """
#         Accepts the raw LLM dict + optional rule-based patient_info override.
#         Returns a flat dict that the frontend and upload router both consume.
#         All field names are canonical here — upload.py must NOT re-map them.
#         """
#         pi = data.get("patient_info") or {}
#         if patient_info:
#             pi = self.merge_patient_info(pi, patient_info)

#         # Medications — normalise each item to {name, dose, frequency, duration, purpose}
#         raw_meds = data.get("medications") or []
#         medications = []
#         for m in raw_meds:
#             if isinstance(m, dict):
#                 medications.append({
#                     "name":      m.get("name", ""),
#                     "dose":      m.get("dose") or m.get("dosage") or m.get("amount") or "",
#                     "frequency": m.get("frequency") or m.get("freq") or "",
#                     "duration":  m.get("duration") or "",
#                     "purpose":   m.get("purpose") or m.get("indication") or "",
#                 })
#             elif isinstance(m, str):
#                 medications.append({"name": m, "dose": "", "frequency": "", "duration": "", "purpose": ""})

#         return {
#             # ── Patient ──────────────────────────────────────────────────────
#             "patient_info": {
#                 "name":    pi.get("name", ""),
#                 "age":     pi.get("age"),
#                 "gender":  pi.get("gender", ""),
#                 "history": pi.get("history") or [],
#             },

#             # ── Clinical ─────────────────────────────────────────────────────
#             "chief_complaints":      _to_list(data.get("chief_complaints")),
#             "symptoms":              _to_list(data.get("symptoms")),
#             "diagnosis":             _to_list(data.get("diagnosis") or data.get("medical_conditions")),
#             "risk_factors":          _to_list(data.get("risk_factors")),
#             "procedures":            _to_list(data.get("procedures")),
#             "hospital_course":       _to_list(data.get("hospital_course")),
#             "emergency_signs":       _to_list(data.get("emergency_signs")),

#             # ── Vitals / Labs ─────────────────────────────────────────────────
#             "vitals": data.get("vitals") or {},
#             "lab_results": data.get("lab_results") or {},

#             # ── Medications ───────────────────────────────────────────────────
#             "medications": medications,

#             # ── Post-discharge instructions ───────────────────────────────────
#             "doctor_instructions":   _to_list(data.get("doctor_instructions")),
#             # canonical name: diet_recommendations  (frontend + upload both use this)
#             "diet_recommendations":  _to_list(
#                 data.get("diet_recommendations") or data.get("dietary_recommendations")
#             ),
#             "activity_restrictions": _to_list(data.get("activity_restrictions")),

#             # ── Follow-up / summary ───────────────────────────────────────────
#             "follow_up": data.get("follow_up") or "",
#             "summary":   data.get("summary") or "",
#         }

#     # ── Main extraction ──────────────────────────────────────────────────────
#     def extract(self, text: str) -> dict:
#         # Step 1 — rule-based extraction
#         patient_info = self.extract_patient_info(text)

#         # Step 2 — LLM extraction
#         prompt = f"""
# You are an expert clinical medical information extraction system used in hospitals.

# Your task is to extract COMPLETE and HIGHLY DETAILED structured medical data from the given text.

# Return ONLY valid JSON — no markdown, no explanation, no preamble.

# JSON STRUCTURE:
# {{
#   "patient_info": {{
#     "name": "",
#     "age": null,
#     "gender": "",
#     "history": []
#   }},
#   "chief_complaints": [],
#   "symptoms": [],
#   "medical_conditions": [],
#   "risk_factors": [],
#   "vitals": {{
#     "blood_pressure": "",
#     "heart_rate": "",
#     "oxygen_saturation": "",
#     "temperature": "",
#     "respiratory_rate": "",
#     "weight": "",
#     "height": ""
#   }},
#   "lab_results": {{
#     "blood_tests": [],
#     "ecg": "",
#     "imaging": []
#   }},
#   "diagnosis": [],
#   "procedures": [],
#   "hospital_course": [],
#   "medications": [
#     {{
#       "name": "",
#       "dose": "",
#       "frequency": "",
#       "duration": "",
#       "purpose": ""
#     }}
#   ],
#   "doctor_instructions": [],
#   "diet_recommendations": [],
#   "activity_restrictions": [],
#   "emergency_signs": [],
#   "follow_up": "",
#   "summary": ""
# }}

# STRICT RULES:
# - Extract EVERYTHING mentioned in the text
# - Do NOT miss ANY clinical detail
# - Use precise medical terminology
# - Extract name, age, gender even if implicit (e.g. "58-year-old male")
# - Extract ALL symptoms (even minor ones)
# - Extract ALL diseases (past + present)
# - Extract lifestyle risks (smoking, sedentary lifestyle, alcohol use)
# - Extract vitals EXACTLY as written
# - Extract lab findings (ECG, troponin, HbA1c, etc.)
# - Extract procedures (angiography, PCI, stent, surgery, etc.)
# - Extract full medication details (name, dose, frequency, duration, purpose)
# - hospital_course = key events during hospital stay
# - summary = 2-3 lines in clinical style
# - DO NOT hallucinate — if not present use empty list or null
# - Output STRICT JSON only

# TEXT:
# \"\"\"{text}\"\"\"
# """

#         response = self.llm.invoke(prompt)

#         # Step 3 — parse JSON
#         raw = response.content if hasattr(response, "content") else str(response)

#         # strip markdown fences
#         raw = re.sub(r"```json|```", "", raw).strip()
#         match = re.search(r"\{.*\}", raw, re.DOTALL)
#         if match:
#             raw = match.group(0)
#         # fix trailing commas
#         raw = re.sub(r",\s*}", "}", raw)
#         raw = re.sub(r",\s*]", "]", raw)

#         try:
#             llm_data = json.loads(raw)
#         except Exception as e:
#             return {
#                 "error": "Invalid JSON from LLM",
#                 "raw_output": response.content if hasattr(response, "content") else str(response)
#             }

#         # Step 4 — normalize (merges rule-based patient info)
#         return self.normalize(llm_data, patient_info)


# # ── Helper ───────────────────────────────────────────────────────────────────
# def _to_list(value) -> list:
#     if value is None:
#         return []
#     if isinstance(value, list):
#         return value
#     if isinstance(value, str):
#         return [value] if value.strip() else []
#     return [value]


# # singleton
# medical_extractor = MedicalExtractor()




# backend/core/medical_extractor.py
# 🔥 FAST VERSION - No LLM, pure regex extraction

import re
from typing import Dict, List, Any


class MedicalExtractor:
    """
    FAST medical entity extractor using regex patterns.
    No LLM calls = <10ms response time.
    """
    
    def __init__(self):
        # Pre-compile all regex patterns for speed
        self.patterns = {
            'name': re.compile(r"(?:Patient\s*Name|Name)[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", re.IGNORECASE),
            'age_direct': re.compile(r"Age[:\-]?\s*(\d{1,3})", re.IGNORECASE),
            'age_year_old': re.compile(r"(\d{1,3})[\s-]*year[\s-]*old", re.IGNORECASE),
            'age_years_old': re.compile(r"(\d{1,3})[\s-]*years[\s-]*old", re.IGNORECASE),
            'gender': re.compile(r"\b(Male|Female|Other|M|F)\b", re.IGNORECASE),
            'gender_label': re.compile(r"Gender[:\-]?\s*(Male|Female|Other)", re.IGNORECASE),
        }
        
        # Common symptoms for quick extraction
        self.common_symptoms = [
            "pain", "fever", "cough", "headache", "nausea", "vomiting",
            "dizziness", "fatigue", "weakness", "shortness of breath",
            "chest pain", "abdominal pain", "back pain", "joint pain"
        ]
        
        # Common medications
        self.common_medications = [
            "metformin", "aspirin", "atorvastatin", "clopidogrel",
            "metoprolol", "ramipril", "lisinopril", "insulin",
            "paracetamol", "ibuprofen", "amoxicillin"
        ]

    def extract_patient_info(self, text: str) -> Dict[str, Any]:
        """Extract name, age, gender using regex only"""
        info = {}
        
        # Name extraction
        name_match = self.patterns['name'].search(text)
        if name_match:
            info["name"] = name_match.group(1).strip()
        
        # Age extraction (try multiple patterns)
        age = None
        age_match = self.patterns['age_year_old'].search(text)
        if not age_match:
            age_match = self.patterns['age_years_old'].search(text)
        if not age_match:
            age_match = self.patterns['age_direct'].search(text)
        
        if age_match:
            try:
                age = int(age_match.group(1))
                info["age"] = age
            except ValueError:
                pass
        
        # Gender extraction
        gender_match = self.patterns['gender_label'].search(text)
        if not gender_match:
            gender_match = self.patterns['gender'].search(text)
        
        if gender_match:
            gender = gender_match.group(1).capitalize()
            if gender == "M":
                gender = "Male"
            elif gender == "F":
                gender = "Female"
            info["gender"] = gender
        
        return info

    def extract_symptoms(self, text: str) -> List[str]:
        """Extract symptoms using keyword matching"""
        text_lower = text.lower()
        found = []
        for symptom in self.common_symptoms:
            if symptom in text_lower:
                found.append(symptom)
        return found

    def extract_medications(self, text: str) -> List[Dict[str, str]]:
        """Extract medication names"""
        text_lower = text.lower()
        found = []
        for med in self.common_medications:
            if med in text_lower:
                found.append({"name": med, "dose": "", "frequency": "", "duration": "", "purpose": ""})
        return found

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Main extraction method - FAST (no LLM)
        Returns structured data similar to LLM version but faster
        """
        if not text or not isinstance(text, str):
            return {}
        
        patient_info = self.extract_patient_info(text)
        
        # Build response structure (matching expected format)
        result = {
            "patient_info": patient_info,
            "chief_complaints": [],
            "symptoms": self.extract_symptoms(text),
            "diagnosis": [],
            "risk_factors": [],
            "vitals": {},
            "lab_results": {},
            "medications": self.extract_medications(text),
            "doctor_instructions": [],
            "diet_recommendations": [],
            "activity_restrictions": [],
            "emergency_signs": [],
            "follow_up": "",
            "summary": "",
            "procedures": [],
            "hospital_course": []
        }
        
        return result


# Singleton instance
medical_extractor = MedicalExtractor()