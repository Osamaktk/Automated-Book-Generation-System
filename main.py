from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import logging
from supabase import create_client
from openai import OpenAI

# ─── LOGGING SETUP ────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── SETUP ────────────────────────────────────────────────
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AutoBook API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
try:
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"]
    )
    logger.info("✅ Supabase connected")
except Exception as e:
    logger.error(f"❌ Supabase connection failed: {e}")
    raise

# OpenRouter client (OpenAI-compatible)
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
    logger.error(f"❌ OpenRouter connection failed: {e}")
    raise

# ─── REQUEST MODELS ───────────────────────────────────────
class BookInput(BaseModel):
    title: str
    notes: str

class EditorFeedback(BaseModel):
    status: str        # "approved" or "needs_revision"
    editor_notes: str = ""

# ─── HELPER: CALL AI ──────────────────────────────────────
def call_ai(prompt: str, max_tokens: int = 2000) -> str:
    """Generic function to call OpenRouter AI."""
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

# ─── HELPER: GENERATE OUTLINE ─────────────────────────────
def generate_outline(title: str, notes: str, editor_notes: str = "") -> str:
    revision_text = ""
    if editor_notes:
        revision_text = f"\n\nEDITOR FEEDBACK (please apply this):\n{editor_notes}"

    prompt = f"""You are a professional book author and editor.
Generate a detailed book outline for the following:

TITLE: {title}
AUTHOR NOTES: {notes}{revision_text}

Your outline must include:
1. A brief book description (2-3 sentences)
2. List of chapters (at least 5) with:
   - Chapter number and title
   - A 2-3 sentence description of what happens in that chapter

Format it cleanly and professionally."""

    logger.info(f"🤖 Generating outline for: {title}")
    return call_ai(prompt, max_tokens=2000)

# ─── HELPER: GENERATE CHAPTER ─────────────────────────────
def generate_chapter(
    title: str,
    outline: str,
    chapter_number: int,
    chapter_title: str,
    previous_summaries: list,
    editor_notes: str = ""
) -> str:
    """Generate a single chapter with full context of previous chapters."""

    # Build previous chapters context
    context = ""
    if previous_summaries:
        context = "\n\nPREVIOUS CHAPTERS SUMMARY (for context and continuity):\n"
        for s in previous_summaries:
            context += f"Chapter {s['chapter_number']}: {s['summary']}\n"

    revision_text = ""
    if editor_notes:
        revision_text = f"\n\nEDITOR FEEDBACK (please apply this):\n{editor_notes}"

    prompt = f"""You are a professional novelist writing a book called "{title}".

FULL BOOK OUTLINE:
{outline}
{context}
NOW WRITE: Chapter {chapter_number} - {chapter_title}
{revision_text}

Instructions:
- Write a full, engaging chapter (minimum 800 words)
- Stay consistent with the characters, plot, and tone from previous chapters
- Use vivid descriptions and natural dialogue
- End the chapter in a way that makes the reader want to continue

Write the chapter now:"""

    logger.info(f"🤖 Generating Chapter {chapter_number}: {chapter_title}")
    return call_ai(prompt, max_tokens=3000)

# ─── HELPER: SUMMARIZE CHAPTER ────────────────────────────
def summarize_chapter(chapter_number: int, chapter_title: str, content: str) -> str:
    """Create a short summary of a chapter for use as context in future chapters."""

    prompt = f"""Summarize the following chapter in 3-5 sentences.
Focus on: key events, character developments, and important plot points.
This summary will be used to maintain story continuity in future chapters.

Chapter {chapter_number} - {chapter_title}:
{content[:3000]}

Write only the summary, nothing else:"""

    logger.info(f"📝 Summarizing Chapter {chapter_number}")
    return call_ai(prompt, max_tokens=300)

# ═══════════════════════════════════════════════════════════
# MILESTONE 1 ROUTES
# ═══════════════════════════════════════════════════════════

# ─── ROUTE 1: CREATE BOOK + GENERATE OUTLINE ──────────────
@app.post("/books/create")
async def create_book(input: BookInput):
    try:
        logger.info(f"📖 Creating book: {input.title}")

        book_result = supabase.table("books").insert({
            "title": input.title,
            "notes": input.notes,
            "status": "generating"
        }).execute()

        book = book_result.data[0]
        book_id = book["id"]

        outline_content = generate_outline(input.title, input.notes)

        outline_result = supabase.table("outlines").insert({
            "book_id": book_id,
            "content": outline_content,
            "status": "waiting_for_review"
        }).execute()

        outline = outline_result.data[0]

        supabase.table("books").update({
            "status": "waiting_for_review"
        }).eq("id", book_id).execute()

        return {
            "message": "Book created and outline generated!",
            "book_id": book_id,
            "outline_id": outline["id"],
            "outline": outline_content,
            "status": "waiting_for_review",
            "next_step": f"Review the outline and call POST /books/{book_id}/feedback"
        }

    except Exception as e:
        logger.error(f"❌ Error in create_book: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 2: GET BOOK ────────────────────────────────────
@app.get("/books/{book_id}")
async def get_book(book_id: str):
    try:
        book = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book.data:
            raise HTTPException(status_code=404, detail="Book not found")

        outline = supabase.table("outlines").select("*").eq("book_id", book_id)\
            .order("created_at", desc=True).limit(1).execute()

        return {
            "book": book.data[0],
            "outline": outline.data[0] if outline.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in get_book: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 3: OUTLINE FEEDBACK ────────────────────────────
@app.post("/books/{book_id}/feedback")
async def submit_outline_feedback(book_id: str, feedback: EditorFeedback):
    try:
        if feedback.status not in ["approved", "needs_revision"]:
            raise HTTPException(status_code=400, detail="Status must be 'approved' or 'needs_revision'")

        outline_result = supabase.table("outlines").select("*")\
            .eq("book_id", book_id).order("created_at", desc=True).limit(1).execute()

        if not outline_result.data:
            raise HTTPException(status_code=404, detail="Outline not found")

        outline = outline_result.data[0]
        book_result = supabase.table("books").select("*").eq("id", book_id).execute()
        book = book_result.data[0]

        if feedback.status == "approved":
            supabase.table("outlines").update({
                "status": "approved",
                "editor_notes": feedback.editor_notes
            }).eq("id", outline["id"]).execute()

            supabase.table("books").update({
                "status": "outline_approved"
            }).eq("id", book_id).execute()

            return {
                "message": "✅ Outline approved! Ready for chapter generation.",
                "book_id": book_id,
                "status": "outline_approved",
                "next_step": f"Call POST /books/{book_id}/generate-chapter to generate Chapter 1"
            }

        elif feedback.status == "needs_revision":
            supabase.table("outlines").update({
                "status": "needs_revision",
                "editor_notes": feedback.editor_notes
            }).eq("id", outline["id"]).execute()

            new_outline_content = generate_outline(
                title=book["title"],
                notes=book["notes"],
                editor_notes=feedback.editor_notes
            )

            new_outline = supabase.table("outlines").insert({
                "book_id": book_id,
                "content": new_outline_content,
                "status": "waiting_for_review"
            }).execute()

            supabase.table("books").update({
                "status": "waiting_for_review"
            }).eq("id", book_id).execute()

            return {
                "message": "🔄 Outline regenerated with your feedback!",
                "book_id": book_id,
                "outline_id": new_outline.data[0]["id"],
                "new_outline": new_outline_content,
                "status": "waiting_for_review"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in submit_outline_feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 4: LIST ALL BOOKS ──────────────────────────────
@app.get("/books")
async def list_books():
    try:
        books = supabase.table("books").select("*").order("created_at", desc=True).execute()
        return {"books": books.data}
    except Exception as e:
        logger.error(f"❌ Error in list_books: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# MILESTONE 2 ROUTES — CHAPTER ENGINE
# ═══════════════════════════════════════════════════════════

# ─── ROUTE 5: GENERATE NEXT CHAPTER ──────────────────────
@app.post("/books/{book_id}/generate-chapter")
async def generate_next_chapter(book_id: str):
    """
    Generates the next chapter in sequence.
    - Checks no chapter is pending review
    - Injects summaries of ALL previous approved chapters into prompt
    - Saves new chapter with status = waiting_for_review
    """
    try:
        # 1. Get book
        book_result = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book_result.data:
            raise HTTPException(status_code=404, detail="Book not found")
        book = book_result.data[0]

        # 2. Check outline is approved
        if book["status"] not in ["outline_approved", "chapters_in_progress"]:
            raise HTTPException(
                status_code=400,
                detail=f"Outline must be approved first. Current status: {book['status']}"
            )

        # 3. Get approved outline
        outline_result = supabase.table("outlines").select("*")\
            .eq("book_id", book_id).eq("status", "approved").execute()
        if not outline_result.data:
            raise HTTPException(status_code=404, detail="No approved outline found")
        outline = outline_result.data[0]

        # 4. Block if a chapter is waiting for review
        pending = supabase.table("chapters").select("*")\
            .eq("book_id", book_id).eq("status", "waiting_for_review").execute()
        if pending.data:
            raise HTTPException(
                status_code=400,
                detail=f"Chapter {pending.data[0]['chapter_number']} is waiting for review. Approve it first!"
            )

        # 5. Find next chapter number
        approved_chapters = supabase.table("chapters").select("*")\
            .eq("book_id", book_id).eq("status", "approved")\
            .order("chapter_number").execute()

        next_chapter_number = len(approved_chapters.data) + 1
        logger.info(f"📖 Generating Chapter {next_chapter_number}")

        # 6. Extract chapter title from outline
        chapter_title = f"Chapter {next_chapter_number}"
        for line in outline["content"].split("\n"):
            if f"Chapter {next_chapter_number}" in line or f"**{next_chapter_number}." in line:
                clean = line.replace("**", "").replace("*", "").strip()
                if clean:
                    chapter_title = clean
                    break

        # 7. Build previous summaries for context chaining
        previous_summaries = [
            {"chapter_number": c["chapter_number"], "summary": c["summary"]}
            for c in approved_chapters.data if c.get("summary")
        ]

        # 8. Generate chapter
        chapter_content = generate_chapter(
            title=book["title"],
            outline=outline["content"],
            chapter_number=next_chapter_number,
            chapter_title=chapter_title,
            previous_summaries=previous_summaries
        )

        # 9. Save to DB
        chapter_result = supabase.table("chapters").insert({
            "book_id": book_id,
            "chapter_number": next_chapter_number,
            "content": chapter_content,
            "status": "waiting_for_review"
        }).execute()

        chapter = chapter_result.data[0]

        # 10. Update book status
        supabase.table("books").update({
            "status": "chapters_in_progress"
        }).eq("id", book_id).execute()

        return {
            "message": f"✅ Chapter {next_chapter_number} generated!",
            "chapter_id": chapter["id"],
            "chapter_number": next_chapter_number,
            "chapter_title": chapter_title,
            "content": chapter_content,
            "context_used": f"{len(previous_summaries)} previous chapter summaries injected",
            "status": "waiting_for_review",
            "next_step": f"Review and call POST /chapters/{chapter['id']}/feedback"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in generate_next_chapter: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 6: LIST ALL CHAPTERS ───────────────────────────
@app.get("/books/{book_id}/chapters")
async def list_chapters(book_id: str):
    """List all chapters for a book with their statuses."""
    try:
        book = supabase.table("books").select("*").eq("id", book_id).execute()
        if not book.data:
            raise HTTPException(status_code=404, detail="Book not found")

        chapters = supabase.table("chapters").select(
            "id, chapter_number, status, editor_notes, created_at"
        ).eq("book_id", book_id).order("chapter_number").execute()

        approved_count = sum(1 for c in chapters.data if c["status"] == "approved")
        total_count = len(chapters.data)

        return {
            "book_title": book.data[0]["title"],
            "book_status": book.data[0]["status"],
            "progress": f"{approved_count}/{total_count} chapters approved",
            "chapters": chapters.data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in list_chapters: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 7: GET SINGLE CHAPTER ──────────────────────────
@app.get("/chapters/{chapter_id}")
async def get_chapter(chapter_id: str):
    """Get full content of a single chapter."""
    try:
        chapter = supabase.table("chapters").select("*").eq("id", chapter_id).execute()
        if not chapter.data:
            raise HTTPException(status_code=404, detail="Chapter not found")
        return {"chapter": chapter.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in get_chapter: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 8: CHAPTER FEEDBACK ────────────────────────────
@app.post("/chapters/{chapter_id}/feedback")
async def submit_chapter_feedback(chapter_id: str, feedback: EditorFeedback):
    """
    Editor approves or requests revision for a chapter.
    - approved      → summarize chapter, save summary, ready for next chapter
    - needs_revision → regenerate with editor notes
    """
    try:
        if feedback.status not in ["approved", "needs_revision"]:
            raise HTTPException(status_code=400, detail="Status must be 'approved' or 'needs_revision'")

        chapter_result = supabase.table("chapters").select("*").eq("id", chapter_id).execute()
        if not chapter_result.data:
            raise HTTPException(status_code=404, detail="Chapter not found")
        chapter = chapter_result.data[0]
        book_id = chapter["book_id"]

        book_result = supabase.table("books").select("*").eq("id", book_id).execute()
        book = book_result.data[0]

        outline_result = supabase.table("outlines").select("*")\
            .eq("book_id", book_id).eq("status", "approved").execute()
        outline = outline_result.data[0]

        if feedback.status == "approved":
            # Summarize chapter for future context
            summary = summarize_chapter(
                chapter_number=chapter["chapter_number"],
                chapter_title=f"Chapter {chapter['chapter_number']}",
                content=chapter["content"]
            )

            supabase.table("chapters").update({
                "status": "approved",
                "summary": summary,
                "editor_notes": feedback.editor_notes
            }).eq("id", chapter_id).execute()

            return {
                "message": f"✅ Chapter {chapter['chapter_number']} approved!",
                "chapter_number": chapter["chapter_number"],
                "summary_saved": summary,
                "status": "approved",
                "next_step": f"Call POST /books/{book_id}/generate-chapter for the next chapter"
            }

        elif feedback.status == "needs_revision":
            # Get previous summaries for context
            approved_chapters = supabase.table("chapters").select("*")\
                .eq("book_id", book_id).eq("status", "approved")\
                .order("chapter_number").execute()

            previous_summaries = [
                {"chapter_number": c["chapter_number"], "summary": c["summary"]}
                for c in approved_chapters.data if c.get("summary")
            ]

            chapter_title = f"Chapter {chapter['chapter_number']}"
            for line in outline["content"].split("\n"):
                if f"Chapter {chapter['chapter_number']}" in line:
                    clean = line.replace("**", "").replace("*", "").strip()
                    if clean:
                        chapter_title = clean
                        break

            new_content = generate_chapter(
                title=book["title"],
                outline=outline["content"],
                chapter_number=chapter["chapter_number"],
                chapter_title=chapter_title,
                previous_summaries=previous_summaries,
                editor_notes=feedback.editor_notes
            )

            supabase.table("chapters").update({
                "content": new_content,
                "status": "waiting_for_review",
                "editor_notes": feedback.editor_notes
            }).eq("id", chapter_id).execute()

            return {
                "message": f"🔄 Chapter {chapter['chapter_number']} regenerated with your feedback!",
                "chapter_id": chapter_id,
                "chapter_number": chapter["chapter_number"],
                "new_content": new_content,
                "status": "waiting_for_review",
                "next_step": f"Review and call POST /chapters/{chapter_id}/feedback again"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in submit_chapter_feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── HEALTH CHECK ─────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "AutoBook API is running! 🚀 Milestone 2 active."}