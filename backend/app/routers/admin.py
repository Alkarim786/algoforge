from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.content_checks import check_case
from app.db import get_db
from app.evaluation import ACCEPTED
from app.models import Problem, Solution, Submission, TestCase, Topic, User
from app.progress import JUDGED_SUBMISSION, user_evaluation
from app.schemas import (
    AdminProblemDetail,
    AdminProblemRow,
    AdminTestCase,
    AdminUserList,
    Role,
    RoleUpdate,
    SolutionIn,
    SolutionOut,
    TestCaseIn,
    TestCaseUpdate,
    UserEvaluation,
    UserOut,
)
from app.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User | None, Depends(require_admin)]  # None when the request used ADMIN_API_KEY


@router.get("/users", response_model=AdminUserList)
def list_users(
    db: DbSession,
    search: str | None = None,
    role: Role | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    judged = JUDGED_SUBMISSION
    submissions = func.count(Submission.id).filter(judged)
    is_accepted = judged & (Submission.status == ACCEPTED)
    accepted = func.count(Submission.id).filter(is_accepted)
    solved = func.count(distinct(Submission.problem_id)).filter(is_accepted)
    attempted = func.count(distinct(Submission.problem_id)).filter(judged)
    query = select(
        User.id,
        User.username,
        User.email,
        User.role,
        User.created_at,
        solved.label("solved"),
        attempted.label("attempted"),
        submissions.label("submissions"),
        accepted.label("accepted"),
        func.max(Submission.created_at).filter(judged).label("last_active"),
    ).outerjoin(Submission, Submission.user_id == User.id)
    count_query = select(func.count()).select_from(User)
    filters = []
    if search:
        filters.append(User.username.icontains(search, autoescape=True) | User.email.icontains(search, autoescape=True))
    if role:
        filters.append(User.role == role)
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    rows = db.execute(query.group_by(User.id).order_by(solved.desc(), User.username).limit(limit).offset(offset))
    return {
        "total_users": db.scalar(count_query),
        "total_problems": db.scalar(select(func.count()).select_from(Problem)),
        "users": [
            {
                **row._mapping,
                "acceptance_rate": round(row.accepted / row.submissions, 3) if row.submissions else None,
            }
            for row in rows
        ],
    }


@router.get("/users/{user_id}/evaluation", response_model=UserEvaluation)
def evaluate_user(user_id: int, db: DbSession) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user_evaluation(db, user)


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_role(user_id: int, payload: RoleUpdate, db: DbSession, admin: AdminUser) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if admin is not None and admin.id == user.id and payload.role != "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't remove your own admin access")
    user.role = payload.role
    db.commit()
    return user


# Content editing: test cases (hidden ones included) and solution guides for a problem.
def problem_for_editing(db: Session, slug: str) -> Problem:
    problem = db.scalar(
        select(Problem)
        .where(Problem.slug == slug)
        .options(joinedload(Problem.topic), selectinload(Problem.test_cases), selectinload(Problem.solutions))
    )
    if problem is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Problem not found")
    return problem


def checked_case(problem: Problem, input_text: str, expected_output: str) -> tuple[str, str]:
    try:
        return check_case(problem.entry, input_text, expected_output)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from None


@router.get("/problems", response_model=list[AdminProblemRow])
def list_problems_for_editing(db: DbSession) -> list[dict]:
    cases = (
        select(
            TestCase.problem_id,
            func.count().filter(~TestCase.is_hidden).label("visible_cases"),
            func.count().filter(TestCase.is_hidden).label("hidden_cases"),
        )
        .group_by(TestCase.problem_id)
        .subquery()
    )
    solutions = select(Solution.problem_id, func.count().label("solutions")).group_by(Solution.problem_id).subquery()
    rows = db.execute(
        select(
            Problem.id,
            Problem.slug,
            Problem.title,
            Problem.difficulty,
            Problem.is_flagship,
            Topic.slug.label("topic_slug"),
            Topic.name.label("topic_name"),
            (Problem.thinking.is_not(None) & (Problem.thinking != "")).label("has_thinking"),
            func.coalesce(cases.c.visible_cases, 0).label("visible_cases"),
            func.coalesce(cases.c.hidden_cases, 0).label("hidden_cases"),
            func.coalesce(solutions.c.solutions, 0).label("solutions"),
        )
        .join(Problem.topic)
        .outerjoin(cases, cases.c.problem_id == Problem.id)
        .outerjoin(solutions, solutions.c.problem_id == Problem.id)
        .order_by(Topic.order, Problem.order_within_topic, Problem.id)
    )
    return [dict(row._mapping) for row in rows]


@router.get("/problems/{slug}", response_model=AdminProblemDetail)
def get_problem_for_editing(slug: str, db: DbSession) -> Problem:
    return problem_for_editing(db, slug)


@router.post("/problems/{slug}/test-cases", response_model=AdminTestCase, status_code=status.HTTP_201_CREATED)
def add_test_case(slug: str, payload: TestCaseIn, db: DbSession) -> TestCase:
    problem = problem_for_editing(db, slug)
    input_text, expected = checked_case(problem, payload.input, payload.expected_output)
    case = TestCase(input=input_text, expected_output=expected, is_hidden=payload.is_hidden)
    problem.test_cases.append(case)
    db.commit()
    return case


def test_case_or_404(db: Session, case_id: int) -> TestCase:
    case = db.get(TestCase, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test case not found")
    return case


@router.patch("/test-cases/{case_id}", response_model=AdminTestCase)
def update_test_case(case_id: int, payload: TestCaseUpdate, db: DbSession) -> TestCase:
    case = test_case_or_404(db, case_id)
    case.input, case.expected_output = checked_case(
        case.problem,
        payload.input if payload.input is not None else case.input,
        payload.expected_output if payload.expected_output is not None else case.expected_output,
    )
    if payload.is_hidden is not None:
        case.is_hidden = payload.is_hidden
    db.commit()
    return case


@router.delete("/test-cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_case(case_id: int, db: DbSession) -> None:
    db.delete(test_case_or_404(db, case_id))
    db.commit()


APPROACH_ORDER = {"brute_force": 1, "optimized": 2}
ApproachType = Literal["brute_force", "optimized"]


@router.put("/problems/{slug}/solutions/{approach_type}", response_model=SolutionOut)
def save_solution(slug: str, approach_type: ApproachType, payload: SolutionIn, db: DbSession) -> Solution:
    problem = problem_for_editing(db, slug)
    solution = next((item for item in problem.solutions if item.approach_type == approach_type), None)
    if solution is None:
        solution = Solution(approach_type=approach_type, order=APPROACH_ORDER[approach_type])
        problem.solutions.append(solution)
    data = payload.model_dump()
    data["code"] = {"python": data["code"]}
    for field, value in data.items():
        setattr(solution, field, value)
    db.commit()
    return solution


@router.delete("/problems/{slug}/solutions/{approach_type}", status_code=status.HTTP_204_NO_CONTENT)
def delete_solution(slug: str, approach_type: ApproachType, db: DbSession) -> None:
    problem = problem_for_editing(db, slug)
    solution = next((item for item in problem.solutions if item.approach_type == approach_type), None)
    if solution is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such solution")
    problem.solutions.remove(solution)
    db.commit()
