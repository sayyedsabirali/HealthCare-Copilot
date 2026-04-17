from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from backend.auth.auth_dependency import get_current_user
from database.mongo_client import db
from datetime import datetime
from backend.core.medical_extractor import medical_extractor

import os
import json
import uuid
import shutil
import fitz
import pytesseract
import re
from PIL import Image

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# MongoDB Collections
medical_texts   = db["medical_texts"]
medical_reports = db["medical_reports"]
medical_images  = db["medical_images"]


# ─────────────────────────────────────────────────────────────
# SYNC TO PATIENT PROFILE
# All field names must match what medical_extractor.normalize() returns.
# ─────────────────────────────────────────────────────────────
def _sync_to_patient_profile(patient_id: str, data: dict):
    if not data:
        print("⚠️  No data to sync")
        return

    set_ops    = {"updated_at": datetime.utcnow()}
    push_ops   = {}

    # ── patient_info fields (scalar — just $set, don't overwrite with empty) ──
    pi = data.get("patient_info") or {}
    if pi.get("name"):
        set_ops["patient_info.name"]   = pi["name"]
    if pi.get("age") is not None:
        set_ops["patient_info.age"]    = pi["age"]
    if pi.get("gender"):
        set_ops["patient_info.gender"] = pi["gender"]
    if pi.get("history"):
        push_ops.setdefault("patient_info.history", []).extend(pi["history"])

    # ── list fields — push each new item (avoid duplicates via $addToSet) ────
    list_fields = [
        "diagnosis",
        "symptoms",
        "chief_complaints",
        "risk_factors",
        "procedures",
        "hospital_course",
        "emergency_signs",
        "doctor_instructions",
        "diet_recommendations",        # canonical name
        "activity_restrictions",
    ]
    for field in list_fields:
        items = data.get(field) or []
        if items:
            push_ops[field] = items

    # ── medications — stored as array of dicts, use $push (not $addToSet) ───
    meds = data.get("medications") or []
    if meds:
        push_ops["medications"] = meds

    # ── vitals / lab_results — merge dict fields ─────────────────────────────
    vitals = data.get("vitals") or {}
    for k, v in vitals.items():
        if v:
            set_ops[f"vitals.{k}"] = v

    lab = data.get("lab_results") or {}
    for k, v in lab.items():
        if v:
            set_ops[f"lab_results.{k}"] = v

    # ── follow_up / summary ───────────────────────────────────────────────────
    if data.get("follow_up"):
        set_ops["follow_up"] = data["follow_up"]
    if data.get("summary"):
        set_ops["summary"] = data["summary"]

    # Build the MongoDB update document
    update_doc: dict = {}
    if set_ops:
        update_doc["$set"] = set_ops

    # Use $push with $each for list/dict arrays
    if push_ops:
        push_each = {}
        for field, items in push_ops.items():
            push_each[field] = {"$each": items}
        update_doc["$push"] = push_each

    if not update_doc:
        return

    db["patients"].update_one(
        {"patient_id": patient_id},
        update_doc,
        upsert=True,
    )
    print("✅ Patient profile updated for:", patient_id)


# ─────────────────────────────────────────────────────────────
# TEXT UPLOAD
# ─────────────────────────────────────────────────────────────
class TextUpload(BaseModel):
    text: str


@router.post("/text")
def upload_text(data: TextUpload, user=Depends(get_current_user)):
    patient_id = user.get("patient_id")
    text = data.text.strip()
    if not text:
        raise HTTPException(400, "Text cannot be empty")

    try:
        # extract() already returns the fully normalised dict
        structured_data = medical_extractor.extract(text)

        if "error" in structured_data:
            print("⚠️  LLM extraction error:", structured_data.get("raw_output", "")[:200])
            structured_data = {}

        print("🔥 FINAL STRUCTURED (TEXT):", json.dumps(structured_data, indent=2)[:500])

    except Exception as e:
        print("🔥 Extraction exception:", e)
        raise HTTPException(500, "Extraction failed")

    doc = {
        "patient_id":     patient_id,
        "raw_text":       text,
        "structured_data": structured_data,
        "created_at":     datetime.utcnow(),
        "type":           "text",
    }
    result = medical_texts.insert_one(doc)

    _sync_to_patient_profile(patient_id, structured_data)

    return {
        "type":           "text",
        "structured_data": structured_data,
        "raw_text":       text,
        "document_id":    str(result.inserted_id),
        "collection":     "medical_texts",
        "profile_synced": True,
    }


# ─────────────────────────────────────────────────────────────
# FILE UPLOAD  (PDF / Image)
# ─────────────────────────────────────────────────────────────
@router.post("/medical-report")
async def upload_medical_report(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    patient_id = user.get("patient_id")
    filename   = file.filename or "upload"
    file_path  = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print("🔥 File save error:", e)
        raise HTTPException(500, "File upload failed")

    extracted_text = ""
    file_type      = "unknown"
    fname_lower    = filename.lower()

    if fname_lower.endswith(".pdf"):
        file_type = "pdf"
        try:
            doc = fitz.open(file_path)
            for page in doc:
                extracted_text += page.get_text()
        except Exception as e:
            print("🔥 PDF parse error:", e)

    elif fname_lower.endswith((".png", ".jpg", ".jpeg")):
        file_type = "image"
        try:
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image)
        except Exception as e:
            print("🔥 OCR error:", e)

    if len(extracted_text.strip()) < 20:
        raise HTTPException(400, "Could not extract enough text from this file. "
                                 "Ensure the PDF has selectable text or the image is legible.")

    try:
        structured_data = medical_extractor.extract(extracted_text)

        if "error" in structured_data:
            print("⚠️  LLM extraction error:", structured_data.get("raw_output", "")[:200])
            structured_data = {}

        print("🔥 FINAL STRUCTURED (FILE):", json.dumps(structured_data, indent=2)[:500])

    except Exception as e:
        print("🔥 Extraction exception:", e)
        raise HTTPException(500, "Extraction failed")

    collection = medical_images if file_type == "image" else medical_reports

    doc = {
        "patient_id":     patient_id,
        "filename":       filename,
        "file_path":      file_path,
        "file_type":      file_type,
        "extracted_text": extracted_text,
        "structured_data": structured_data,
        "created_at":     datetime.utcnow(),
    }
    result = collection.insert_one(doc)

    _sync_to_patient_profile(patient_id, structured_data)

    return {
        "message":        "File uploaded and processed",
        "document_id":    str(result.inserted_id),
        "extracted_text": extracted_text,
        "structured_data": structured_data,
        "profile_synced": True,
    }


# ─────────────────────────────────────────────────────────────
# MULTIPLE FILES
# ─────────────────────────────────────────────────────────────
@router.post("/multiple")
async def upload_multiple(
    files: list[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
):
    patient_id = user.get("patient_id")
    results = []

    for file in files:
        filename  = file.filename or "upload"
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{filename}")
        fname_lower = filename.lower()

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception:
            results.append({"file": filename, "status": "failed", "reason": "save error"})
            continue

        extracted_text = ""
        file_type      = "unknown"

        if fname_lower.endswith(".pdf"):
            file_type = "pdf"
            try:
                doc = fitz.open(file_path)
                for page in doc:
                    extracted_text += page.get_text()
            except Exception:
                pass

        elif fname_lower.endswith((".png", ".jpg", ".jpeg")):
            file_type = "image"
            try:
                image = Image.open(file_path)
                extracted_text = pytesseract.image_to_string(image)
            except Exception:
                pass

        elif fname_lower.endswith(".txt"):
            file_type = "text"
            try:
                with open(file_path, "r", errors="ignore") as f:
                    extracted_text = f.read()
            except Exception:
                pass

        if len(extracted_text.strip()) < 20:
            results.append({"file": filename, "status": "failed", "reason": "insufficient text"})
            continue

        try:
            structured_data = medical_extractor.extract(extracted_text)
            if "error" in structured_data:
                structured_data = {}
        except Exception:
            structured_data = {}

        collection = medical_images if file_type == "image" else (
            medical_texts if file_type == "text" else medical_reports
        )

        doc = {
            "patient_id":      patient_id,
            "filename":        filename,
            "file_path":       file_path,
            "file_type":       file_type,
            "extracted_text":  extracted_text,
            "structured_data": structured_data,
            "created_at":      datetime.utcnow(),
        }
        collection.insert_one(doc)
        _sync_to_patient_profile(patient_id, structured_data)

        results.append({"file": filename, "status": "ok"})

    return {"results": results}


# ─────────────────────────────────────────────────────────────
# GET COUNTS
# ─────────────────────────────────────────────────────────────
@router.get("/counts")
def get_upload_counts(user=Depends(get_current_user)):
    patient_id = user.get("patient_id")
    return {
        "text":      medical_texts.count_documents({"patient_id": patient_id}),
        "documents": medical_reports.count_documents({"patient_id": patient_id}),
        "images":    medical_images.count_documents({"patient_id": patient_id}),
    }


# ─────────────────────────────────────────────────────────────
# GET TEXTS
# ─────────────────────────────────────────────────────────────
@router.get("/my-texts")
def get_my_texts(user=Depends(get_current_user)):
    patient_id = user.get("patient_id")
    docs = list(
        medical_texts.find({"patient_id": patient_id}, {"_id": 0})
        .sort("created_at", -1)
    )
    for doc in docs:
        if "created_at" in doc:
            doc["created_at"] = doc["created_at"].isoformat()
    return {"texts": docs, "count": len(docs)}