import asyncio
import os

from backend.config import (
    DEEPSEEK_MODEL,
    MODEL_CANDIDATES,
    get_deepseek_client,
    get_openrouter_client,
    logger,
)


def _deepseek_enabled() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def _create_completion(prompt: str, model_name: str, max_tokens: int, provider: str):
    client = get_deepseek_client() if provider == "deepseek" else get_openrouter_client()
    return client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        timeout=90,
    )


def call_ai(prompt: str, max_tokens: int = 2000) -> str:
    attempts = []
    if _deepseek_enabled():
        attempts.append(("deepseek", DEEPSEEK_MODEL))
    attempts.extend(("openrouter", model_name) for model_name in MODEL_CANDIDATES)

    last_error = None
    for index, (provider, model_name) in enumerate(attempts):
        try:
            response = _create_completion(prompt, model_name, max_tokens, provider)
            return response.choices[0].message.content
        except Exception as exc:
            last_error = exc
            if index < len(attempts) - 1:
                next_provider, next_model = attempts[index + 1]
                logger.warning(
                    "%s model %s failed: %s. Trying %s %s next.",
                    provider.title(),
                    model_name,
                    exc,
                    next_provider.title(),
                    next_model,
                )
            else:
                logger.error("All AI providers failed. Last error: %s", exc)
    raise last_error or RuntimeError("No AI providers configured")


async def stream_ai_async(prompt: str, max_tokens: int = 2000):
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def enqueue_stream(model_name: str, provider: str):
        client = get_deepseek_client() if provider == "deepseek" else get_openrouter_client()
        stream = client.chat.completions.create(
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
            attempts = []
            if _deepseek_enabled():
                attempts.append(("deepseek", DEEPSEEK_MODEL))
            attempts.extend(("openrouter", model_name) for model_name in MODEL_CANDIDATES)
            last_error = None
            for index, (provider, model_name) in enumerate(attempts):
                try:
                    enqueue_stream(model_name, provider)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    if index < len(attempts) - 1:
                        next_provider, next_model = attempts[index + 1]
                        logger.warning(
                            "%s stream model %s failed: %s. Trying %s %s next.",
                            provider.title(),
                            model_name,
                            exc,
                            next_provider.title(),
                            next_model,
                        )
                    else:
                        loop.call_soon_threadsafe(
                            queue.put_nowait, f"__ERROR__:{exc}"
                        )
            if last_error and len(attempts) == 0:
                loop.call_soon_threadsafe(
                    queue.put_nowait, "__ERROR__:No AI providers configured"
                )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    loop.run_in_executor(None, run_stream)

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        if chunk.startswith("__ERROR__:"):
            raise Exception(chunk[10:])
        yield chunk
