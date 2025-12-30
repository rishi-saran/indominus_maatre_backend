from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import SignupRequest, LoginRequest
from app.schemas.user import UserResponse
from app.services.auth_service import (
    signup_user,
    login_user,
    refresh_tokens,
    logout_user,
)

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
        secure=False,          # set False only in local dev 
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/auth",
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")


# -----------------------------
# Routes
# -----------------------------

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await signup_user(
            db,
            email=payload.email,
            password=payload.password,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        access_token, refresh_token = await login_user(
            db,
            email=payload.email,
            password=payload.password,
        )
        _set_auth_cookies(
            response,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        return {"message": "Login successful"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        new_access, new_refresh = await refresh_tokens(
            db,
            refresh_token=refresh_token,
        )
        _set_auth_cookies(
            response,
            access_token=new_access,
            refresh_token=new_refresh,
        )
        return {"message": "Token refreshed"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await logout_user(db, refresh_token=refresh_token)

    _clear_auth_cookies(response)
    return None
