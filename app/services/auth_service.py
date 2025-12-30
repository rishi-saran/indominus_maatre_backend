from datetime import datetime, timedelta, timezone
from typing import Tuple
import hashlib

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# -----------------------------
# Helpers
# -----------------------------

def _hash_refresh_token(token: str) -> str:
    """
    Hash refresh token before storing in DB.
    """
    return hashlib.sha256(token.encode()).hexdigest()


# -----------------------------
# Signup
# -----------------------------

async def signup_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError("Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


# -----------------------------
# Login
# -----------------------------

async def login_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> Tuple[str, str]:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise ValueError("Invalid credentials")

    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")

    # Create tokens
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Store refresh token (hashed)
    refresh_token_obj = RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False,
    )

    db.add(refresh_token_obj)
    await db.commit()

    return access_token, refresh_token


# -----------------------------
# Refresh tokens (rotation)
# -----------------------------

async def refresh_tokens(
    db: AsyncSession,
    *,
    refresh_token: str,
) -> Tuple[str, str]:
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    user_id = payload.get("sub")
    token_hash = _hash_refresh_token(refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token:
        raise ValueError("Invalid or expired refresh token")

    # Revoke old token
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.id == stored_token.id)
        .values(is_revoked=True)
    )

    # Issue new tokens
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)

    new_refresh_obj = RefreshToken(
        user_id=stored_token.user_id,
        token_hash=_hash_refresh_token(new_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False,
    )

    db.add(new_refresh_obj)
    await db.commit()

    return new_access_token, new_refresh_token


# -----------------------------
# Logout (server-side invalidation)
# -----------------------------

async def logout_user(
    db: AsyncSession,
    *,
    refresh_token: str,
) -> None:
    token_hash = _hash_refresh_token(refresh_token)

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(is_revoked=True)
    )
    await db.commit()
