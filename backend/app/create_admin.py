"""Create an admin account, or promote an existing account to admin.

Run with: docker compose exec api python -m app.create_admin <username> <email>

The password is asked for interactively, or read from the ADMIN_PASSWORD environment variable
(for `docker compose exec -T`, where there is no terminal to type into). An existing account keeps
its password unless a new one is given.
"""
import argparse
import os
import sys
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User
from app.schemas import UserCreate
from app.security import hash_password


def create_admin(db: Session, username: str, email: str, password: str | None) -> tuple[User, bool]:
    """Returns (user, created). Raises ValueError for invalid details."""
    email = email.lower()
    user = db.scalar(select(User).where(or_(User.username == username, User.email == email)))
    if user is not None:
        if (user.username, user.email) != (username, email):
            raise ValueError(f"'{username}' / '{email}' match different existing accounts; pass both exactly")
        if password:
            user.password_hash = hash_password(UserCreate(username=username, email=email, password=password).password)
        user.role = "admin"
        db.commit()
        return user, False
    if not password:
        raise ValueError("a password is needed for a new account")
    details = UserCreate(username=username, email=email, password=password)
    user = User(username=details.username, email=details.email, password_hash=hash_password(details.password), role="admin")
    db.add(user)
    db.commit()
    return user, True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("username")
    parser.add_argument("email")
    args = parser.parse_args()

    password = os.environ.get("ADMIN_PASSWORD")
    if password is None and sys.stdin.isatty():
        password = getpass("Password (leave empty to keep an existing account's password): ")
        if password and getpass("Repeat password: ") != password:
            raise SystemExit("Passwords don't match.")

    with SessionLocal() as session:
        try:
            user, created = create_admin(session, args.username, args.email, password or None)
        except (ValueError, ValidationError) as error:
            raise SystemExit(f"Error: {error}") from None
    print(f"{'Created' if created else 'Promoted'} admin '{user.username}'. Sign in at /admin/login.")


if __name__ == "__main__":
    main()
