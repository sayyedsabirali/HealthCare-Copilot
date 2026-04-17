from database.mongo_client import db
from datetime import datetime

patients_col     = db["patients"]
medical_texts    = db["medical_texts"]
medical_reports  = db["medical_reports"]
medical_images   = db["medical_images"]


class PatientRepository:

    # ─────────────────────────────────────────────────────
    # CREATE or UPDATE patient using the JWT patient_id
    # (upsert so we never create a duplicate)
    # ─────────────────────────────────────────────────────
    def create_patient_record(self, patient_data: dict, patient_id: str = None) -> str:
        """
        Upsert a patient record.

        If `patient_id` is supplied (from the JWT token) we always
        upsert on that id so the same patient never gets two records.
        """
        if patient_id:
            patients_col.update_one(
                {"patient_id": patient_id},
                {
                    "$set": {
                        **patient_data,
                        "patient_id": patient_id,
                        "updated_at": datetime.utcnow(),
                    },
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )
            return patient_id

        # Fallback: old behaviour (should not be reached after this fix)
        from bson import ObjectId
        new_id = str(ObjectId())
        patient_data["patient_id"] = new_id
        patient_data["created_at"] = datetime.utcnow()
        patients_col.insert_one(patient_data)
        return new_id

    # ─────────────────────────────────────────────────────
    # GET patient by patient_id
    # ─────────────────────────────────────────────────────
    def get_patient(self, patient_id: str) -> dict | None:
        doc = patients_col.find_one({"patient_id": patient_id}, {"_id": 0})
        return doc

    # ─────────────────────────────────────────────────────
    # UPDATE medical data fields
    # ─────────────────────────────────────────────────────
    def update_medical_data(self, patient_id: str, medical_data: dict) -> bool:
        result = patients_col.update_one(
            {"patient_id": patient_id},
            {
                "$set": {
                    **medical_data,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,   # create the record if it doesn't exist yet
        )
        if result.modified_count > 0:
            return True
        if result.upserted_id is not None:
            return True
        return False

    # ─────────────────────────────────────────────────────
    # ADD symptoms
    # ─────────────────────────────────────────────────────
    def add_symptoms(self, patient_id: str, symptoms: dict | str) -> int:

        if isinstance(symptoms, str):
            symptoms = {"symptom": symptoms}

        result = patients_col.update_one(
            {"patient_id": patient_id},
            {
                "$addToSet": {"symptoms": symptoms},   
                "$set": {
                    "updated_at": datetime.utcnow(), 
                }
            }
        )
        return result.modified_count


patient_repository = PatientRepository()