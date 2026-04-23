import json
import os
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from supabase import Client

from ai import call_ai, stream_ai_async
from config import create_rls_client, logger
from database import (
    create_book,
    create_book_share,
    create_chapter,
    create_outline,
    get_approved_chapters,
    get_approved_outline,
    get_book,
    get_book_share_by_token,
    get_latest_outline,
    get_pending_review_chapter,
    list_books,
    update_book_status,
    update_outline,
)
from models import BookInput, EditorFeedback, ShareUserInput
from prompts import build_chapter_prompt, build_outline_prompt, extract_chapter_title
from services.auth import AuthenticatedUser, get_current_user, get_optional_current_user
from services.compiler import compile_to_docx, compile_to_pdf
from services.notifications import notify


router = APIRouter(prefix="/books", tags=["books"])


def _serialize_event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _build_previous_summaries(approved_chapters: list[dict]) -> list[dict]:
    return [
        {"chapter_number": chapter["chapter_number"], "summary": chapter["summary"]}
        for chapter in approved_chapters
        if chapter.get("summary")
    ]


def _build_user_client(current_user: AuthenticatedUser) -> Client:
    """Create a request-scoped Supabase client for the authenticated user."""
    return create_rls_client(current_user.access_token)


def _require_owner(book: dict, current_user: AuthenticatedUser) -> None:
    """Ensure the authenticated user owns the target book."""
    if book.get("user_id") != current_user.user_id:
        raise HTTPException(403, "Only the book owner can perform this action")


def _resolve_book_read_access(
    book_id: str,
    current_user: AuthenticatedUser | None,
    share: str | None = None,
) -> tuple[dict, Client]:
    """Resolve read access for an owner/shared user or a public share token."""
    if share:
        public_client = create_rls_client()
        share_row = get_book_share_by_token(book_id, share, client=public_client)
        if not share_row:
            raise HTTPException(404, "Share link not found")
        book = get_book(book_id, client=public_client)
        if not book:
            raise HTTPException(404, "Book not found")
        return book, public_client

    if not current_user:
        raise HTTPException(401, "Authentication required")

    user_client = _build_user_client(current_user)
    book = get_book(book_id, client=user_client)
    if not book:
        raise HTTPException(404, "Book not found")
    return book, user_client


def _generate_next_chapter_for_book(book: dict, client: Client) -> dict:
    """Generate the next chapter for a visible book using the caller's RLS client."""
    if book["status"] not in {"outline_approved", "chapters_in_progress"}:
        raise HTTPException(
            400, f"Outline must be approved first. Status: {book['status']}"
        )

    outline = get_approved_outline(book["id"], client=client)
    if not outline:
        raise HTTPException(404, "No approved outline found")

    pending_chapter = get_pending_review_chapter(book["id"], client=client)
    if pending_chapter:
        raise HTTPException(
            400,
            f"Chapter {pending_chapter['chapter_number']} is waiting for review!",
        )

    approved_chapters = get_approved_chapters(book["id"], client=client)
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
        book_id=book["id"],
        chapter_number=next_number,
        content=content,
        status="waiting_for_review",
        client=client,
    )
    notify(
        "chapter_ready",
        book["title"],
        f"Chapter {next_number} is ready for review",
    )
    update_book_status(book["id"], "chapters_in_progress", client=client)
    return {
        "message": f"Chapter {next_number} generated!",
        "chapter_id": chapter["id"],
        "chapter_number": next_number,
        "content": content,
        "status": "waiting_for_review",
    }


@router.post("/create-stream")
async def create_book_stream(
    input: BookInput,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    async def generate():
        try:
            user_client = _build_user_client(current_user)
            book = create_book(
                input.title,
                input.notes,
                current_user.user_id,
                status="generating",
                client=user_client,
            )
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
                client=user_client,
            )
            notify("outline_ready", book["title"], f"Book ID: {book_id}")
            update_book_status(book_id, "waiting_for_review", client=user_client)

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
async def create_book_route(
    input: BookInput,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        book = create_book(
            input.title,
            input.notes,
            current_user.user_id,
            status="generating",
            client=user_client,
        )
        outline_content = call_ai(build_outline_prompt(input.title, input.notes), 2000)
        outline = create_outline(
            book_id=book["id"],
            content=outline_content,
            status="waiting_for_review",
            client=user_client,
        )
        notify("outline_ready", book["title"], f"Book ID: {book['id']}")
        update_book_status(book["id"], "waiting_for_review", client=user_client)
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
async def list_books_route(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        return {"books": list_books(client=user_client)}
    except Exception as exc:
        logger.error("List books failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.get("/{book_id}")
async def get_book_route(
    book_id: str,
    share: str | None = None,
    current_user: AuthenticatedUser | None = Depends(get_optional_current_user),
):
    try:
        book, client = _resolve_book_read_access(book_id, current_user, share)
        return {"book": book, "outline": get_latest_outline(book_id, client=client)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Get book failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.delete("/{book_id}")
async def delete_book_route(
    book_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        book = get_book(book_id, client=user_client)
        if not book:
            raise HTTPException(404, "Book not found")
        _require_owner(book, current_user)

        chapters = (
            user_client.table("chapters").select("id").eq("book_id", book_id).execute().data
            or []
        )
        outlines = (
            user_client.table("outlines").select("id").eq("book_id", book_id).execute().data
            or []
        )

        chapters_deleted = len(chapters)
        outlines_deleted = len(outlines)

        if chapters_deleted:
            user_client.table("chapters").delete().eq("book_id", book_id).execute()

        if outlines_deleted:
            user_client.table("outlines").delete().eq("book_id", book_id).execute()

        user_client.table("books").delete().eq("id", book_id).execute()

        logger.info(
            "Deleted book %s with %s chapters and %s outlines",
            book_id,
            chapters_deleted,
            outlines_deleted,
        )
        return {
            "message": "Book deleted successfully",
            "book_id": book_id,
            "chapters_deleted": chapters_deleted,
            "outlines_deleted": outlines_deleted,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Delete book failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.post("/{book_id}/feedback")
async def submit_outline_feedback(
    book_id: str,
    feedback: EditorFeedback,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        if feedback.status not in {"approved", "needs_revision"}:
            raise HTTPException(400, "Status must be 'approved' or 'needs_revision'")

        outline = get_latest_outline(book_id, client=user_client)
        if not outline:
            raise HTTPException(404, "Outline not found")

        book = get_book(book_id, client=user_client)
        if not book:
            raise HTTPException(404, "Book not found")
        _require_owner(book, current_user)

        if feedback.status == "approved":
            update_outline(
                outline["id"],
                client=user_client,
                status="approved",
                editor_notes=feedback.editor_notes,
            )
            update_book_status(book_id, "outline_approved", client=user_client)
            first_chapter = _generate_next_chapter_for_book(
                {**book, "status": "outline_approved"},
                user_client,
            )
            return {
                "message": "Outline approved and first chapter generated!",
                "book_id": book_id,
                "status": "chapters_in_progress",
                "chapter_id": first_chapter["chapter_id"],
                "chapter_number": first_chapter["chapter_number"],
                "next_step": f"Review Chapter {first_chapter['chapter_number']}",
            }

        update_outline(
            outline["id"],
            client=user_client,
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
            client=user_client,
        )
        notify("outline_ready", book["title"], f"Book ID: {book_id}")
        update_book_status(book_id, "waiting_for_review", client=user_client)
        return {
            "message": "Outline regenerated!",
            "book_id": book_id,
            "outline_id": new_outline["id"],
            "new_outline": new_content,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Outline feedback failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.get("/{book_id}/compile")
async def compile_book_route(
    book_id: str,
    format: str = "docx",
    share: str | None = None,
    current_user: AuthenticatedUser | None = Depends(get_optional_current_user),
):
    try:
        if format not in {"docx", "pdf", "txt"}:
            raise HTTPException(400, "Format must be one of: docx, pdf, txt")

        book, client = _resolve_book_read_access(book_id, current_user, share)

        outline = get_latest_outline(book_id, client=client)
        if not outline:
            raise HTTPException(404, "Outline not found")

        chapters = (
            client.table("chapters").select("*").eq("book_id", book_id).execute().data or []
        )
        approved_chapters = sorted(
            [chapter for chapter in chapters if chapter["status"] == "approved"],
            key=lambda chapter: chapter["chapter_number"],
        )
        if not approved_chapters:
            raise HTTPException(400, "No approved chapters found to compile")

        slug = (
            re.sub(
                r"-+",
                "-",
                re.sub(r"[^a-z0-9]+", "-", book["title"].lower()),
            ).strip("-")
            or "book"
        )
        headers = {
            "Content-Disposition": f'attachment; filename="{slug}_{book_id[:8]}.{format}"'
        }

        if format == "docx":
            content = compile_to_docx(book, outline, approved_chapters)
            logger.info("Compiled DOCX document for book %s", book_id)
            return StreamingResponse(
                iter([content]),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers=headers,
            )

        if format == "pdf":
            content = compile_to_pdf(book, outline, approved_chapters)
            logger.info("Compiled PDF document for book %s", book_id)
            return StreamingResponse(
                iter([content]),
                media_type="application/pdf",
                headers=headers,
            )

        compiled_sections = [book["title"].strip()]

        if book.get("notes"):
            compiled_sections.extend(["", "Author Notes", book["notes"].strip()])

        if outline.get("content"):
            compiled_sections.extend(["", "Outline", outline["content"].strip()])

        for chapter in approved_chapters:
            chapter_title = extract_chapter_title(
                outline.get("content", ""), chapter["chapter_number"]
            )
            compiled_sections.extend(
                [
                    "",
                    f"Chapter {chapter['chapter_number']} - {chapter_title}",
                    chapter["content"].strip(),
                ]
            )
            if chapter.get("summary"):
                compiled_sections.extend(["", f"Summary: {chapter['summary'].strip()}"])

        content = "\n".join(compiled_sections).strip().encode("utf-8")
        logger.info("Compiled TXT document for book %s", book_id)
        return StreamingResponse(
            iter([content]),
            media_type="text/plain",
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Compile book failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.post("/{book_id}/generate-chapter-stream")
async def generate_chapter_stream(
    book_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    async def generate():
        try:
            user_client = _build_user_client(current_user)
            book = get_book(book_id, client=user_client)
            if not book:
                yield _serialize_event({"type": "error", "message": "Book not found"})
                return
            _require_owner(book, current_user)

            if book["status"] not in {"outline_approved", "chapters_in_progress"}:
                yield _serialize_event(
                    {
                        "type": "error",
                        "message": f"Outline must be approved first. Status: {book['status']}",
                    }
                )
                return

            outline = get_approved_outline(book_id, client=user_client)
            if not outline:
                yield _serialize_event(
                    {"type": "error", "message": "No approved outline found"}
                )
                return

            pending_chapter = get_pending_review_chapter(book_id, client=user_client)
            if pending_chapter:
                yield _serialize_event(
                    {
                        "type": "error",
                        "message": f"Chapter {pending_chapter['chapter_number']} is waiting for review!",
                    }
                )
                return

            approved_chapters = get_approved_chapters(book_id, client=user_client)
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
                client=user_client,
            )
            notify(
                "chapter_ready",
                book["title"],
                f"Chapter {next_number} is ready for review",
            )
            update_book_status(book_id, "chapters_in_progress", client=user_client)

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
async def generate_next_chapter(
    book_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        book = get_book(book_id, client=user_client)
        if not book:
            raise HTTPException(404, "Book not found")
        _require_owner(book, current_user)
        return _generate_next_chapter_for_book(book, user_client)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Generate chapter failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.post("/{book_id}/share/user")
async def share_book_with_user(
    book_id: str,
    share_input: ShareUserInput,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        book = get_book(book_id, client=user_client)
        if not book:
            raise HTTPException(404, "Book not found")
        _require_owner(book, current_user)

        share = create_book_share(
            book_id=book_id,
            shared_by=current_user.user_id,
            shared_with=share_input.shared_with,
            client=user_client,
        )
        return {
            "message": "Book shared successfully",
            "book_id": book_id,
            "shared_with": share["shared_with"],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Share with user failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))


@router.post("/{book_id}/share/link")
async def share_book_with_link(
    book_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        user_client = _build_user_client(current_user)
        book = get_book(book_id, client=user_client)
        if not book:
            raise HTTPException(404, "Book not found")
        _require_owner(book, current_user)

        share_token = secrets.token_urlsafe(24)
        create_book_share(
            book_id=book_id,
            shared_by=current_user.user_id,
            share_token=share_token,
            client=user_client,
        )
        frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
        share_url = (
            f"{frontend_url}/?book={book_id}&share={share_token}"
            if frontend_url
            else f"?book={book_id}&share={share_token}"
        )
        return {
            "message": "Share link created successfully",
            "book_id": book_id,
            "share_token": share_token,
            "share_url": share_url,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Share link creation failed: %s", exc, exc_info=True)
        raise HTTPException(500, str(exc))
