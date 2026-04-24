import asyncio

from backend.config import MODEL_CANDIDATES, get_openrouter_client, logger


def _create_completion(prompt: str, model_name: str, max_tokens: int):
    openrouter_client = get_openrouter_client()
    return openrouter_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        timeout=90,
    )


def call_ai(prompt: str, max_tokens: int = 2000) -> str:
    last_error = None
    for index, model_name in enumerate(MODEL_CANDIDATES):
        try:
            response = _create_completion(prompt, model_name, max_tokens)
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc
            if index < len(MODEL_CANDIDATES) - 1:
                logger.warning(
                    "OpenRouter model %s failed: %s. Trying %s next.",
                    model_name,
                    exc,
                    MODEL_CANDIDATES[index + 1],
                )
            else:
                logger.error("All OpenRouter models failed. Last error: %s", exc)
    raise last_error or RuntimeError("No OpenRouter models configured")


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
            last_error = None
            for index, model_name in enumerate(MODEL_CANDIDATES):
                try:
                    enqueue_stream(model_name)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    if index < len(MODEL_CANDIDATES) - 1:
                        logger.warning(
                            "OpenRouter stream model %s failed: %s. Trying %s next.",
                            model_name,
                            exc,
                            MODEL_CANDIDATES[index + 1],
                        )
                    else:
                        loop.call_soon_threadsafe(
                            queue.put_nowait, f"__ERROR__:{exc}"
                        )
            if last_error and len(MODEL_CANDIDATES) == 0:
                loop.call_soon_threadsafe(
                    queue.put_nowait, "__ERROR__:No OpenRouter models configured"
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
