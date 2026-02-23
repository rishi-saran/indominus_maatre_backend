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
    PreDirectSessionResponse
)


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail = "Supabase Error")
    
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
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DirectSessionResponse
)
def approve_direct_session_request(
    session_id: UUID, 
    request: PreDirectSessionResponse,
    current_user: dict = Depends(require_admin)
): 
    data = request.dict(exclude_unset=True)