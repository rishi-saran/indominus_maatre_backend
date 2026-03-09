# /app/api/one_on_one_session.py

from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
from datetime import timezone, timedelta

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user, require_admin
from app.schemas.one_on_one_session import (
    SessionLifecycle,
    DirectSessionResponse,
    DirectSessionListResponse,
    PreDirectSessionRequest,
    PreDirectSessionResponse,
)
from app.services.stream_service import StreamService
from app.tasks.email_tasks import send_confirmation_email_task

router = APIRouter(prefix="/sessions", tags=["1 on 1 Sessions"])

IST = timezone(timedelta(hours=5, minutes=30))


@router.post(
    "/request-session",
    status_code=status.HTTP_200_OK,
    response_model=PreDirectSessionResponse
)
def request_one_on_one_session(
    request: PreDirectSessionRequest,
    current_user: dict = Depends(get_current_user)
):

    session_data = {
        "start_time": request.start_time.isoformat(),
        "end_time": request.end_time.isoformat(),
        "customer_id": str(current_user["id"]),
        "status": SessionLifecycle.requested.value
    }

    response = supabase.table("sessions").insert(session_data).execute()

    if not response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create a session"
        )

    return response.data[0]


@router.get(
    "/list-all",
    status_code=status.HTTP_200_OK,
    response_model=DirectSessionListResponse
)
def list_all_one_on_one_session(
    current_user: dict = Depends(require_admin)
):

    query = supabase.table("sessions").select("*")
    response = query.execute()

    return {"items": response.data}


@router.put(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    response_model=DirectSessionResponse
)
def approve_direct_session_request(
    session_id: UUID,
    current_user: dict = Depends(require_admin)
):

    response = supabase.rpc(
        "approve_and_assign_session",
        {"p_session_id": str(session_id)}
    ).execute()

    if not response.data:
        raise HTTPException(400, "Unable to approve session")

    session = response.data[0]

    print("Session:", session)

    session_db_id = session["session_id"]

    stream_id = f"session_{session_db_id}"

    try:
        StreamService.create_call(
            stream_id,
            session["customer_id"],
            session["priest_id"]
        )
    except Exception as e:
        print("Stream call creation failed:", e)
        raise HTTPException(500, "Failed to create video call")

    update_response = (
        supabase
        .table("sessions")
        .update({"stream_id": stream_id})
        .eq("id", session_db_id)
        .execute()
    )

    print("Stream ID update:", update_response)

    send_confirmation_email_task.delay(str(session_db_id))

    session["id"] = session.pop("session_id") # done to match response model
    return session


@router.get(
    "/{session_id}/join",
    status_code=status.HTTP_200_OK
)
def join_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user)
):

    response = (
        supabase
        .table("sessions")
        .select("*")
        .eq("id", str(session_id))
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(404, "Session not found")

    session = response.data

    user_id = str(current_user["id"])

    allowed_users = [
        session["customer_id"],
        session["priest_id"]
    ]

    # Check admin role from users table
    role_response = (
        supabase
        .table("users")
        .select("role")
        .eq("id", user_id)
        .single()
        .execute()
    )

    is_admin = role_response.data and role_response.data["role"] == "admin"

    if user_id not in allowed_users and not is_admin:
        raise HTTPException(403, "You are not allowed to join this session")

    if session["status"] not in ["approved", "live"]:
        raise HTTPException(400, "Session not ready")

    call_id = session["stream_id"]

    if not call_id:
        raise HTTPException(400, "Stream not initialized")

    token = StreamService.create_token(user_id)
    
    user_profile = (
        supabase
        .table("users")
        .select("first_name")
        .eq("id", user_id)
        .single()
        .execute()
    )

    first_name = user_profile.data["first_name"]

    return {
        "call_id": call_id,
        "token": token,
        "user_id": user_id,
        "first_name": first_name,
        "api_key": StreamService.api_key
    }