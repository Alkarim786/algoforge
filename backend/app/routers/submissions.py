from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis import RedisError
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.evaluation import PENDING, RUNNING, SYSTEM_ERROR
from app.jobs import enqueue
from app.models import Problem, Submission, SubmissionResult, TestCase, User
from app.schemas import CaseResult, SubmissionCreate, SubmissionDetail, SubmissionSummary
from app.security import get_current_user

router = APIRouter(prefix="/submissions", tags=["submissions"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

MAX_IN_FLIGHT = 3
# Past this age an unfinished submission is assumed lost to a worker crash, so it stops blocking the user.
IN_FLIGHT_WINDOW = timedelta(minutes=5)


@router.post("", response_model=SubmissionSummary, status_code=status.HTTP_202_ACCEPTED)
def create_submission(payload: SubmissionCreate, user: CurrentUser, db: DbSession) -> dict:
    problem = db.scalar(select(Problem).where(Problem.slug == payload.problem_slug))
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")

    case_filter = TestCase.problem_id == problem.id
    if payload.mode == "run":
        case_filter &= TestCase.is_hidden.is_(False)
    if payload.custom_inputs is None and not db.scalar(select(exists().where(case_filter))):
        raise HTTPException(status.HTTP_409_CONFLICT, "This problem has no test cases yet, so it can't be judged.")

    in_flight = db.scalar(
        select(func.count())
        .select_from(Submission)
        .where(
            Submission.user_id == user.id,
            Submission.status.in_((PENDING, RUNNING)),
            Submission.created_at > datetime.now(UTC) - IN_FLIGHT_WINDOW,
        )
    )
    if in_flight >= MAX_IN_FLIGHT:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "You already have 3 submissions running. Wait for one to finish, then try again.")

    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        language=payload.language,
        code=payload.code,
        kind=payload.mode,
        custom_inputs=payload.custom_inputs,
    )
    db.add(submission)
    db.commit()
    try:
        enqueue(submission.id)
    except RedisError:
        submission.status = SYSTEM_ERROR
        db.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The judge is unavailable right now. Please try again in a moment.") from None
    return summarize(submission, problem.slug)


def summarize(submission: Submission, problem_slug: str) -> dict:
    return {
        "id": submission.id,
        "problem_slug": problem_slug,
        "language": submission.language,
        "mode": submission.kind,
        "status": submission.status,
        "created_at": submission.created_at,
    }


@router.get("", response_model=list[SubmissionSummary])
def list_submissions(
    user: CurrentUser,
    db: DbSession,
    problem: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    query = (
        select(Submission, Problem.slug)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(Submission.user_id == user.id, Submission.kind == "submit")
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if problem is not None:
        query = query.where(Problem.slug == problem)
    return [summarize(submission, slug) for submission, slug in db.execute(query)]


@router.get("/{submission_id}", response_model=SubmissionDetail)
def get_submission(submission_id: int, user: CurrentUser, db: DbSession) -> dict:
    submission = db.get(Submission, submission_id)
    # 404 rather than 403, so ids can't be probed for other users' submissions.
    if submission is None or submission.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found")

    slug = db.scalar(select(Problem.slug).where(Problem.id == submission.problem_id))
    rows = db.execute(
        select(SubmissionResult, TestCase)
        .outerjoin(TestCase, SubmissionResult.test_case_id == TestCase.id)
        .where(SubmissionResult.submission_id == submission.id)
        .order_by(SubmissionResult.id)
    )
    return {**summarize(submission, slug), "code": submission.code, "results": [to_case_result(*row) for row in rows]}


def to_case_result(result: SubmissionResult, case: TestCase | None) -> CaseResult:
    is_hidden = case is not None and case.is_hidden
    visible = {} if is_hidden else {
        "input": case.input if case else result.custom_input,
        "expected_output": case.expected_output if case else None,
        "actual_output": result.actual_output,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }  # fmt: skip
    # Output and stderr from a hidden case could echo its input, so they stay on the server.
    return CaseResult(
        is_hidden=is_hidden,
        passed=result.passed,
        verdict=result.verdict,
        runtime_ms=result.runtime_ms,
        memory_kb=result.memory_kb,
        **visible,
    )
