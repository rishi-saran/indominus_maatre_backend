from fastapi import APIRouter, HTTPException
from app.core.supabase import supabase
from app.schemas.page import PageResponse

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


