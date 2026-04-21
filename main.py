from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import os
from supabase import create_client
from openai import OpenAI

# ─── SETUP ────────────────────────────────────────────────
app = FastAPI(title="AutoBook API")

# Supabase client
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# DeepSeek client (uses OpenAI-compatible API)
deepseek = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# ─── REQUEST MODELS ───────────────────────────────────────
class BookInput(BaseModel):
    title: str
    notes: str

class EditorFeedback(BaseModel):
    status: str        # "approved" or "needs_revision"
    editor_notes: str = ""

# ─── HELPER: CALL DEEPSEEK ────────────────────────────────
def generate_outline(title: str, notes: str, editor_notes: str = "") -> str:
    """Call DeepSeek to generate a book outline."""

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

    response = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )

    return response.choices[0].message.content

# ─── ROUTE 1: CREATE BOOK + GENERATE OUTLINE ──────────────
@app.post("/books/create")
async def create_book(input: BookInput):
    """
    Step 1: Takes title + notes, saves book to DB,
    generates outline, saves outline with status = waiting_for_review
    """

    # 1. Save book to Supabase
    book_result = supabase.table("books").insert({
        "title": input.title,
        "notes": input.notes,
        "status": "generating"
    }).execute()

    book = book_result.data[0]
    book_id = book["id"]

    # 2. Generate outline using DeepSeek
    outline_content = generate_outline(input.title, input.notes)

    # 3. Save outline to Supabase
    outline_result = supabase.table("outlines").insert({
        "book_id": book_id,
        "content": outline_content,
        "status": "waiting_for_review"
    }).execute()

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

# ─── ROUTE 2: GET BOOK STATUS ─────────────────────────────
@app.get("/books/{book_id}")
async def get_book(book_id: str):
    """Get current status and outline of a book."""

    book = supabase.table("books").select("*").eq("id", book_id).execute()
    if not book.data:
        raise HTTPException(status_code=404, detail="Book not found")

    outline = supabase.table("outlines").select("*").eq("book_id", book_id)\
        .order("created_at", desc=True).limit(1).execute()

    return {
        "book": book.data[0],
        "outline": outline.data[0] if outline.data else None
    }

# ─── ROUTE 3: EDITOR SUBMITS FEEDBACK ─────────────────────
@app.post("/books/{book_id}/feedback")
async def submit_feedback(book_id: str, feedback: EditorFeedback):
    """
    Editor approves or requests revision.
    - If approved     → book moves to chapter generation stage
    - If needs_revision → regenerate outline with editor notes
    """

    if feedback.status not in ["approved", "needs_revision"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be 'approved' or 'needs_revision'"
        )

    # Get latest outline
    outline_result = supabase.table("outlines").select("*")\
        .eq("book_id", book_id).order("created_at", desc=True).limit(1).execute()

    if not outline_result.data:
        raise HTTPException(status_code=404, detail="Outline not found")

    outline = outline_result.data[0]

    # Get book
    book_result = supabase.table("books").select("*").eq("id", book_id).execute()
    book = book_result.data[0]

    if feedback.status == "approved":
        # Mark outline as approved
        supabase.table("outlines").update({
            "status": "approved",
            "editor_notes": feedback.editor_notes
        }).eq("id", outline["id"]).execute()

        # Update book status
        supabase.table("books").update({
            "status": "outline_approved"
        }).eq("id", book_id).execute()

        return {
            "message": "✅ Outline approved! Ready for chapter generation.",
            "book_id": book_id,
            "status": "outline_approved",
            "next_step": "Milestone 2 — Chapter generation will begin soon!"
        }

    elif feedback.status == "needs_revision":
        # Update old outline status
        supabase.table("outlines").update({
            "status": "needs_revision",
            "editor_notes": feedback.editor_notes
        }).eq("id", outline["id"]).execute()

        # Regenerate outline with editor notes
        new_outline_content = generate_outline(
            title=book["title"],
            notes=book["notes"],
            editor_notes=feedback.editor_notes
        )

        # Save new outline
        new_outline = supabase.table("outlines").insert({
            "book_id": book_id,
            "content": new_outline_content,
            "status": "waiting_for_review"
        }).execute()

        # Update book status
        supabase.table("books").update({
            "status": "waiting_for_review"
        }).eq("id", book_id).execute()

        return {
            "message": "🔄 Outline regenerated with your feedback!",
            "book_id": book_id,
            "outline_id": new_outline.data[0]["id"],
            "new_outline": new_outline_content,
            "status": "waiting_for_review",
            "next_step": f"Review the new outline and call /books/{book_id}/feedback again"
        }

# ─── ROUTE 4: LIST ALL BOOKS ──────────────────────────────
@app.get("/books")
async def list_books():
    """List all books and their statuses."""
    books = supabase.table("books").select("*").order("created_at", desc=True).execute()
    return {"books": books.data}

# ─── HEALTH CHECK ─────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "AutoBook API is running! 🚀"}
