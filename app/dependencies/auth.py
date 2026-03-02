import logging
from urllib.parse import urlparse
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.core.supabase import SUPABASE_URL, get_anon_client, get_service_role_client


logger = logging.getLogger("app.auth")


def _supabase_project_ref() -> str:
    try:
        hostname = (urlparse(SUPABASE_URL).hostname or "").strip()
        return hostname.split(".")[0] if hostname else "unknown"
    except Exception:
        return "unknown"


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
        auth_client = get_anon_client()
        user_response = auth_client.auth.get_user(access_token)
        user = user_response.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        logger.warning(
            "auth.get_user success: path=%s method=%s token_user_id=%s token_user_email=%s supabase_project_ref=%s",
            request.url.path,
            request.method,
            user.id,
            user.email,
            _supabase_project_ref(),
        )

        return {
            "id": UUID(user.id),
            "email": user.email,
        }

    except Exception as exc:
        logger.warning(
            "auth.get_user failed: path=%s method=%s reason=%s supabase_project_ref=%s",
            request.url.path,
            request.method,
            str(exc),
            _supabase_project_ref(),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

def require_admin(request: Request, user: dict = Depends(get_current_user)) -> dict:
    """
    Allows access only if user.role === 'admin'
    """

    try:
        lookup_user_id = str(user["id"])
        admin_client = get_service_role_client()
        logger.warning(
            "require_admin lookup start: path=%s method=%s schema=public table=users filter=id.eq.%s supabase_project_ref=%s",
            request.url.path,
            request.method,
            lookup_user_id,
            _supabase_project_ref(),
        )

        response = (
            admin_client
            .table("users")
            .select("id, role")
            .eq("id", lookup_user_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.warning(
            "require_admin lookup error: path=%s method=%s schema=public table=users filter=id.eq.%s reason=%s",
            request.url.path,
            request.method,
            str(user.get("id")),
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to validate admin user",
        )

    rows = response.data or []
    logger.warning(
        "require_admin lookup result: path=%s method=%s filter_id=%s row_count=%s role=%s",
        request.url.path,
        request.method,
        str(user["id"]),
        len(rows),
        rows[0].get("role") if rows else None,
    )

    if not rows:
        logger.warning(
            "require_admin no row: schema=public table=users filter=id.eq.%s returning=403",
            str(user["id"]),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with id {user['id']} not found in users table. Ensure admin user exists and UUID matches Supabase Auth.",
        )

    if rows[0].get("role") != "admin":
        logger.warning(
            "require_admin non-admin role: user_id=%s role=%s returning=403",
            str(user["id"]),
            rows[0].get("role"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    logger.warning(
        "require_admin granted: user_id=%s role=%s path=%s",
        str(user["id"]),
        rows[0].get("role"),
        request.url.path,
    )

    return user

