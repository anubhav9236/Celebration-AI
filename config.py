import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "celebrationai-dev-secret-key-change-in-prod-82bbf40a")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "celebration.db"))
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request payload
    DEFAULT_CURRENCY = "INR"
    DEFAULT_CURRENCY_SYMBOL = "₹"
