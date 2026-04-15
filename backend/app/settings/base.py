import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core.apps.CoreConfig",
    "apps.documents.apps.DocumentsConfig",
    "apps.chat.apps.ChatConfig",
    "apps.demo.apps.DemoConfig",
    "apps.llm.apps.LLMConfig",
    "apps.retrieval.apps.RetrievalConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.mock_data.apps.MockDataConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "app.wsgi.application"
ASGI_APPLICATION = "app.asgi.application"

db_engine = os.getenv("DB_ENGINE")
if db_engine:
    DATABASES = {
        "default": {
            "ENGINE": db_engine,
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "NAME": os.getenv("DB_NAME", "smartdocsai"),
            "USER": os.getenv("DB_USER", "smartdocs"),
            "PASSWORD": os.getenv("DB_PASSWORD", "smartdocs"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / os.getenv("MEDIA_ROOT", "media")
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "smartdocsai_documents")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:1.5b")

PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://localhost:8888/ocr")
PADDLEOCR_TIMEOUT_SECONDS = env_int("PADDLEOCR_TIMEOUT_SECONDS", 60)
PADDLEOCR_API_KEY = os.getenv("PADDLEOCR_API_KEY", "")
PADDLEOCR_API_KEY_HEADER = os.getenv("PADDLEOCR_API_KEY_HEADER", "Authorization")
PADDLEOCR_API_KEY_PREFIX = os.getenv("PADDLEOCR_API_KEY_PREFIX", "Bearer")
PADDLEOCR_REQUEST_MODE = os.getenv("PADDLEOCR_REQUEST_MODE", "multipart")
PADDLEOCR_FILE_FIELD = os.getenv("PADDLEOCR_FILE_FIELD", "file")
PADDLEOCR_EXTRA_PARAMS_JSON = os.getenv("PADDLEOCR_EXTRA_PARAMS_JSON", "{}")
PADDLEOCR_MODEL = os.getenv("PADDLEOCR_MODEL", "PaddleOCR-VL-1.5")
PADDLEOCR_OPTIONAL_PAYLOAD_JSON = os.getenv("PADDLEOCR_OPTIONAL_PAYLOAD_JSON", "{}")
PADDLEOCR_JOB_POLL_SECONDS = env_int("PADDLEOCR_JOB_POLL_SECONDS", 5)
PADDLEOCR_JOB_TIMEOUT_SECONDS = env_int("PADDLEOCR_JOB_TIMEOUT_SECONDS", 300)

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "gemini-embedding-2-preview")
EMBEDDING_VECTOR_SIZE = env_int("EMBEDDING_VECTOR_SIZE", 3072)  # gemini-embedding-2-preview returns 3072-dim vectors
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
EMBEDDING_TIMEOUT_SECONDS = env_int("EMBEDDING_TIMEOUT_SECONDS", 60)
EMBEDDING_GEMINI_TASK_TYPE_DOCUMENT = os.getenv("EMBEDDING_GEMINI_TASK_TYPE_DOCUMENT", "RETRIEVAL_DOCUMENT")
EMBEDDING_GEMINI_TASK_TYPE_QUERY = os.getenv("EMBEDDING_GEMINI_TASK_TYPE_QUERY", "RETRIEVAL_QUERY")
EMBEDDING_STRICT = env_bool("EMBEDDING_STRICT", False)

CHUNK_SIZE = env_int("CHUNK_SIZE", 700)
CHUNK_OVERLAP = env_int("CHUNK_OVERLAP", 120)
RETRIEVAL_TOP_K = env_int("RETRIEVAL_TOP_K", 5)

SESSION_MEMORY_ENABLED = env_bool("SESSION_MEMORY_ENABLED", True)
SESSION_MEMORY_MAX_TURNS = env_int("SESSION_MEMORY_MAX_TURNS", 8)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.handlers.drf_exception_handler",
}
