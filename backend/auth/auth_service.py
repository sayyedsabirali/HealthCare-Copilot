from bson import ObjectId
from fastapi import HTTPException

from database.mongo_client import db
from backend.auth.auth_utils import hash_password, verify_password, create_access_token

users = db["users"]


class AuthService:

    def register(self, email: str, password: str):

        existing_user = users.find_one({"email": email})

        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = hash_password(password)

        patient_id = str(ObjectId())

        user = {
            "email": email,
            "password": hashed_password,
            "patient_id": patient_id
        }

        users.insert_one(user)

        return {
            "message": "User registered successfully"
        }

    def login(self, email: str, password: str):

        user = users.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({
            "user_id": str(user["_id"]),
            "patient_id": user["patient_id"]
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "patient_id": user["patient_id"]   # 🔥 ADD THIS
        }

auth_service = AuthService()