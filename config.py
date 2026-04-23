import logging
import os

from openai import OpenAI
from supabase import Client, create_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_TITLE = "AutoBook API"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://autobook.railway.app",
    "X-Title": "AutoBook",
}

PRIMARY_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
FALLBACK_MODEL = "openrouter/free"


def get_supabase_client() -> Client:
    try:
        client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
        logger.info("Supabase connected")
        return client
    except Exception as exc:
        logger.error("Supabase connection failed: %s", exc)
        raise


def get_openrouter_client() -> OpenAI:
    try:
        client = OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url=OPENROUTER_BASE_URL,
            default_headers=OPENROUTER_HEADERS,
        )
        logger.info("OpenRouter connected, primary model: %s", PRIMARY_MODEL)
        return client
    except Exception as exc:
        logger.error("OpenRouter connection failed: %s", exc)
        raise


supabase = get_supabase_client()
openrouter_client = get_openrouter_client()
