from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional

from app.core.supabase import supabase
from app.schemas.page import (
    PageResponse,
    PageListResponse,
    PageCreateRequest,
    PageUpdateRequest,
)
from app.dependencies.auth import get_current_user, require_admin

router = APIRouter(
    prefix="/pages",
    tags=["Pages"],
)

@router.get("/{slug}", response_model=PageResponse)
def get_page_by_slug(slug: str):
    response = (
        supabase
        .table("pages")
        .select("*")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Page not found")

    return response.data[0]


@router.get("", response_model=PageListResponse)
def list_pages(
    type: Optional[str] = None,
    current_user: Optional[dict] = Depends(get_current_user),
):
    query = (
        supabase
        .table("pages")
        .select("slug, title, type, published")
    )

    if not current_user or current_user.get("role") != "admin":
        query = query.eq("published", True)

    if type:
        query = query.eq("type", type)

    response = query.execute()

    return {
        "items": response.data or []
    }

@router.post(
    "",
    response_model=PageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_page(
    payload: PageCreateRequest,
    current_user: dict = Depends(require_admin),
):
    # Check slug uniqueness
    existing = (
        supabase
        .table("pages")
        .select("id")
        .eq("slug", payload.slug)
        .limit(1)
        .execute()
    )

    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="Page with this slug already exists",
        )

    data = {
        "slug": payload.slug,
        "title": payload.title,
        "type": payload.type,
        "published": payload.published,
        "content": {
            "sections": [
                {
                    "key": "main",
                    "title": payload.title,   # REQUIRED by schema
                    "delta": payload.content, # raw Quill delta
                }
            ]
        },
    }

    response = (
        supabase
        .table("pages")
        .insert(data)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create page")

    return response.data[0]


@router.put("/{slug}")
def update_page(
    slug: str,
    payload: PageUpdateRequest,
    current_user: dict = Depends(require_admin),
):
    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    if "content" in update_data:
        update_data["content"] = {
            "sections": [
                {
                    "key": "main",
                    "title": update_data.get("title", "Content"),
                    "delta": update_data["content"],  # <-- RAW QUILL DELTA ONLY
                }
            ]
        }

    supabase.table("pages").update(update_data).eq("slug", slug).execute()

    return {"success": True}

