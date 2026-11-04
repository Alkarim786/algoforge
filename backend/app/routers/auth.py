from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import rate_limit
from app.db import get_db
from app.models import User
from app.schemas import PasswordChange, Token, UserCreate, UserOut
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    email = payload.email.lower()
    if db.scalar(select(User).where(or_(User.username == payload.username, User.email == email))):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already registered")
    user = User(username=payload.username, email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    portal: Literal["student", "admin"] = "student",
) -> Token:
    """Form-encoded `username` (username or email) and `password`, so Swagger's Authorize button works.

    `?portal=admin` is the admin sign-in: it only succeeds for admin accounts. Admins may also use the student one.
    """
    identifier = form.username.lower() if "@" in form.username else form.username
    address = request.client.host if request.client else "unknown"
    if rate_limit.is_locked(identifier, address):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed sign-in attempts. Wait 15 minutes and try again.",
            headers={"Retry-After": str(rate_limit.WINDOW_SECONDS)},
        )
    user = db.scalar(select(User).where(or_(User.username == identifier, User.email == identifier)))
    if not verify_password(form.password, user.password_hash if user else None):
        rate_limit.record_failure(identifier, address)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect username or password", headers={"WWW-Authenticate": "Bearer"}
        )
    rate_limit.clear_account(identifier)
    if portal == "admin" and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account doesn't have admin access. Use the student sign-in.")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]
) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
