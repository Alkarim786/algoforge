from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import get_db
from app.models import Problem, Topic
from app.schemas import Difficulty, ProblemCreate, ProblemDetail, ProblemSolutions, ProblemSummary, ProblemUpdate
from app.security import require_admin

router = APIRouter(prefix="/problems", tags=["problems"])
DbSession = Annotated[Session, Depends(get_db)]


def get_problem_or_404(db: Session, slug: str) -> Problem:
    problem = db.scalar(
        select(Problem)
        .where(Problem.slug == slug)
        .options(joinedload(Problem.topic), selectinload(Problem.test_cases))
    )
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")
    return problem


def resolve_topic_id(db: Session, slug: str) -> int:
    topic_id = db.scalar(select(Topic.id).where(Topic.slug == slug))
    if topic_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown topic '{slug}'")
    return topic_id


@router.get("", response_model=list[ProblemSummary])
def list_problems(
    db: DbSession,
    topic: str | None = None,
    difficulty: Difficulty | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Problem]:
    query = (
        select(Problem)
        .join(Problem.topic)
        .options(joinedload(Problem.topic))
        .order_by(Topic.order, Problem.order_within_topic, Problem.id)
        .limit(limit)
        .offset(offset)
    )
    if topic is not None:
        query = query.where(Topic.slug == topic)
    if difficulty is not None:
        query = query.where(Problem.difficulty == difficulty)
    return list(db.scalars(query))


@router.get("/{slug}", response_model=ProblemDetail)
def get_problem(slug: str, db: DbSession) -> Problem:
    return get_problem_or_404(db, slug)


@router.get("/{slug}/solutions", response_model=ProblemSolutions)
def get_solutions(slug: str, db: DbSession) -> dict:
    problem = db.scalar(select(Problem).where(Problem.slug == slug).options(selectinload(Problem.solutions)))
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")
    return {"thinking": problem.thinking, "approaches": problem.solutions}


@router.post(
    "", response_model=ProblemDetail, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)]
)
def create_problem(payload: ProblemCreate, db: DbSession) -> Problem:
    data = payload.model_dump(exclude={"topic_slug"})
    problem = Problem(topic_id=resolve_topic_id(db, payload.topic_slug), **data)
    db.add(problem)
    db.commit()
    return get_problem_or_404(db, problem.slug)


@router.patch("/{slug}", response_model=ProblemDetail, dependencies=[Depends(require_admin)])
def update_problem(slug: str, payload: ProblemUpdate, db: DbSession) -> Problem:
    problem = get_problem_or_404(db, slug)
    changes = payload.model_dump(exclude_unset=True)
    if "topic_slug" in changes:
        problem.topic_id = resolve_topic_id(db, changes.pop("topic_slug"))
    for field, value in changes.items():
        setattr(problem, field, value)
    db.commit()
    return get_problem_or_404(db, problem.slug)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_problem(slug: str, db: DbSession) -> None:
    db.delete(get_problem_or_404(db, slug))
    db.commit()
