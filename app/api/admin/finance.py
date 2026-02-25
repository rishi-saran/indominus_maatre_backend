from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import require_admin
from pydantic import BaseModel
from typing import List, Optional

class AdminFinanceRecord(BaseModel):
    id: int
    booking_id: int
    amount: float
    status: str
    created_at: Optional[str]

router = APIRouter(prefix="/admin/finance", tags=["Admin Finance"])

@router.get("/", response_model=List[AdminFinanceRecord])
def list_finance_records(current_user=Depends(require_admin)):
    return []

@router.get("/{record_id}", response_model=AdminFinanceRecord)
def get_finance_record(record_id: int, current_user=Depends(require_admin)):
    return {"id": record_id, "booking_id": 1, "amount": 0.0, "status": "pending"}

@router.post("/", response_model=AdminFinanceRecord, status_code=status.HTTP_201_CREATED)
def create_finance_record(record: AdminFinanceRecord, current_user=Depends(require_admin)):
    return record

@router.put("/{record_id}", response_model=AdminFinanceRecord)
def update_finance_record(record_id: int, record: AdminFinanceRecord, current_user=Depends(require_admin)):
    return record

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finance_record(record_id: int, current_user=Depends(require_admin)):
    return None
