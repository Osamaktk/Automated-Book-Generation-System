from supabase import Client

from config import supabase


def create_book(
    title: str,
    notes: str,
    user_id: str,
    status: str = "generating",
    client: Client = supabase,
) -> dict:
    """Insert a new book owned by the authenticated user."""
    result = (
        client.table("books")
        .insert({"title": title, "notes": notes, "user_id": user_id, "status": status})
        .execute()
    )
    return result.data[0]


def get_book(book_id: str, client: Client = supabase) -> dict | None:
    """Fetch a single book visible to the current caller."""
    result = client.table("books").select("*").eq("id", book_id).execute()
    return result.data[0] if result.data else None


def list_books(client: Client = supabase) -> list[dict]:
    """List all books visible to the current caller under RLS."""
    result = client.table("books").select("*").order("created_at", desc=True).execute()
    return result.data


def update_book_status(book_id: str, status: str, client: Client = supabase):
    """Update the status for a book visible to the current caller."""
    client.table("books").update({"status": status}).eq("id", book_id).execute()


def create_outline(
    book_id: str,
    content: str,
    status: str,
    editor_notes: str = "",
    client: Client = supabase,
) -> dict:
    """Insert a new outline for a book visible to the current caller."""
    payload = {
        "book_id": book_id,
        "content": content,
        "status": status,
        "editor_notes": editor_notes,
    }
    result = client.table("outlines").insert(payload).execute()
    return result.data[0]


def get_latest_outline(book_id: str, client: Client = supabase) -> dict | None:
    """Fetch the latest outline visible to the current caller."""
    result = (
        client.table("outlines")
        .select("*")
        .eq("book_id", book_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_approved_outline(book_id: str, client: Client = supabase) -> dict | None:
    """Fetch the approved outline visible to the current caller."""
    result = (
        client.table("outlines")
        .select("*")
        .eq("book_id", book_id)
        .eq("status", "approved")
        .execute()
    )
    return result.data[0] if result.data else None


def update_outline(outline_id: str, client: Client = supabase, **fields):
    """Update an outline visible to the current caller."""
    client.table("outlines").update(fields).eq("id", outline_id).execute()


def create_chapter(
    book_id: str,
    chapter_number: int,
    content: str,
    status: str,
    client: Client = supabase,
) -> dict:
    """Insert a new chapter for a book visible to the current caller."""
    result = (
        client.table("chapters")
        .insert(
            {
                "book_id": book_id,
                "chapter_number": chapter_number,
                "content": content,
                "status": status,
            }
        )
        .execute()
    )
    return result.data[0]


def get_chapter(chapter_id: str, client: Client = supabase) -> dict | None:
    """Fetch a single chapter visible to the current caller."""
    result = client.table("chapters").select("*").eq("id", chapter_id).execute()
    return result.data[0] if result.data else None


def get_book_chapter(
    chapter_id: str,
    book_id: str,
    client: Client = supabase,
) -> dict | None:
    """Fetch a chapter by id constrained to a specific parent book."""
    result = (
        client.table("chapters")
        .select("*")
        .eq("id", chapter_id)
        .eq("book_id", book_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def list_book_chapters(book_id: str, client: Client = supabase) -> list[dict]:
    """List chapters for a visible book in chapter order."""
    result = (
        client.table("chapters")
        .select("id, chapter_number, status, editor_notes, created_at")
        .eq("book_id", book_id)
        .order("chapter_number")
        .execute()
    )
    return result.data


def get_pending_review_chapter(book_id: str, client: Client = supabase) -> dict | None:
    """Fetch the pending review chapter visible to the current caller."""
    result = (
        client.table("chapters")
        .select("*")
        .eq("book_id", book_id)
        .eq("status", "waiting_for_review")
        .execute()
    )
    return result.data[0] if result.data else None


def get_approved_chapters(book_id: str, client: Client = supabase) -> list[dict]:
    """Fetch all approved chapters visible to the current caller."""
    result = (
        client.table("chapters")
        .select("*")
        .eq("book_id", book_id)
        .eq("status", "approved")
        .order("chapter_number")
        .execute()
    )
    return result.data


def update_chapter(chapter_id: str, client: Client = supabase, **fields):
    """Update a chapter visible to the current caller."""
    client.table("chapters").update(fields).eq("id", chapter_id).execute()


def create_book_share(
    book_id: str,
    shared_by: str,
    shared_with: str | None = None,
    share_token: str | None = None,
    can_view: bool = True,
    client: Client = supabase,
) -> dict:
    """Insert a share row for a visible book."""
    payload = {
        "book_id": book_id,
        "shared_by": shared_by,
        "shared_with": shared_with,
        "share_token": share_token,
        "can_view": can_view,
    }
    result = client.table("book_shares").insert(payload).execute()
    return result.data[0]


def get_book_share_by_token(
    book_id: str,
    share_token: str,
    client: Client = supabase,
) -> dict | None:
    """Fetch a share row for a specific book/token pair."""
    result = (
        client.table("book_shares")
        .select("*")
        .eq("book_id", book_id)
        .eq("share_token", share_token)
        .eq("can_view", True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_share_by_token(share_token: str, client: Client = supabase) -> dict | None:
    """Fetch a share row by token for public share-link access."""
    result = (
        client.table("book_shares")
        .select("*")
        .eq("share_token", share_token)
        .eq("can_view", True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
