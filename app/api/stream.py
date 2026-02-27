from fastapi import APIRouter, Depends
from app.services.stream_service import StreamService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/stream", tags=["Stream"])

@router.get("/token")
def get_stream_token(current_user=Depends(get_current_user)):
    token = StreamService.generate_token(str(current_user["id"]))
    return {"token": token}