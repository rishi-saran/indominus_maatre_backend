from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional

class AdminBooking(BaseModel):
    id: int
    user_id: int
    service_id: int
    status: str
    created_at: Optional[str]

router = APIRouter(prefix="/admin/bookings", tags=["Admin Bookings"])

@router.get("/", response_model=List[AdminBooking])
def list_bookings(current_user=Depends(require_admin)):
    return []

@router.get("/{booking_id}", response_model=AdminBooking)
def get_booking(booking_id: int, current_user=Depends(require_admin)):
    return {"id": booking_id, "user_id": 1, "service_id": 1, "status": "pending"}

@router.post("/", response_model=AdminBooking, status_code=status.HTTP_201_CREATED)
def create_booking(booking: AdminBooking, current_user=Depends(require_admin)):
    return booking

@router.put("/{booking_id}", response_model=AdminBooking)
def update_booking(booking_id: int, booking: AdminBooking, current_user=Depends(require_admin)):
    return booking

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, current_user=Depends(require_admin)):
    return None
