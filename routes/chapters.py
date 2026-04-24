from fastapi import APIRouter, HTTPException

from ai import call_ai
from config import logger, supabase
from database import (
    get_approved_chapters,
    get_approved_outline,
    get_book,
    get_chapter,
    list_book_chapters,
    update_book_status,
    update_chapter,
)
from models import EditorFeedback
from prompts import (
    build_chapter_prompt,
    build_summary_prompt,
    count_outline_chapters,
    extract_chapter_title,
)
from services.notifications import notify


router = APIRouter(tags=["chapters"])


def _build_previous_summaries(approved_chapters: list[dict]) -> list[dict]:
    return [
        {"chapter_number": chapter["chapter_number"], "summary": chapter["summary"]}
        for chapter in approved_chapters
        if chapter.get("summary")
    ]


@router.get("/books/{book_id}/chapters")
async def list_chapters(
    book_id: str,
):
    try:
        book = get_book(book_id, client=supabase)
        if not book:
            raise HTTPException(404, "Book not found")

        chapters = list_book_chapters(book_id, client=supabase)
        approved_count = sum(1 for chapter in chapters if chapter["status"] == "approved")
        return {
            "book_title": book["title"],
            "book_status": book["status"],
            "progress": f"{approved_count}/{len(chapters)}",
            "chapters": chapters,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("List chapters failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.get("/chapters/{chapter_id}")
async def get_chapter_route(
    chapter_id: str,
):
    try:
        chapter = get_chapter(chapter_id, client=supabase)
        if not chapter:
            raise HTTPException(404, "Chapter not found")
        return {"chapter": chapter}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Get chapter failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.post("/chapters/{chapter_id}/feedback")
async def submit_chapter_feedback(
    chapter_id: str,
    feedback: EditorFeedback,
):
    try:
        if feedback.status not in {"approved", "needs_revision", "final_chapter"}:
            raise HTTPException(
                400,
                "Status must be 'approved', 'final_chapter', or 'needs_revision'",
            )

        chapter = get_chapter(chapter_id, client=supabase)
        if not chapter:
            raise HTTPException(404, "Chapter not found")

        book = get_book(chapter["book_id"], client=supabase)
        if not book:
            raise HTTPException(404, "Book not found")

        outline = get_approved_outline(chapter["book_id"], client=supabase)
        if not outline:
            raise HTTPException(404, "No approved outline found")

        if feedback.status in {"approved", "final_chapter"}:
            summary = call_ai(
                build_summary_prompt(chapter["chapter_number"], chapter["content"]),
                300,
            )
            update_chapter(
                chapter_id,
                client=supabase,
                status="approved",
                summary=summary,
                editor_notes=feedback.editor_notes,
            )

            approved_chapters = get_approved_chapters(chapter["book_id"], client=supabase)
            planned_chapter_count = count_outline_chapters(outline["content"])
            is_complete = feedback.status == "final_chapter" or (
                planned_chapter_count > 0
                and len(approved_chapters) >= planned_chapter_count
            )

            if is_complete:
                update_book_status(
                    chapter["book_id"], "chapters_complete", client=supabase
                )
                notify(
                    "book_complete",
                    book["title"],
                    "All chapters approved. Ready to compile.",
                )
                return {
                    "message": (
                        f"Chapter {chapter['chapter_number']} approved. "
                        "All planned chapters are complete."
                    ),
                    "status": "chapters_complete",
                    "chapter_number": chapter["chapter_number"],
                    "summary_saved": summary,
                }
            return {
                "message": f"Chapter {chapter['chapter_number']} approved!",
                "chapter_number": chapter["chapter_number"],
                "summary_saved": summary,
                "status": "approved",
            }

        approved_chapters = get_approved_chapters(chapter["book_id"], client=supabase)
        previous_summaries = _build_previous_summaries(approved_chapters)
        chapter_title = extract_chapter_title(
            outline["content"], chapter["chapter_number"]
        )
        new_content = call_ai(
            build_chapter_prompt(
                title=book["title"],
                outline=outline["content"],
                chapter_number=chapter["chapter_number"],
                chapter_title=chapter_title,
                previous_summaries=previous_summaries,
                editor_notes=feedback.editor_notes,
            ),
            3000,
        )
        update_chapter(
            chapter_id,
            client=supabase,
            content=new_content,
            status="waiting_for_review",
            editor_notes=feedback.editor_notes,
        )
        return {
            "message": f"Chapter {chapter['chapter_number']} regenerated!",
            "chapter_id": chapter_id,
            "new_content": new_content,
            "status": "waiting_for_review",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chapter feedback failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))
