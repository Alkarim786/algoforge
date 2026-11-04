from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.routers import admin, auth, me, problems, submissions, topics

app = FastAPI(title="AlgoForge API", version="0.1.0")
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(topics.router)
app.include_router(problems.router)
app.include_router(submissions.router)


@app.exception_handler(IntegrityError)
def integrity_error(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Conflicts with existing data (duplicate value, or the record is still referenced)"},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
