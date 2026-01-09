from fastapi import APIRouter, HTTPException, Response, Request, status

from app.schemas.auth import SignupRequest, LoginRequest
from app.schemas.user import UserResponse
from app.core.supabase import supabase

router = APIRouter(prefix="/api/auth", tags=["auth"])


# -----------------------------
# Helpers
# -----------------------------

def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,          # False only for local dev
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,          # False only for local dev
        samesite="strict",
        path="/api/auth",
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")


# -----------------------------
# Routes
# -----------------------------

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(payload: SignupRequest):
    try:
        result = supabase.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )

        if result.user is None:
            raise HTTPException(status_code=400, detail="Signup failed")

        return UserResponse(
            id=result.user.id,
            email=result.user.email,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
):
    try:
        result = supabase.auth.sign_in_with_password(
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

        return {"message": "Login successful"}

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        result = supabase.auth.refresh_session(refresh_token)
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
async def logout(
    response: Response,
):
    _clear_auth_cookies(response)
    return None