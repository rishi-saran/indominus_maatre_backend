from fastapi import APIRouter, HTTPException, Response, Request, status

from app.schemas.auth import SignupRequest, LoginRequest
from app.schemas.user import UserResponse
from app.core.supabase import get_anon_client, get_service_role_client

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------------
# Cookie Helpers
# -----------------------------

def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
):
    # Access token (used for API auth)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,          # set True in production with HTTPS
        samesite="strict",
        path="/",
    )

    # Refresh token (used only for refresh endpoint)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,          # set True in production with HTTPS
        samesite="strict",
        path="/api/v1/auth",
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth")


# -----------------------------
# Routes
# -----------------------------

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(payload: SignupRequest):
    """
    1. Create user in Supabase Auth (auth.users)
    2. Create matching row in public.profiles
    """
    try:
        auth_client = get_anon_client()
        db_client = get_service_role_client()

        result = auth_client.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )

        user = result.user
        if not user:
            raise HTTPException(status_code=400, detail="Signup failed")

        # 🔑 Create profile row linked to auth.users.id
        db_client.table("profiles").insert(
            {
                "id": user.id,
                "role": "user",
            }
        ).execute()

        return UserResponse(
            id=user.id,
            email=user.email,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
):
    """
    Login using Supabase Auth
    """
    try:
        auth_client = get_anon_client()
        result = auth_client.auth.sign_in_with_password(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )

        session = result.session
        if session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        _set_auth_cookies(
            response,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )

        return {
            "message": "Login successful",
            "user_id": result.user.id,
            "email": result.user.email,
        }

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
):
    """
    Refresh access token using refresh token cookie
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        auth_client = get_anon_client()
        result = auth_client.auth.refresh_session(refresh_token)
        session = result.session

        if session is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        _set_auth_cookies(
            response,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )

        return {"message": "Token refreshed"}

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """
    Clear auth cookies
    """
    _clear_auth_cookies(response)
    return None