import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent

# Check if running in a serverless environment (Vercel, AWS Lambda) where project root is read-only
IS_SERVERLESS = bool(
    os.environ.get("VERCEL")
    or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    or os.environ.get("LAMBDA_TASK_ROOT")
)

if IS_SERVERLESS:
    DEFAULT_DB_PATH = "/tmp/celebration.db"
else:
    DEFAULT_DB_PATH = str(BASE_DIR / "celebration.db")

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "celebrationai-dev-secret-key-change-in-prod-82bbf40a")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request payload
    DEFAULT_CURRENCY = "INR"
    DEFAULT_CURRENCY_SYMBOL = "₹"

