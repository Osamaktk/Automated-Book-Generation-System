import logging
import os
import sys
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from supabase import Client, create_client


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "frontend" / ".env")

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

APP_TITLE = "AutoBook API"
SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = (
    os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_KEY")
    or os.environ.get("VITE_SUPABASE_ANON_KEY", "")
)
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://autobook.railway.app",
    "X-Title": "AutoBook",
}
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

MODEL_CANDIDATES = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "mistralai/mistral-small-3.1-24b-instruct",
    "qwen/qwen-2.5-7b-instruct",
    "google/gemma-2-9b-it",
]
_openrouter_client: OpenAI | None = None
_deepseek_client: OpenAI | None = None


def get_supabase_client() -> Client:
    """Create a base Supabase client using the anon key for auth operations."""
    try:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError(
                "Missing Supabase configuration. Set SUPABASE_URL and SUPABASE_KEY "
                "or provide VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY."
            )
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase connected")
        return client
    except Exception as exc:
        logger.error("Supabase connection failed: %s", exc, exc_info=True)
        raise


def create_rls_client(access_token: str | None = None) -> Client:
    """Create a request-scoped Supabase client and attach the caller JWT for RLS."""
    try:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError(
                "Missing Supabase configuration. Set SUPABASE_URL and SUPABASE_KEY "
                "or provide VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY."
            )
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        if access_token:
            client.postgrest.auth(access_token)
        return client
    except Exception as exc:
        logger.error("RLS client creation failed: %s", exc, exc_info=True)
        raise


def get_openrouter_client() -> OpenAI:
    """Create the OpenRouter client used for generation requests."""
    global _openrouter_client
    if _openrouter_client is not None:
        return _openrouter_client

    try:
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing OPENROUTER_API_KEY. Add it to your environment or .env file "
                "before generating outlines or chapters."
            )

        client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers=OPENROUTER_HEADERS,
        )
        logger.info("OpenRouter connected, model order: %s", ", ".join(MODEL_CANDIDATES))
        _openrouter_client = client
        return _openrouter_client
    except Exception as exc:
        logger.error("OpenRouter connection failed: %s", exc, exc_info=True)
        raise


def get_deepseek_client() -> OpenAI:
    """Create the direct DeepSeek client when a DeepSeek API key is configured."""
    global _deepseek_client
    if _deepseek_client is not None:
        return _deepseek_client

    try:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "Missing DEEPSEEK_API_KEY. Add it to your environment or .env file "
                "before using direct DeepSeek generation."
            )

        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        logger.info("DeepSeek connected, model: %s", DEEPSEEK_MODEL)
        _deepseek_client = client
        return _deepseek_client
    except Exception as exc:
        logger.error("DeepSeek connection failed: %s", exc, exc_info=True)
        raise


supabase = get_supabase_client()
