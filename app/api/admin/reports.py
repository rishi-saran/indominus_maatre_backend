from fastapi import APIRouter, Depends
from app.dependencies.auth import require_admin

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])

@router.get("/summary")
def get_reports_summary(current_user=Depends(require_admin)):
    return {"message": "Reports summary placeholder"}
