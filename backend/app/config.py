import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

def _clean_gemini_key(key: str) -> str:
    if not key or not isinstance(key, str):
        return ""
    k = key.strip()
    # Reject Antigravity tokens (AQ.), placeholders, or malformed keys
    if k.startswith("AQ.") or "your_" in k.lower() or "<" in k or len(k) < 20:
        return ""
    return k

class Settings(BaseSettings):
    PROJECT_NAME: str = "Resume Interview AI"
    API_PREFIX: str = "/api"
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "resume_interview_ai")
    GEMINI_API_KEY: str = _clean_gemini_key(os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret-jwt-key-for-demo-purposes-12345")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

os.makedirs(settings.STORAGE_DIR, exist_ok=True)

