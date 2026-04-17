from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from langsmith import Client

from backend.config.settings import settings
from backend.api import patient, upload, chat
from backend.auth import auth_router


# -----------------------
# LangSmith Client
# -----------------------

client = Client()


# -----------------------
# FastAPI App
# -----------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Personal Health Copilot API",
    docs_url="/docs",
    redoc_url="/redoc"
)


# -----------------------
# CORS Middleware
# -----------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------
# Routers
# -----------------------

app.include_router(auth_router.router, prefix="")
app.include_router(patient.router, prefix="")
app.include_router(upload.router, prefix="")
app.include_router(chat.router, prefix="")


# -----------------------
# Root Endpoint
# -----------------------

@app.get("/")
def root():
    return {
        "message": "AI Health Copilot API running",
        "version": settings.APP_VERSION
    }


# -----------------------
# Health Check
# -----------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AI Health Copilot"
    }


# -----------------------
# Startup Event
# -----------------------

@app.on_event("startup")
def startup_event():
    print("🚀 AI Health Copilot API started")


# -----------------------
# Shutdown Event
# -----------------------

@app.on_event("shutdown")
def shutdown_event():
    print("🛑 AI Health Copilot API stopped")