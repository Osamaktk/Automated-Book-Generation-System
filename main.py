from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import json
import logging
import asyncio
from supabase import create_client
from openai import OpenAI

# ─── LOGGING ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── SETUP ────────────────────────────────────────────────
app = FastAPI(title="AutoBook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
try:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    logger.info("✅ Supabase connected")
except Exception as e:
    logger.error(f"❌ Supabase: {e}")
    raise

# OpenRouter
try:
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://autobook.railway.app",
            "X-Title": "AutoBook"
        }
    )
    logger.info("✅ OpenRouter connected")
except Exception as e:
    logger.error(f"❌ OpenRouter: {e}")
    raise

# ─── AI MODEL REGISTRY (PRODUCTION ROUTER) ─────────────────

MODEL_REGISTRY = {
    "fast": [
        "google/gemma-7b-it",
        "mistralai/mistral-7b-instruct",
    ],

    "balanced": [
        "mistralai/mistral-7b-instruct-v0.2",
        "meta-llama/llama-3-8b-instruct",
    ],

    "strong": [
        "meta-llama/llama-3.1-8b-instruct",
        "nousresearch/hermes-2-pro-llama-3-8b",
    ]
}

AI_MODEL_OVERRIDE = os.environ.get("AI_MODEL")

def route_task(prompt: str) -> str:
    p = prompt.lower()

    if any(word in p for word in ["summarize", "short", "extract"]):
        return "fast"

    if any(word in p for word in ["write", "chapter", "story", "book", "novel"]):
        return "strong"

    return "balanced"

# Optional override (if you still want manual control)
AI_MODEL = os.environ.get("AI_MODEL")
# ─── PYDANTIC MODELS ──────────────────────────────────────
class BookInput(BaseModel):
    title: str
    notes: str

class EditorFeedback(BaseModel):
    status: str
    editor_notes: str = ""

def call_ai(prompt: str, max_tokens: int = 2000) -> str:
    task = route_task(prompt)

    models = MODEL_REGISTRY.get(task, MODEL_REGISTRY["balanced"])

    last_error = None

    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=90
            )
            return response.choices[0].message.content

        except Exception as e:
            last_error = str(e)
            logger.warning(f"Model failed: {model} -> {e}")

    raise Exception(f"All models failed. Last error: {last_error}")

# ─── HELPER: STREAM AI (async generator) ──────────────────
async def stream_ai_async(prompt: str, max_tokens: int = 2000):
    """
    Async generator that streams text chunks from OpenRouter.
    Runs the blocking SDK call in a thread pool so it doesn't
    block the event loop.
    """
    loop = asyncio.get_running_loop()   # ← correct for async context
    queue: asyncio.Queue = asyncio.Queue()

    def run_stream():
        task = route_task(prompt)
        models = MODEL_REGISTRY.get(task, MODEL_REGISTRY["balanced"])

        last_error = None

        for model in models:
            try:
                stream = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    stream=True,
                    timeout=90
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if getattr(delta, "content", None):
                        loop.call_soon_threadsafe(queue.put_nowait, delta.content)

                loop.call_soon_threadsafe(queue.put_nowait, None)
                return

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Streaming failed: {model} -> {e}")

        loop.call_soon_threadsafe(queue.put_nowait, f"__ERROR__:{last_error}")
        loop.call_soon_threadsafe(queue.put_nowait, None)

    # Submit blocking work to thread pool
    loop.run_in_executor(None, run_stream)

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        if isinstance(chunk, str) and chunk.startswith("__ERROR__:"):
            raise Exception(chunk[10:])
        yield chunk

# ─── PROMPTS ──────────────────────────────────────────────
def outline_prompt(title: str, notes: str, editor_notes: str = "") -> str:
    rev = f"\n\nEDITOR FEEDBACK:\n{editor_notes}" if editor_notes else ""
    return f"""You are a professional book author and editor.
Generate a detailed book outline for the following:

TITLE: {title}
AUTHOR NOTES: {notes}{rev}

Your outline must include:
1. A brief book description (2-3 sentences)
2. List of chapters (at least 5) with:
   - Chapter number and title
   - A 2-3 sentence description of what happens in that chapter

Format it cleanly and professionally."""


def chapter_prompt(
    title: str,
    outline: str,
    chapter_number: int,
    chapter_title: str,
    previous_summaries: list,
    editor_notes: str = ""
) -> str:
    context = ""
    if previous_summaries:
        context = "\n\nPREVIOUS CHAPTERS SUMMARY:\n"
        for s in previous_summaries:
            context += f"Chapter {s['chapter_number']}: {s['summary']}\n"
    rev = f"\n\nEDITOR FEEDBACK:\n{editor_notes}" if editor_notes else ""
    return f"""You are a professional novelist writing a book called "{title}".

FULL BOOK OUTLINE:
{outline}
{context}
NOW WRITE: Chapter {chapter_number} - {chapter_title}
{rev}

Instructions:
- Write a full, engaging chapter (minimum 800 words)
- Stay consistent with characters, plot, and tone from previous chapters
- Use vivid descriptions and natural dialogue
- End in a way that makes the reader want to continue

Write the chapter now:"""


def summary_prompt(chapter_number: int, content: str) -> str:
    return f"""Summarize the following chapter in 3-5 sentences.
Focus on: key events, character developments, and important plot points.

Chapter {chapter_number}:
{content[:3000]}

Write only the summary:"""


# ─── UTILITY: extract chapter title from outline text ─────
def extract_chapter_title(outline_content: str, chapter_number: int) -> str:
    for line in outline_content.split("\n"):
        if f"Chapter {chapter_number}" in line or f"**{chapter_number}." in line:
            clean = line.replace("**", "").replace("*", "").strip()
            if clean:
                return clean
    return f"Chapter {chapter_number}"


# ═══════════════════════════════════════════════════════════
# STREAMING ROUTES
# ═══════════════════════════════════════════════════════════

@app.post("/books/create-stream")
async def create_book_stream(input: BookInput):
    """
    Creates a book record and streams the outline generation as SSE.
    Events: book_id | chunk | done | error
    """
    async def generate():
        try:
            # 1. Save book to DB
            book_result = supabase.table("books").insert({
                "title": input.title,
                "notes": input.notes,
                "status": "generating"
            }).execute()
            book_id = book_result.data[0]["id"]

            yield f"data: {json.dumps({'type': 'book_id', 'book_id': book_id})}\n\n"

            # 2. Stream outline from AI
            prompt = outline_prompt(input.title, input.notes)
            full_content = ""

            async for chunk in stream_ai_async(prompt, max_tokens=2000):
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

            # 3. Save outline to DB
            outline_result = supabase.table("outlines").insert({
                "book_id": book_id,
                "content": full_content,
                "status": "waiting_for_review"
            }).execute()

            supabase.table("books").update({"status": "waiting_for_review"}).eq("id", book_id).execute()

            yield f"data: {json.dumps({'type': 'done', 'book_id': book_id, 'outline_id': outline_result.data[0]['id']})}\n\n"

        except Exception as e:
            logger.error(f"❌ create-stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/books/{book_id}/generate-chapter-stream")
async def generate_chapter_stream(book_id: str):
    """
    Generates the next chapter and streams it as SSE.
    Events: chapter_info | chunk | done | error
    """
    async def generate():
        try:
            # 1. Get book
            book_result = supabase.table("books").select("*").eq("id", book_id).execute()
            if not book_result.data:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Book not found'})}\n\n"
                return
            book = book_result.data[0]

            if book["status"] not in ["outline_approved", "chapters_in_progress"]:
                msg = "Outline must be approved first. Status: " + book["status"]
                yield "data: " + json.dumps({"type": "error", "message": msg}) + "\n\n"
                return

            # 2. Get approved outline
            outline_result = (
                supabase.table("outlines")
                .select("*")
                .eq("book_id", book_id)
                .eq("status", "approved")
                .execute()
            )
            if not outline_result.data:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No approved outline found'})}\n\n"
                return
            outline = outline_result.data[0]

            # 3. Block if a chapter is already pending review
            pending = (
                supabase.table("chapters")
                .select("*")
                .eq("book_id", book_id)
                .eq("status", "waiting_for_review")
                .execute()
            )
            if pending.data:
                msg = "Chapter " + str(pending.data[0]["chapter_number"]) + " is waiting for review!"
                yield "data: " + json.dumps({"type": "error", "message": msg}) + "\n\n"
                return

            # 4. Next chapter number
            approved_chapters = (
                supabase.table("chapters")
                .select("*")
                .eq("book_id", book_id)
                .eq("status", "approved")
                .order("chapter_number")
                .execute()
            )
            next_num = len(approved_chapters.data) + 1

            # 5. Extract chapter title
            chapter_title = extract_chapter_title(outline["content"], next_num)

            # 6. Previous summaries
            previous_summaries = [
                {"chapter_number": c["chapter_number"], "summary": c["summary"]}
                for c in approved_chapters.data
                if c.get("summary")
            ]

            yield f"data: {json.dumps({'type': 'chapter_info', 'chapter_number': next_num, 'chapter_title': chapter_title})}\n\n"

            # 7. Stream chapter content  ← BUG FIX: was `for chunk in stream_ai(...)`
            prompt = chapter_prompt(book["title"], outline["content"], next_num, chapter_title, previous_summaries)
            full_content = ""

            async for chunk in stream_ai_async(prompt, max_tokens=3000):   # ← fixed
                full_content += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

            # 8. Save chapter
            chapter_result = supabase.table("chapters").insert({
                "book_id": book_id,
                "chapter_number": next_num,
                "content": full_content,
                "status": "waiting_for_review"
            }).execute()

            supabase.table("books").update({"status": "chapters_in_progress"}).eq("id", book_id).execute()

            yield f"data: {json.dumps({'type': 'done', 'chapter_id': chapter_result.data[0]['id'], 'chapter_number': next_num})}\n\n"

        except Exception as e:
            logger.error(f"❌ chapter-stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


# ═══════════════════════════════════════════════════════════
# STANDARD (non-streaming) ROUTES
# ═══════════════════════════════════════════════════════════

@app.post("/books/create")
async def create_book(input: BookInput):
    try:
        book_result = supabase.table("books").insert({
            "title": input.title,
            "notes": input.notes,
            "status": "generating"
        }).execute()
        book = book_result.data[0]
        book_id = book["id"]

        outline_content = call_ai(outline_prompt(input.title, input.notes), 2000)

        outline_result = supabase.table("outlines").insert({
            "book_id": book_id,
            "content": outline_content,
            "status": "waiting_for_review"
        }).execute()

        supabase.table("books").update({"status": "waiting_for_review"}).eq("id", book_id).execute()

        return {
            "message": "Book created!",
            "book_id": book_id,
            "outline_id": outline_result.data[0]["id"],
            "outline": outline_content,
            "status": "waiting_for_review"
        }
    except Exception as e:
        logger.error(f"❌ create_book: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@app.get("/books")
async def list_books():
    try:
        books = supabase.table("books").select("*").order("created_at", desc=True).execute()
        return {"books": books.data}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/books/{book_id}")
async def get_book(book_id: str):
    try:
        book = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book.data:
            raise HTTPException(404, "Book not found")
        outline = (
            supabase.table("outlines")
            .select("*")
            .eq("book_id", book_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return {"book": book.data[0], "outline": outline.data[0] if outline.data else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/books/{book_id}/feedback")
async def submit_outline_feedback(book_id: str, feedback: EditorFeedback):
    try:
        if feedback.status not in ["approved", "needs_revision"]:
            raise HTTPException(400, "Status must be 'approved' or 'needs_revision'")

        outline_result = (
            supabase.table("outlines")
            .select("*")
            .eq("book_id", book_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if not outline_result.data:
            raise HTTPException(404, "Outline not found")
        outline = outline_result.data[0]

        book_result = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book_result.data:
            raise HTTPException(404, "Book not found")
        book = book_result.data[0]

        if feedback.status == "approved":
            supabase.table("outlines").update({
                "status": "approved",
                "editor_notes": feedback.editor_notes
            }).eq("id", outline["id"]).execute()

            supabase.table("books").update({"status": "outline_approved"}).eq("id", book_id).execute()

            return {
                "message": "✅ Outline approved!",
                "book_id": book_id,
                "status": "outline_approved",
                "next_step": f"POST /books/{book_id}/generate-chapter-stream"
            }

        else:   # needs_revision
            supabase.table("outlines").update({
                "status": "needs_revision",
                "editor_notes": feedback.editor_notes
            }).eq("id", outline["id"]).execute()

            new_content = call_ai(outline_prompt(book["title"], book["notes"], feedback.editor_notes), 2000)

            new_outline = supabase.table("outlines").insert({
                "book_id": book_id,
                "content": new_content,
                "status": "waiting_for_review"
            }).execute()

            supabase.table("books").update({"status": "waiting_for_review"}).eq("id", book_id).execute()

            return {
                "message": "🔄 Outline regenerated!",
                "book_id": book_id,
                "outline_id": new_outline.data[0]["id"],
                "new_outline": new_content
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ submit_outline_feedback: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@app.post("/books/{book_id}/generate-chapter")
async def generate_next_chapter(book_id: str):
    """Non-streaming chapter generation (kept for compatibility)."""
    try:
        book_result = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book_result.data:
            raise HTTPException(404, "Book not found")
        book = book_result.data[0]

        if book["status"] not in ["outline_approved", "chapters_in_progress"]:
            raise HTTPException(400, f"Outline must be approved first. Status: {book['status']}")

        outline_result = (
            supabase.table("outlines")
            .select("*")
            .eq("book_id", book_id)
            .eq("status", "approved")
            .execute()
        )
        if not outline_result.data:
            raise HTTPException(404, "No approved outline found")
        outline = outline_result.data[0]

        pending = (
            supabase.table("chapters")
            .select("*")
            .eq("book_id", book_id)
            .eq("status", "waiting_for_review")
            .execute()
        )
        if pending.data:
            raise HTTPException(400, f"Chapter {pending.data[0]['chapter_number']} is waiting for review!")

        approved_chapters = (
            supabase.table("chapters")
            .select("*")
            .eq("book_id", book_id)
            .eq("status", "approved")
            .order("chapter_number")
            .execute()
        )
        next_num = len(approved_chapters.data) + 1
        chapter_title = extract_chapter_title(outline["content"], next_num)

        previous_summaries = [
            {"chapter_number": c["chapter_number"], "summary": c["summary"]}
            for c in approved_chapters.data
            if c.get("summary")
        ]

        content = call_ai(
            chapter_prompt(book["title"], outline["content"], next_num, chapter_title, previous_summaries),
            max_tokens=3000
        )

        chapter_result = supabase.table("chapters").insert({
            "book_id": book_id,
            "chapter_number": next_num,
            "content": content,
            "status": "waiting_for_review"
        }).execute()

        supabase.table("books").update({"status": "chapters_in_progress"}).eq("id", book_id).execute()

        return {
            "message": f"✅ Chapter {next_num} generated!",
            "chapter_id": chapter_result.data[0]["id"],
            "chapter_number": next_num,
            "content": content,
            "status": "waiting_for_review"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ generate_next_chapter: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@app.get("/books/{book_id}/chapters")
async def list_chapters(book_id: str):
    try:
        book = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book.data:
            raise HTTPException(404, "Book not found")

        chapters = (
            supabase.table("chapters")
            .select("id, chapter_number, status, editor_notes, created_at")
            .eq("book_id", book_id)
            .order("chapter_number")
            .execute()
        )

        approved = sum(1 for c in chapters.data if c["status"] == "approved")
        return {
            "book_title": book.data[0]["title"],
            "book_status": book.data[0]["status"],
            "progress": f"{approved}/{len(chapters.data)}",
            "chapters": chapters.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/chapters/{chapter_id}")
async def get_chapter(chapter_id: str):
    try:
        chapter = supabase.table("chapters").select("*").eq("id", chapter_id).execute()
        if not chapter.data:
            raise HTTPException(404, "Chapter not found")
        return {"chapter": chapter.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/chapters/{chapter_id}/feedback")
async def submit_chapter_feedback(chapter_id: str, feedback: EditorFeedback):
    try:
        if feedback.status not in ["approved", "needs_revision", "final_chapter"]:
            raise HTTPException(400, "Status must be 'approved', 'final_chapter', or 'needs_revision'")

        chapter_result = supabase.table("chapters").select("*").eq("id", chapter_id).execute()
        if not chapter_result.data:
            raise HTTPException(404, "Chapter not found")
        chapter = chapter_result.data[0]
        book_id = chapter["book_id"]

        book_result = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book_result.data:
            raise HTTPException(404, "Book not found")
        book = book_result.data[0]

        outline_result = (
            supabase.table("outlines")
            .select("*")
            .eq("book_id", book_id)
            .eq("status", "approved")
            .execute()
        )
        if not outline_result.data:
            raise HTTPException(404, "No approved outline found")
        outline = outline_result.data[0]

        if feedback.status in ["approved", "final_chapter"]:
            summary = call_ai(summary_prompt(chapter["chapter_number"], chapter["content"]), 300)

            supabase.table("chapters").update({
                "status": "approved",
                "summary": summary,
                "editor_notes": feedback.editor_notes
            }).eq("id", chapter_id).execute()

            if feedback.status == "final_chapter":
                supabase.table("books").update({"status": "chapters_complete"}).eq("id", book_id).execute()
                return {
                    "message": f"📚 Chapter {chapter['chapter_number']} approved as FINAL chapter!",
                    "status": "chapters_complete"
                }

            return {
                "message": f"✅ Chapter {chapter['chapter_number']} approved!",
                "chapter_number": chapter["chapter_number"],
                "summary_saved": summary,
                "status": "approved"
            }

        else:   # needs_revision
            # Only include summaries for chapters OTHER than the one being revised
            approved_chapters = (
                supabase.table("chapters")
                .select("*")
                .eq("book_id", book_id)
                .eq("status", "approved")
                .order("chapter_number")
                .execute()
            )
            previous_summaries = [
                {"chapter_number": c["chapter_number"], "summary": c["summary"]}
                for c in approved_chapters.data
                if c.get("summary") and c["chapter_number"] != chapter["chapter_number"]
            ]

            chapter_title = extract_chapter_title(outline["content"], chapter["chapter_number"])

            new_content = call_ai(
                chapter_prompt(
                    book["title"],
                    outline["content"],
                    chapter["chapter_number"],
                    chapter_title,
                    previous_summaries,
                    feedback.editor_notes
                ),
                max_tokens=3000
            )

            supabase.table("chapters").update({
                "content": new_content,
                "status": "waiting_for_review",
                "editor_notes": feedback.editor_notes
            }).eq("id", chapter_id).execute()

            return {
                "message": f"🔄 Chapter {chapter['chapter_number']} regenerated!",
                "chapter_id": chapter_id,
                "new_content": new_content,
                "status": "waiting_for_review"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ submit_chapter_feedback: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@app.get("/")
async def health():
    return {
        "status": "AutoBook API running 🚀",
        "streaming": True,
        "model": AI_MODEL
    }