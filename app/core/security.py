from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings


# -----------------------------
# Password hashing
# -----------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its hashed version.
    """
    return pwd_context.verify(plain_password, hashed_password)


# -----------------------------
# JWT helpers
# -----------------------------

ALGORITHM = "HS256"


def _create_token(
    *,
    subject: str,
    expires_delta: timedelta,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Internal helper to create a JWT.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # unique token id
    }

    if additional_claims:
        payload.update(additional_claims)

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def create_access_token(user_id: str) -> str:
    """
    Create a short-lived access token.
    """
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"type": "access"},
    )


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived refresh token.
    """
    return _create_token(
        subject=user_id,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        additional_claims={"type": "refresh"},
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises JWTError if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        raise
