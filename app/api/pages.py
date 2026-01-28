from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional

from app.core.supabase import supabase
from app.schemas.page import (
    PageResponse,
    PageListResponse,
    PageCreateRequest,
    PageUpdateRequest,
)
from app.dependencies.auth import require_admin

router = APIRouter(
    prefix="/pages",
    tags=["Pages"] 
)

@router.get("/{slug}", response_model=PageResponse)
def get_page_by_slug(slug: str):
    response = (
        supabase
        .table("pages")
        .select("*")
        .eq("slug", slug)
        .single()
        .execute()
    ) # no need to check for published == true, since its RLS protected
    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Page not found"
        )
    return response.data

# list all/specific pages -> work for both /pages and /pages?type=service
@router.get("", response_model=PageListResponse)
def list_pages(type: Optional[str] = None):
    query = (
        supabase
        .table("pages")
        .select("slug, title, type")
        .eq("published", True)
    )

    if type: #conditional rendering for query params (i.e /pages?type=service)
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

    response = (
        supabase
        .table("pages")
        .insert(payload.dict())
        .execute()
    )

    return response.data[0]

@router.put(
    "/{slug}",
    response_model=PageResponse,
)
def update_page(
    slug: str,
    payload: PageUpdateRequest,
    current_user: dict = Depends(require_admin),
):
    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

    response = (
        supabase
        .table("pages")
        .update(update_data)
        .eq("slug", slug)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Page not found")

    return response.data[0]
