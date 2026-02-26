from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies.auth import require_admin
from app.core.supabase import supabase
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uuid
import bcrypt

router = APIRouter(prefix="/admin/onboarding-requests", tags=["Admin Onboarding"])

class OnboardingRequest(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str]
    password: str
    created_at: Optional[str]

class OnboardingRequestCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str]
    password: str
    retype_password: str

# In-memory fallback for onboarding requests (replace with DB table in production)
ONBOARDING_TABLE = "admin_onboarding_requests"

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_onboarding_request(req: OnboardingRequestCreate, current_user=Depends(require_admin)):
    if req.password != req.retype_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    # Check for existing pending request
    existing = supabase.table(ONBOARDING_TABLE).select("id").eq("email", req.email).execute().data
    if existing:
        raise HTTPException(status_code=400, detail="Onboarding request already exists for this email.")
    # Store hashed password
    hashed_pw = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    entry = {
        "id": str(uuid.uuid4()),
        "first_name": req.first_name,
        "last_name": req.last_name,
        "email": req.email,
        "phone": req.phone,
        "password": hashed_pw,
        "created_at": None
    }
    supabase.table(ONBOARDING_TABLE).insert(entry).execute()
    return {"success": True}

@router.get("/", response_model=List[OnboardingRequest])
def list_onboarding_requests(current_user=Depends(require_admin)):
    data = supabase.table(ONBOARDING_TABLE).select("*").execute().data or []
    return data

@router.post("/{request_id}/approve")
def approve_onboarding_request(request_id: str, current_user=Depends(require_admin)):
    reqs = supabase.table(ONBOARDING_TABLE).select("*").eq("id", request_id).execute().data
    if not reqs:
        raise HTTPException(status_code=404, detail="Request not found.")
    req = reqs[0]
    # Create user in users table
    user_entry = {
        "id": str(uuid.uuid4()),
        "email": req["email"],
        "first_name": req["first_name"],
        "last_name": req["last_name"],
        "phone": req.get("phone"),
        "is_active": True,
        "role": "priest"
    }
    supabase.table("users").insert(user_entry).execute()
    # Create profile
    profile_entry = {
        "id": user_entry["id"],
        "role": "priest"
    }
    supabase.table("profiles").insert(profile_entry).execute()
    # Remove onboarding request
    supabase.table(ONBOARDING_TABLE).delete().eq("id", request_id).execute()
    return {"success": True}

@router.post("/{request_id}/reject")
def reject_onboarding_request(request_id: str, current_user=Depends(require_admin)):
    supabase.table(ONBOARDING_TABLE).delete().eq("id", request_id).execute()
    return {"success": True}
