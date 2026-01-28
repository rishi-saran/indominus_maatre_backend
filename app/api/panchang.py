from fastapi import APIRouter, HTTPException
from app.schemas.panchang import PanchangRequest
from app.services.panchang_service import get_advanced_panchang

router = APIRouter(prefix="/panchang", tags=["Panchang"])

@router.post("/")
async def get_panchang(payload: PanchangRequest):
    try:
        data = await get_advanced_panchang(
            payload.date,
            payload.coordinates
        )
        return {
            "date": payload.date,
            "location": payload.location,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
