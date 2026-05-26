import os
from pathlib import Path

from dotenv import load_dotenv

_api_dir = Path(__file__).resolve().parent

# Set model download directory to api/models before importing any ML libraries
_models_dir = _api_dir / "models"
_models_dir.mkdir(exist_ok=True)
os.environ["HF_HOME"] = str(_models_dir)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_models_dir)
os.environ["TORCH_HOME"] = str(_models_dir)
load_dotenv(_api_dir / ".env")
load_dotenv(_api_dir.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_TEXT = os.getenv("MODEL_TEXT", "mrm8488/bert-tiny-finetuned-fake-news-detection")
MODEL_IMAGE_CAPTION = os.getenv(
    "MODEL_IMAGE_CAPTION", "Salesforce/blip-image-captioning-base"
)
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{_api_dir / 'detections.db'}"
)
# For PostgreSQL, use: postgresql+asyncpg://user:password@host:port/database
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL", 
    DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://") if "sqlite://" in DATABASE_URL 
    else DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
)
USE_ASYNC_DB = os.getenv("USE_ASYNC_DB", "false").lower() in ("true", "1", "yes")
USE_LLM = os.getenv("USE_LLM", "true").lower() in ("true", "1", "yes")
EAGER_LOAD_MODELS = os.getenv("EAGER_LOAD_MODELS", "false").lower() in (
    "true",
    "1",
    "yes",
)
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if o.strip()
]
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", "5242880"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Caching
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))

# Rate limiting
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

# ML timeouts (seconds)
ML_TIMEOUT_SECONDS = float(os.getenv("ML_TIMEOUT_SECONDS", "300"))
URL_FETCH_TIMEOUT_SECONDS = float(os.getenv("URL_FETCH_TIMEOUT_SECONDS", "15"))

# Prevent Rust tokenizer deadlocks in ThreadPoolExecutors
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# GPU / CUDA setup
try:
    import torch
    USE_GPU = torch.cuda.is_available()
    DEVICE = 0 if USE_GPU else -1
    DEVICE_STR = "cuda" if USE_GPU else "cpu"
except ImportError:
    USE_GPU = False
    DEVICE = -1
    DEVICE_STR = "cpu"

# Optional stronger / secondary models (all free on Hugging Face)
MODEL_IMAGE_AI = os.getenv(
    "MODEL_IMAGE_AI", "dima806/deepfake_vs_real_face_detection"
)
USE_IMAGE_AI_CLASSIFIER = os.getenv("USE_IMAGE_AI_CLASSIFIER", "true").lower() in (
    "true",
    "1",
    "yes",
)

# Enhanced model options
MODEL_TEXT_ENHANCED = os.getenv(
    "MODEL_TEXT_ENHANCED", "roberta-base-openai-detector"
)
MODEL_ZERO_SHOT = os.getenv(
    "MODEL_ZERO_SHOT", "facebook/bart-large-mnli"
)
MODEL_AUDIO = os.getenv(
    "MODEL_AUDIO", "facebook/wav2vec2-base"
)

# Ensemble models for voting
MODEL_ENSEMBLE = os.getenv(
    "MODEL_ENSEMBLE", "microsoft/deberta-v3-base"
)
USE_ENSEMBLE = os.getenv("USE_ENSEMBLE", "false").lower() in (
    "true",
    "1",
    "yes",
)

# Zero-shot classification categories
ZERO_SHOT_CATEGORIES = os.getenv(
    "ZERO_SHOT_CATEGORIES", 
    "propaganda,satire,clickbait,conspiracy,real news"
).split(",")

# Default confidence threshold (%): only flag fake when confidence >= this
DEFAULT_CONFIDENCE_THRESHOLD = float(
    os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "50")
)

# Cookie / CSRF settings
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
CSRF_HEADER_NAME = os.getenv("CSRF_HEADER_NAME", "X-CSRF-Token")

# Celery / background job config
USE_CELERY = os.getenv("USE_CELERY", "false").lower() in ("true", "1", "yes")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))
