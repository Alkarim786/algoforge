from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.routers import admin, auth, me, problems, submissions, topics
from app.validation_messages import friendly_errors

app = FastAPI(title="AlgoForge API", version="0.1.0")
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(topics.router)
app.include_router(problems.router)
app.include_router(submissions.router)


@app.exception_handler(RequestValidationError)
def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=friendly_errors(error.errors()))


@app.exception_handler(IntegrityError)
def integrity_error(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "That already exists, or something else still depends on it."},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
