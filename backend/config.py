import logging
import os
import sys

from openai import OpenAI
from supabase import Client, create_client


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

APP_TITLE = "AutoBook API"
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", os.environ["SUPABASE_KEY"])
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://autobook.railway.app",
    "X-Title": "AutoBook",
}

PRIMARY_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
FALLBACK_MODEL = "openrouter/free"


def get_supabase_client() -> Client:
    """Create a base Supabase client using the anon key for auth operations."""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase connected")
        return client
    except Exception as exc:
        logger.error("Supabase connection failed: %s", exc, exc_info=True)
        raise


def create_rls_client(access_token: str | None = None) -> Client:
    """Create a request-scoped Supabase client and attach the caller JWT for RLS."""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        if access_token:
            client.postgrest.auth(access_token)
        return client
    except Exception as exc:
        logger.error("RLS client creation failed: %s", exc, exc_info=True)
        raise


def get_openrouter_client() -> OpenAI:
    """Create the OpenRouter client used for generation requests."""
    try:
        client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=OPENROUTER_BASE_URL,
            default_headers=OPENROUTER_HEADERS,
        )
        logger.info("OpenRouter connected, primary model: %s", PRIMARY_MODEL)
        return client
    except Exception as exc:
        logger.error("OpenRouter connection failed: %s", exc, exc_info=True)
        raise


supabase = get_supabase_client()
openrouter_client = get_openrouter_client()
