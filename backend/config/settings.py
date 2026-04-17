from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str = "AI Health Copilot"
    APP_VERSION: str = "1.0"

    # LLM Provider - CHANGE THIS TO "openai"
    LLM_PROVIDER: str = "openai"  # 🔥 CHANGE: groq → openai
    
    # API Keys
    ANTHROPIC_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None  # 🔥 ADD THIS

    # MongoDB
    MONGO_URI: str
    DATABASE_NAME: str

    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Nutritionix
    USDA_API_KEY: str

    # LangSmith
    LANGSMITH_TRACING: str | None = None
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()