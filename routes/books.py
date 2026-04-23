import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ai import call_ai, stream_ai_async
from config import logger
from database import (
    create_book,
    create_chapter,
    create_outline,
    get_approved_chapters,
    get_approved_outline,
    get_book,
    get_latest_outline,
    get_pending_review_chapter,
    list_books,
    update_book_status,
    update_outline,
)
from models import BookInput, EditorFeedback
from prompts import build_chapter_prompt, build_outline_prompt, extract_chapter_title


router = APIRouter(prefix="/books", tags=["books"])


def _serialize_event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _build_previous_summaries(approved_chapters: list[dict]) -> list[dict]:
    return [
        {"chapter_number": chapter["chapter_number"], "summary": chapter["summary"]}
        for chapter in approved_chapters
        if chapter.get("summary")
    ]


@router.post("/create-stream")
async def create_book_stream(input: BookInput):
    async def generate():
        try:
            book = create_book(input.title, input.notes, status="generating")
            book_id = book["id"]

            yield _serialize_event({"type": "book_id", "book_id": book_id})

            prompt = build_outline_prompt(input.title, input.notes)
            full_content = ""

            async for chunk in stream_ai_async(prompt, max_tokens=2000):
                full_content += chunk
                yield _serialize_event({"type": "chunk", "text": chunk})

            outline = create_outline(
                book_id=book_id,
                content=full_content,
                status="waiting_for_review",
            )
            update_book_status(book_id, "waiting_for_review")

            yield _serialize_event(
                {"type": "done", "book_id": book_id, "outline_id": outline["id"]}
            )
        except Exception as exc:
            logger.error("Outline stream error: %s", exc, exc_info=True)
            yield _serialize_event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/create")
async def create_book_route(input: BookInput):
    try:
        book = create_book(input.title, input.notes, status="generating")
        outline_content = call_ai(build_outline_prompt(input.title, input.notes), 2000)
        outline = create_outline(
            book_id=book["id"],
            content=outline_content,
            status="waiting_for_review",
        )
        update_book_status(book["id"], "waiting_for_review")
        return {
            "message": "Book created!",
            "book_id": book["id"],
            "outline_id": outline["id"],
            "outline": outline_content,
            "status": "waiting_for_review",
        }
    except Exception as exc:
        logger.error("Create book failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.get("")
async def list_books_route():
    try:
        return {"books": list_books()}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.get("/{book_id}")
async def get_book_route(book_id: str):
    try:
        book = get_book(book_id)
        if not book:
            raise HTTPException(404, "Book not found")
        return {"book": book, "outline": get_latest_outline(book_id)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.post("/{book_id}/feedback")
async def submit_outline_feedback(book_id: str, feedback: EditorFeedback):
    try:
        if feedback.status not in {"approved", "needs_revision"}:
            raise HTTPException(400, "Status must be 'approved' or 'needs_revision'")

        outline = get_latest_outline(book_id)
        if not outline:
            raise HTTPException(404, "Outline not found")

        book = get_book(book_id)
        if not book:
            raise HTTPException(404, "Book not found")

        if feedback.status == "approved":
            update_outline(
                outline["id"],
                status="approved",
                editor_notes=feedback.editor_notes,
            )
            update_book_status(book_id, "outline_approved")
            return {
                "message": "Outline approved!",
                "book_id": book_id,
                "status": "outline_approved",
                "next_step": f"Call POST /books/{book_id}/generate-chapter-stream",
            }

        update_outline(
            outline["id"],
            status="needs_revision",
            editor_notes=feedback.editor_notes,
        )
        new_content = call_ai(
            build_outline_prompt(book["title"], book["notes"], feedback.editor_notes),
            2000,
        )
        new_outline = create_outline(
            book_id=book_id,
            content=new_content,
            status="waiting_for_review",
        )
        update_book_status(book_id, "waiting_for_review")
        return {
            "message": "Outline regenerated!",
            "book_id": book_id,
            "outline_id": new_outline["id"],
            "new_outline": new_content,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.post("/{book_id}/generate-chapter-stream")
async def generate_chapter_stream(book_id: str):
    async def generate():
        try:
            book = get_book(book_id)
            if not book:
                yield _serialize_event({"type": "error", "message": "Book not found"})
                return

            if book["status"] not in {"outline_approved", "chapters_in_progress"}:
                yield _serialize_event(
                    {
                        "type": "error",
                        "message": f"Outline must be approved first. Status: {book['status']}",
                    }
                )
                return

            outline = get_approved_outline(book_id)
            if not outline:
                yield _serialize_event(
                    {"type": "error", "message": "No approved outline found"}
                )
                return

            pending_chapter = get_pending_review_chapter(book_id)
            if pending_chapter:
                yield _serialize_event(
                    {
                        "type": "error",
                        "message": f"Chapter {pending_chapter['chapter_number']} is waiting for review!",
                    }
                )
                return

            approved_chapters = get_approved_chapters(book_id)
            next_number = len(approved_chapters) + 1
            chapter_title = extract_chapter_title(outline["content"], next_number)
            previous_summaries = _build_previous_summaries(approved_chapters)

            yield _serialize_event(
                {
                    "type": "chapter_info",
                    "chapter_number": next_number,
                    "chapter_title": chapter_title,
                }
            )

            prompt = build_chapter_prompt(
                title=book["title"],
                outline=outline["content"],
                chapter_number=next_number,
                chapter_title=chapter_title,
                previous_summaries=previous_summaries,
            )
            full_content = ""

            async for chunk in stream_ai_async(prompt, max_tokens=3000):
                full_content += chunk
                yield _serialize_event({"type": "chunk", "text": chunk})

            chapter = create_chapter(
                book_id=book_id,
                chapter_number=next_number,
                content=full_content,
                status="waiting_for_review",
            )
            update_book_status(book_id, "chapters_in_progress")

            yield _serialize_event(
                {
                    "type": "done",
                    "chapter_id": chapter["id"],
                    "chapter_number": next_number,
                }
            )
        except Exception as exc:
            logger.error("Chapter stream error: %s", exc, exc_info=True)
            yield _serialize_event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{book_id}/generate-chapter")
async def generate_next_chapter(book_id: str):
    try:
        book = get_book(book_id)
        if not book:
            raise HTTPException(404, "Book not found")

        if book["status"] not in {"outline_approved", "chapters_in_progress"}:
            raise HTTPException(
                400, f"Outline must be approved first. Status: {book['status']}"
            )

        outline = get_approved_outline(book_id)
        if not outline:
            raise HTTPException(404, "No approved outline found")

        pending_chapter = get_pending_review_chapter(book_id)
        if pending_chapter:
            raise HTTPException(
                400,
                f"Chapter {pending_chapter['chapter_number']} is waiting for review!",
            )

        approved_chapters = get_approved_chapters(book_id)
        next_number = len(approved_chapters) + 1
        chapter_title = extract_chapter_title(outline["content"], next_number)
        previous_summaries = _build_previous_summaries(approved_chapters)
        content = call_ai(
            build_chapter_prompt(
                title=book["title"],
                outline=outline["content"],
                chapter_number=next_number,
                chapter_title=chapter_title,
                previous_summaries=previous_summaries,
            ),
            3000,
        )
        chapter = create_chapter(
            book_id=book_id,
            chapter_number=next_number,
            content=content,
            status="waiting_for_review",
        )
        update_book_status(book_id, "chapters_in_progress")
        return {
            "message": f"Chapter {next_number} generated!",
            "chapter_id": chapter["id"],
            "chapter_number": next_number,
            "content": content,
            "status": "waiting_for_review",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, str(exc))
