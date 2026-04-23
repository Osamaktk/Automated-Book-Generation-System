from typing import Annotated

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel
from supabase import Client

from config import create_rls_client, logger, supabase


class AuthenticatedUser(BaseModel):
    """Authenticated user context derived from the Supabase access token."""

    user_id: str
    access_token: str


def _extract_bearer_token(request: Request) -> str:
    """Extract the bearer token from the Authorization header."""
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Missing or invalid Authorization header")
    return token


def _extract_user_id(user_response) -> str:
    """Normalize the Supabase auth response into a user id string."""
    user = getattr(user_response, "user", None)
    if user is None and isinstance(user_response, dict):
        user = user_response.get("user", user_response)

    user_id = getattr(user, "id", None)
    if user_id is None and isinstance(user, dict):
        user_id = user.get("id") or user.get("sub")

    if not user_id:
        raise HTTPException(401, "Unable to resolve Supabase user")
    return user_id


async def get_current_user(request: Request) -> AuthenticatedUser:
    """
    Validate the Supabase bearer token and return the authenticated user.

    The dependency raises 401 when the token is missing or invalid.
    """
    try:
        access_token = _extract_bearer_token(request)
        user_response = supabase.auth.get_user(access_token)
        user_id = _extract_user_id(user_response)
        return AuthenticatedUser(user_id=user_id, access_token=access_token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Authentication failed: %s", exc, exc_info=True)
        raise HTTPException(401, "Invalid or expired Supabase token")


async def get_optional_current_user(request: Request) -> AuthenticatedUser | None:
    """Return the authenticated user when present, otherwise None."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    return await get_current_user(request)


def get_user_supabase_client(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> Client:
    """Create an RLS-aware Supabase client for the authenticated user."""
    try:
        return create_rls_client(current_user.access_token)
    except Exception as exc:
        logger.error("User Supabase client creation failed: %s", exc, exc_info=True)
        raise HTTPException(500, "Unable to create Supabase client")


def get_public_supabase_client() -> Client:
    """Create an anon-key Supabase client for public share-token reads."""
    try:
        return create_rls_client()
    except Exception as exc:
        logger.error("Public Supabase client creation failed: %s", exc, exc_info=True)
        raise HTTPException(500, "Unable to create Supabase client")
