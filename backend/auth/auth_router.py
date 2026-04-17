from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from backend.auth.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(request: RegisterRequest):
    return auth_service.register(request.email, request.password)


@router.post("/login")
def login(request: LoginRequest):
    return auth_service.login(request.email, request.password)