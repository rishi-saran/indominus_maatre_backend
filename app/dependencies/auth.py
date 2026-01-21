from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.core.supabase import supabase


def get_current_user(request: Request) -> dict:
    """
    Extracts and validates Supabase user from Authorization header
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    access_token = auth_header.replace("Bearer ", "").strip()

    try:
        user_response = supabase.auth.get_user(access_token)
        user = user_response.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "id": UUID(user.id),
            "email": user.email,
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )