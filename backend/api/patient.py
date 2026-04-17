from fastapi import APIRouter, HTTPException, Depends
from database.patient_repository import patient_repository
from backend.auth.auth_dependency import get_current_user

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/")
def create_patient(patient_data: dict, user=Depends(get_current_user)):
    """
    Create or update the patient record.
    Always uses the JWT patient_id so one user = one record.
    """
    patient_id = user["patient_id"]          # ← from JWT, not a new ObjectId
    patient_repository.create_patient_record(patient_data, patient_id=patient_id)

    return {
        "message": "Patient record saved",
        "patient_id": patient_id            # return the same id so frontend can use it
    }


@router.get("/me")
def get_my_patient(user=Depends(get_current_user)):
    """
    Convenience endpoint — returns the logged-in patient's full record.
    Frontend calls this instead of needing to know the patient_id.
    """
    patient_id = user["patient_id"]
    patient = patient_repository.get_patient(patient_id)

    if not patient:
        return {}     # empty dict, not 404 — profile just hasn't been created yet

    return patient


@router.get("/{patient_id}")
def get_patient(patient_id: str, user=Depends(get_current_user)):
    patient = patient_repository.get_patient(patient_id)

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


@router.put("/{patient_id}/medical-data")
def update_medical_data(patient_id: str, medical_data: dict, user=Depends(get_current_user)):
    patient_repository.update_medical_data(patient_id, medical_data)
    return {"message": "Medical data updated"}


@router.put("/me/medical-data")
def update_my_medical_data(medical_data: dict, user=Depends(get_current_user)):
    """Update medical data for the logged-in patient (no patient_id needed in URL)."""
    patient_id = user["patient_id"]
    patient_repository.update_medical_data(patient_id, medical_data)
    return {"message": "Medical data updated"}


@router.post("/{patient_id}/symptoms")
def add_symptoms(patient_id: str, symptoms: dict, user=Depends(get_current_user)):
    updated = patient_repository.add_symptoms(patient_id, symptoms)

    if updated == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {"message": "Symptoms recorded"}