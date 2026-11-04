from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    admin_api_key: str = Field(min_length=16)
    redis_url: str = "redis://redis:6379/0"
    sandbox_python_image: str = "algoforge-sandbox-python:latest"
    sandbox_time_limit_seconds: int = 2  # CPU seconds per test case; wall clock gets double
    # e.g. "runsc" to run user code under gVisor, a user-space kernel, for a stronger boundary than plain Docker.
    sandbox_runtime: str | None = None


settings = Settings()
