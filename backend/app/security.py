import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

# Verified against when the account doesn't exist, so login timing doesn't reveal which usernames are taken.
DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    # Login passwords aren't length-validated, and bcrypt only reads the first 72 bytes.
    candidate = password.encode()
    if len(candidate) > 72:
        return False
    if password_hash is None:
        bcrypt.checkpw(candidate, DUMMY_HASH)
        return False
    return bcrypt.checkpw(candidate, password_hash.encode())


def create_access_token(user_id: int) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Your session has expired. Please sign in again.", headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


def require_admin(
    key: Annotated[str | None, Security(admin_key_header)],
    token: Annotated[str | None, Depends(optional_oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Lets in a signed-in admin, or a script holding ADMIN_API_KEY. Returns the admin user (None for the key)."""
    if key is not None and secrets.compare_digest(key, settings.admin_api_key):
        return None
    if token is not None:
        user = get_current_user(token, db)
        if user.is_admin:
            return user
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
