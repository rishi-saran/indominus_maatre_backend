# /app/api/one_on_one_session.py
from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user, require_admin
from app.schemas.one_on_one_session import (
    SessionLifecycle,
    DirectSessionResponse ,
    DirectSessionListResponse, 
    PreDirectSessionRequest, 
    PreDirectSessionResponse,
    DirectSessionUpdate
)
from app.services.one_on_one_sessions_service import assign_priest

router = APIRouter(prefix="/sessions", tags=["1 on 1 Sessions"])

@router.post(
    "/request-session", 
    status_code=status.HTTP_200_OK,
    response_model=PreDirectSessionResponse
)
def request_one_on_one_session(
    request: PreDirectSessionRequest, 
    current_user : dict = Depends(get_current_user)
):  
    session_data = {
        "start_time":request.start_time.isoformat(),
        "end_time":request.end_time.isoformat(),
        "customer_id":str(current_user["id"]),
        "status": SessionLifecycle.requested.value
    }
    response = (
        supabase
        .table("sessions")
        .insert(session_data)
        .execute()
    )
    if not response:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail = "Failed to create a session")
    
    return response.data[0]

@router.get(
    "/list-all", 
    status_code=status.HTTP_200_OK,
    response_model= DirectSessionListResponse
)
def list_all_one_on_one_session(current_user: dict = Depends(require_admin)):
    
    query = (
        supabase
        .table("sessions")
        .select("*")
    )

    response = query.execute()
    return {"items":response.data}

@router.put(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    response_model=DirectSessionResponse
)
def approve_direct_session_request(
    session_id: UUID, 
    current_user: dict = Depends(require_admin)
): 
    session_res = (
        supabase
        .table("sessions")
        .select("*")
        .eq("id", str(session_id))
        .single()
        .execute()
    )
    session = session_res.data

    if not session or session["status"] != "requested":
        raise HTTPException(400, "Session not approvable")
    
    priest_id = assign_priest(
        session["start_time"],
        session["end_time"]
    )
    
    update_priest = (
        supabase
        .table("priest_availability")
        .update({
            "last_assigned_at": session["start_time"]
        })
        .eq("priest_id", str(priest_id))
        .execute()
    )
    

    update_res = (
        supabase
        .table("sessions")
        .update({
            "priest_id": str(priest_id),
            "status": "approved",
        })
        .eq("id", str(session_id))
        .execute()
    )

    return update_res.data[0]
