from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import require_admin
from app.core.supabase import supabase, get_service_role_client
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uuid

router = APIRouter(prefix="/admin/onboarding-requests", tags=["Admin Onboarding"])

class OnboardingRequest(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str]
    plain_password: str
    created_at: Optional[str]

class OnboardingRequestCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str]
    plain_password: str

# In-memory fallback for onboarding requests (replace with DB table in production)
ONBOARDING_TABLE = "priest_onboarding_requests"

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_onboarding_request(req: OnboardingRequestCreate, current_user=Depends(require_admin)):
    # Check for existing pending request
    existing = supabase.table(ONBOARDING_TABLE).select("id").eq("email", req.email).execute().data
    if existing:
        raise HTTPException(status_code=400, detail="Onboarding request already exists for this email.")
    entry = {
        "id": str(uuid.uuid4()),
        "first_name": req.first_name,
        "last_name": req.last_name,
        "email": req.email,
        "phone": req.phone,
        "plain_password": req.plain_password,
        "created_at": None
    }
    supabase.table(ONBOARDING_TABLE).insert(entry).execute()
    return {"success": True}

@router.get("/", response_model=List[OnboardingRequest])
def list_onboarding_requests(current_user=Depends(require_admin)):
    try:
        data = supabase.table(ONBOARDING_TABLE).select("*").execute().data
        if data is None:
            return []
        return data
    except Exception:
        # Always return 200 OK with empty array if table missing or error
        return []

@router.post("/{request_id}/approve")
def approve_onboarding_request(request_id: str, current_user=Depends(require_admin)):
    reqs = supabase.table(ONBOARDING_TABLE).select("*").eq("id", request_id).execute().data
    if not reqs:
        raise HTTPException(status_code=404, detail="Request not found.")
    req = reqs[0]

    # Use plain password for Supabase Auth
    # You must store the plain password in onboarding table, not the hashed one
    # If you stored only the hash, you cannot create the Supabase Auth user
    # For now, let's assume you store the plain password in a new field 'plain_password'
    plain_password = req.get("plain_password") or None
    if not plain_password:
        raise HTTPException(status_code=400, detail="Plain password not found in onboarding request. Store plain password for approval.")

    # Create user in Supabase Auth (service-role admin API, no sign_in/sign_up session mutation)
    try:
        admin_client = get_service_role_client()
        auth_result = admin_client.auth.admin.create_user({
            "email": req["email"],
            "password": plain_password,
            "email_confirm": True,
            "user_metadata": {"role": "priest"},
        })
        user = auth_result.user
        if not user:
            raise Exception("Supabase Auth user creation failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Supabase Auth error: {str(e)}")

    # Upsert user in users table (use Supabase Auth UUID)
    user_entry = {
        "id": user.id,
        "email": req["email"],
        "first_name": req.get("first_name", ""),
        "last_name": req.get("last_name", ""),
        "phone": req.get("phone", None),
        "is_active": True,
        "role": "priest"
    }
    existing_user = supabase.table("users").select("id").eq("id", user.id).execute().data
    if existing_user:
        user_resp = supabase.table("users").update(user_entry).eq("id", user.id).execute()
    else:
        user_resp = supabase.table("users").insert(user_entry).execute()
    if getattr(user_resp, "error", None):
        raise HTTPException(status_code=500, detail=f"Failed to upsert user: {user_resp.error}")

    # Upsert profile
    profile_entry = {
        "id": user.id,
        "role": "priest"
    }
    existing_profile = supabase.table("profiles").select("id").eq("id", user.id).execute().data
    if existing_profile:
        profile_resp = supabase.table("profiles").update(profile_entry).eq("id", user.id).execute()
    else:
        profile_resp = supabase.table("profiles").insert(profile_entry).execute()
    if getattr(profile_resp, "error", None):
        raise HTTPException(status_code=500, detail=f"Failed to upsert profile: {profile_resp.error}")

    # Remove onboarding request only after successful upserts
    supabase.table(ONBOARDING_TABLE).delete().eq("id", request_id).execute()
    return {"success": True}

@router.post("/{request_id}/reject")
def reject_onboarding_request(request_id: str, current_user=Depends(require_admin)):
    supabase.table(ONBOARDING_TABLE).delete().eq("id", request_id).execute()
    return {"success": True}
