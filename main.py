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
app = FastAPI(title="AutoBook API")

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
    deepseek = OpenAI(
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
    status: str
    editor_notes: str = ""

# ─── HELPER: CALL DEEPSEEK ────────────────────────────────
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

    logger.info(f"🤖 Calling DeepSeek for outline: {title}")
    response = deepseek.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    logger.info("✅ DeepSeek response received")
    return response.choices[0].message.content

# ─── ROUTE 1: CREATE BOOK + GENERATE OUTLINE ──────────────
@app.post("/books/create")
async def create_book(input: BookInput):
    try:
        logger.info(f"📖 Creating book: {input.title}")

        # 1. Save book to Supabase
        book_result = supabase.table("books").insert({
            "title": input.title,
            "notes": input.notes,
            "status": "generating"
        }).execute()
        logger.info(f"✅ Book saved to DB: {book_result.data}")

        book = book_result.data[0]
        book_id = book["id"]

        # 2. Generate outline
        outline_content = generate_outline(input.title, input.notes)

        # 3. Save outline
        outline_result = supabase.table("outlines").insert({
            "book_id": book_id,
            "content": outline_content,
            "status": "waiting_for_review"
        }).execute()
        logger.info(f"✅ Outline saved to DB")

        outline = outline_result.data[0]

        # 4. Update book status
        supabase.table("books").update({
            "status": "waiting_for_review"
        }).eq("id", book_id).execute()

        return {
            "message": "Book created and outline generated!",
            "book_id": book_id,
            "outline_id": outline["id"],
            "outline": outline_content,
            "status": "waiting_for_review",
            "next_step": f"Review the outline and call /books/{book_id}/feedback"
        }

    except Exception as e:
        logger.error(f"❌ Error in create_book: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ─── ROUTE 2: GET BOOK STATUS ─────────────────────────────
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

# ─── ROUTE 3: EDITOR FEEDBACK ─────────────────────────────
@app.post("/books/{book_id}/feedback")
async def submit_feedback(book_id: str, feedback: EditorFeedback):
    try:
        if feedback.status not in ["approved", "needs_revision"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be 'approved' or 'needs_revision'"
            )

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
                "status": "outline_approved"
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
        logger.error(f"❌ Error in submit_feedback: {str(e)}", exc_info=True)
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

# ─── HEALTH CHECK ─────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "AutoBook API is running! 🚀"}