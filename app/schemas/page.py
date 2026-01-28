from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
from typing import Optional

class PageSection(BaseModel):
    key: str
    title: str
    delta: Dict[str, Any] #since QUILL DELTA is flexible, over validation thevai illai


class PageContent(BaseModel):
    sections: List[PageSection]

class PageResponse(BaseModel):
    id: UUID
    slug: str #this is the unique identifier -> GET /api/pages/{slug}
    title: str # free text, for title
    type: str # meant to be enum, but kept as str for testing purposes
    content: PageContent #jsonb
    published: bool #only published pages can be accessed(RLS enabled)
    created_at: datetime

class PageListItem(BaseModel): # for query params
    slug: str
    title: str
    type: str
# eg: GET /pages?type=service

class PageListResponse(BaseModel):
    items: List[PageListItem]

class PageCreateRequest(BaseModel):
    slug: str
    title: str
    type: str
    content: Dict[str, Any]  
    published: bool = False

class PageUpdateRequest(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    published: Optional[bool] = None
