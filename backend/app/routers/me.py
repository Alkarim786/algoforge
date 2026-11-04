from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.progress import dashboard, problem_rows, verdicts_by_problem
from app.evaluation import ACCEPTED
from app.schemas import Dashboard, Progress
from app.security import get_current_user

router = APIRouter(prefix="/me", tags=["me"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/dashboard", response_model=Dashboard)
def get_dashboard(user: CurrentUser, db: DbSession) -> dict:
    return dashboard(db, user, today=datetime.now(UTC).date())


@router.get("/progress", response_model=Progress)
def get_progress(user: CurrentUser, db: DbSession) -> dict:
    """Solved and attempted problem slugs, for marking problem lists."""
    statuses = verdicts_by_problem(db, user.id)
    rows = problem_rows(db)
    return {
        "solved": [row.slug for row in rows if statuses.get(row.id, {}).get(ACCEPTED)],
        "attempted": [row.slug for row in rows if row.id in statuses and not statuses[row.id][ACCEPTED]],
    }
