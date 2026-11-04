"""Runs against a throwaway `<db>_test` Postgres database, built by the real Alembic migration."""
import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

admin_url = make_url(os.environ["DATABASE_URL"])
test_url = admin_url.set(database=f"{admin_url.database}_test")
os.environ["DATABASE_URL"] = test_url.render_as_string(hide_password=False)  # before any app import

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import rate_limit  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{test_url.database}" WITH (FORCE)'))
        connection.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    command.upgrade(Config("alembic.ini"), "head")
    yield
    engine.dispose()
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE "{test_url.database}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    rate_limit.clear_all()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def admin_headers():
    return {"X-Admin-Key": settings.admin_api_key}
