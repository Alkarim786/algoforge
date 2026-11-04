from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import drivers
from app.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('student', 'admin')", name="role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    # Sign-up always creates a student; admins are made with `python -m app.create_admin` or by another admin.
    role: Mapped[str] = mapped_column(String(10), default="student", server_default="student")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    notes_content: Mapped[str | None] = mapped_column(Text)

    problems: Mapped[list["Problem"]] = relationship(back_populates="topic", order_by="Problem.order_within_topic")


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (CheckConstraint("difficulty IN ('Easy', 'Medium', 'Hard')", name="difficulty"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    difficulty: Mapped[str] = mapped_column(String(10))
    description: Mapped[str] = mapped_column(Text)
    constraints: Mapped[str] = mapped_column(Text, default="")
    examples: Mapped[list] = mapped_column(JSONB, default=list)
    order_within_topic: Mapped[int] = mapped_column(Integer, default=0)
    is_flagship: Mapped[bool] = mapped_column(Boolean, default=False)
    entry: Mapped[dict | None] = mapped_column(JSONB)  # How to call user code; see app/drivers.py
    thinking: Mapped[str | None] = mapped_column(Text)  # "How to think" guide, markdown

    topic: Mapped[Topic] = relationship(back_populates="problems")
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", order_by="TestCase.id", cascade="all, delete-orphan", passive_deletes=True
    )
    solutions: Mapped[list["Solution"]] = relationship(
        order_by="Solution.order", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def topic_slug(self) -> str:
        return self.topic.slug

    @property
    def sample_test_cases(self) -> list["TestCase"]:
        return [case for case in self.test_cases if not case.is_hidden]

    @property
    def can_submit(self) -> bool:
        return bool(self.test_cases)

    @property
    def starter_code(self) -> dict[str, str]:
        return {"python": drivers.starter_code(self.entry)}


class TestCase(Base):
    __tablename__ = "test_cases"
    __test__ = False  # not a pytest class, despite the name

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    input: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    problem: Mapped[Problem] = relationship(back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # RESTRICT: deleting a problem must not silently erase users' submission history.
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), index=True)
    language: Mapped[str] = mapped_column(String(20))
    code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    # "run" (visible cases, no effect on stats) or "submit" (all cases).
    kind: Mapped[str] = mapped_column(String(10), default="submit", server_default="submit")
    # Set on a run that uses inputs from the Testcase tab instead of the problem's visible cases.
    custom_inputs: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubmissionResult(Base):
    __tablename__ = "submission_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    # Null for a custom input, which has no stored case behind it.
    test_case_id: Mapped[int | None] = mapped_column(ForeignKey("test_cases.id", ondelete="CASCADE"), index=True)
    custom_input: Mapped[str | None] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(Boolean)
    verdict: Mapped[str | None] = mapped_column(String(30))
    actual_output: Mapped[str | None] = mapped_column(Text)
    stdout: Mapped[str | None] = mapped_column(Text)  # Debug prints, separate from the answer
    stderr: Mapped[str | None] = mapped_column(Text)
    runtime_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)


class Solution(Base):
    __tablename__ = "solutions"
    __table_args__ = (
        CheckConstraint("approach_type IN ('brute_force', 'optimized')", name="approach_type"),
        UniqueConstraint("problem_id", "approach_type", name="uq_solutions_problem_id_approach_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"), index=True)
    approach_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200), default="", server_default="")
    code: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"python": "...", "cpp": "..."}
    explanation: Mapped[str] = mapped_column(Text)
    # [{"start": 3, "end": 5, "note": "..."}], line numbers in the code, for the synced explanation panel
    line_notes: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    time_complexity: Mapped[str] = mapped_column(String(50))
    space_complexity: Mapped[str] = mapped_column(String(50))
    flowchart_mermaid: Mapped[str | None] = mapped_column(Text)
    order: Mapped[int] = mapped_column(Integer, default=0)
