from fastapi import APIRouter, Depends, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional

class AdminLiveStream(BaseModel):
    id: int
    title: str
    status: str
    scheduled_at: Optional[str]

router = APIRouter(prefix="/admin/live-streams", tags=["Admin Live Streams"])

@router.get("/", response_model=List[AdminLiveStream])
def list_live_streams(current_user=Depends(require_admin)):
    return []

@router.get("/{stream_id}", response_model=AdminLiveStream)
def get_live_stream(stream_id: int, current_user=Depends(require_admin)):
    return {"id": stream_id, "title": "Sample Stream", "status": "scheduled"}

@router.post("/", response_model=AdminLiveStream, status_code=status.HTTP_201_CREATED)
def create_live_stream(stream: AdminLiveStream, current_user=Depends(require_admin)):
    return stream

@router.put("/{stream_id}", response_model=AdminLiveStream)
def update_live_stream(stream_id: int, stream: AdminLiveStream, current_user=Depends(require_admin)):
    return stream

@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_live_stream(stream_id: int, current_user=Depends(require_admin)):
    return None
