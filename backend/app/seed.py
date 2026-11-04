"""Load content/ into the database. Safe to re-run: rows are matched by slug and updated in place.

Run with: python -m app.seed
"""
import json
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Problem, Solution, TestCase, Topic
from app.schemas import ProblemCreate, TopicCreate
from app.solution_content import parse_solution

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"


class SeedTestCase(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False


class SeedProblem(ProblemCreate):
    test_cases: list[SeedTestCase] = []


def load_topics() -> list[TopicCreate]:
    topics = [TopicCreate(**raw) for raw in json.loads((CONTENT_DIR / "topics.json").read_text("utf-8"))]
    for topic in topics:
        notes = CONTENT_DIR / "notes" / f"{topic.slug}.md"
        if notes.exists():
            topic.notes_content = notes.read_text("utf-8")
    return topics


def load_problems() -> list[SeedProblem]:
    entries = json.loads((CONTENT_DIR / "entries.json").read_text("utf-8"))
    problems = []
    for path in sorted((CONTENT_DIR / "problems").glob("*.json")):
        problems += [
            SeedProblem(topic_slug=path.stem, entry=entries.get(raw["slug"]), **raw)
            for raw in json.loads(path.read_text("utf-8"))
        ]
    return problems


def sync_test_cases(db: Session, problem: Problem, cases: list[SeedTestCase]) -> None:
    # Matched by input rather than replaced wholesale, so ids referenced by stored results survive a re-seed.
    existing = {case.input: case for case in problem.test_cases}
    for case in cases:
        if case.input in existing:
            row = existing.pop(case.input)
            row.expected_output, row.is_hidden = case.expected_output, case.is_hidden
        else:
            problem.test_cases.append(TestCase(**case.model_dump()))
    for stale in existing.values():
        problem.test_cases.remove(stale)


def load_solution_guide(slug: str) -> dict | None:
    path = CONTENT_DIR / "solutions" / f"{slug}.md"
    if not path.exists():
        return None
    try:
        return parse_solution(path.read_text("utf-8"))
    except ValueError as error:
        raise ValueError(f"{path.name}: {error}") from None


def sync_solutions(problem: Problem) -> None:
    guide = load_solution_guide(problem.slug)
    problem.thinking = guide["thinking"] if guide else None
    existing = {solution.approach_type: solution for solution in problem.solutions}
    wanted = guide["approaches"] if guide else []
    for data in wanted:
        solution = existing.pop(data["approach_type"], None) or Solution(approach_type=data["approach_type"])
        for field, value in data.items():
            setattr(solution, field, value)
        if solution not in problem.solutions:
            problem.solutions.append(solution)
    for stale in existing.values():
        problem.solutions.remove(stale)


def seed(db: Session) -> tuple[int, int, int]:
    topic_ids = {}
    topics = load_topics()
    for data in topics:
        topic = db.scalar(select(Topic).where(Topic.slug == data.slug))
        if topic is None:
            topic = Topic(slug=data.slug)
            db.add(topic)
        topic.name, topic.order, topic.notes_content = data.name, data.order, data.notes_content
        db.flush()
        topic_ids[data.slug] = topic.id

    problems = load_problems()
    for data in problems:
        problem = db.scalar(select(Problem).where(Problem.slug == data.slug))
        if problem is None:
            problem = Problem(slug=data.slug)
            db.add(problem)
        problem.topic_id = topic_ids[data.topic_slug]
        for field in ("title", "difficulty", "description", "constraints", "order_within_topic", "is_flagship", "entry"):
            setattr(problem, field, getattr(data, field))
        problem.examples = [example.model_dump(exclude_none=True) for example in data.examples]
        sync_test_cases(db, problem, data.test_cases)
        sync_solutions(problem)
    db.commit()
    return len(topics), len(problems), sum(len(problem.test_cases) for problem in problems)


if __name__ == "__main__":
    with SessionLocal() as session:
        topic_count, problem_count, case_count = seed(session)
    print(f"Seeded {topic_count} topics, {problem_count} problems, {case_count} test cases.")
