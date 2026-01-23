from fastapi import APIRouter, HTTPException
from app.core.supabase import supabase
from app.schemas.page import PageResponse, PageListResponse, PageListItem
from typing import Optional

router = APIRouter(
    prefix="/pages",
    tags=["Pages"] # for swagger
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
