import asyncio

from backend.config import FALLBACK_MODEL, PRIMARY_MODEL, get_openrouter_client, logger


def call_ai(prompt: str, max_tokens: int = 2000) -> str:
    try:
        openrouter_client = get_openrouter_client()
        response = openrouter_client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            timeout=90,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.warning(
            "Primary model %s failed: %s. Falling back to %s.",
            PRIMARY_MODEL,
            exc,
            FALLBACK_MODEL,
        )
        try:
            openrouter_client = get_openrouter_client()
            response = openrouter_client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=90,
            )
            return response.choices[0].message.content
        except Exception as fallback_exc:
            logger.error("Fallback model also failed: %s", fallback_exc)
            raise fallback_exc


async def stream_ai_async(prompt: str, max_tokens: int = 2000):
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def enqueue_stream(model_name: str):
        openrouter_client = get_openrouter_client()
        stream = openrouter_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            stream=True,
            timeout=90,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                loop.call_soon_threadsafe(queue.put_nowait, delta.content)

    def run_stream():
        try:
            enqueue_stream(PRIMARY_MODEL)
        except Exception as exc:
            logger.warning(
                "Primary model stream %s failed: %s. Falling back to %s.",
                PRIMARY_MODEL,
                exc,
                FALLBACK_MODEL,
            )
            try:
                enqueue_stream(FALLBACK_MODEL)
            except Exception as fallback_exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait, f"__ERROR__:{fallback_exc}"
                )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    asyncio.get_event_loop().run_in_executor(None, run_stream)

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        if chunk.startswith("__ERROR__:"):
            raise Exception(chunk[10:])
        yield chunk
