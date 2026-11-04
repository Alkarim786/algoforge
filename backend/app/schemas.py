from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.content_checks import validate_entry

Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=100)]
Difficulty = Literal["Easy", "Medium", "Hard"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Auth
class UserCreate(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_-]{3,32}$")
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def fits_bcrypt(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return value


Role = Literal["student", "admin"]


class UserOut(ORMModel):
    id: int
    username: str
    email: EmailStr
    role: Role
    created_at: datetime


class RoleUpdate(BaseModel):
    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Topics
class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: Slug
    order: int = 0
    notes_content: str | None = None


class TopicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: Slug | None = None
    order: int | None = None
    notes_content: str | None = None


class TopicSummary(ORMModel):
    id: int
    name: str
    slug: str
    order: int


# Problems
class Example(BaseModel):
    input: str
    output: str
    explanation: str | None = None


def _valid_entry(entry: dict | None) -> dict | None:
    validate_entry(entry)
    return entry


class ProblemCreate(BaseModel):
    topic_slug: Slug
    title: str = Field(min_length=1, max_length=200)
    slug: Slug
    difficulty: Difficulty
    description: str
    constraints: str = ""
    examples: list[Example] = []
    order_within_topic: int = 0
    is_flagship: bool = False
    entry: dict | None = None
    thinking: str | None = None

    _check_entry = field_validator("entry")(_valid_entry)


class ProblemUpdate(BaseModel):
    topic_slug: Slug | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: Slug | None = None
    difficulty: Difficulty | None = None
    description: str | None = None
    constraints: str | None = None
    examples: list[Example] | None = None
    order_within_topic: int | None = None
    is_flagship: bool | None = None
    entry: dict | None = None
    thinking: str | None = None

    _check_entry = field_validator("entry")(_valid_entry)


class ProblemSummary(ORMModel):
    id: int
    topic_slug: str
    title: str
    slug: str
    difficulty: str
    order_within_topic: int
    is_flagship: bool


class SampleTestCase(ORMModel):
    id: int
    input: str
    expected_output: str


class ProblemDetail(ProblemSummary):
    description: str
    constraints: str
    examples: list[Example]
    # Visible cases only. Hidden cases must never be serialized to clients.
    sample_test_cases: list[SampleTestCase]
    can_submit: bool
    starter_code: dict[str, str]


class TopicDetail(TopicSummary):
    notes_content: str | None
    problems: list[ProblemSummary]


class LineNote(BaseModel):
    start: int
    end: int
    note: str


class SolutionOut(ORMModel):
    approach_type: str
    title: str
    time_complexity: str
    space_complexity: str
    explanation: str
    code: dict[str, str]
    line_notes: list[LineNote]
    flowchart_mermaid: str | None


class ProblemSolutions(BaseModel):
    thinking: str | None
    approaches: list[SolutionOut]


# Admin content editing. Unlike the public schemas, these include hidden test cases.
class TestCaseIn(BaseModel):
    __test__ = False  # not a pytest class, despite the name

    input: str = Field(min_length=1, max_length=2_000_000)
    expected_output: str = Field(min_length=1, max_length=2_000_000)
    is_hidden: bool = False


class TestCaseUpdate(BaseModel):
    __test__ = False

    input: str | None = Field(default=None, min_length=1, max_length=2_000_000)
    expected_output: str | None = Field(default=None, min_length=1, max_length=2_000_000)
    is_hidden: bool | None = None


class AdminTestCase(ORMModel):
    id: int
    input: str
    expected_output: str
    is_hidden: bool


class SolutionIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    time_complexity: str = Field(min_length=1, max_length=50)
    space_complexity: str = Field(min_length=1, max_length=50)
    explanation: str = ""
    code: str = Field(min_length=1, max_length=64_000)
    line_notes: list[LineNote] = []
    flowchart_mermaid: str | None = None

    @model_validator(mode="after")
    def notes_fit_the_code(self) -> "SolutionIn":
        line_count = len(self.code.rstrip("\n").split("\n"))
        for note in self.line_notes:
            if not 1 <= note.start <= note.end <= line_count:
                raise ValueError(f"line note {note.start}-{note.end} is outside the code's lines 1-{line_count}")
        return self


class AdminProblemRow(BaseModel):
    id: int
    slug: str
    title: str
    difficulty: str
    is_flagship: bool
    topic_slug: str
    topic_name: str
    has_thinking: bool
    visible_cases: int
    hidden_cases: int
    solutions: int


class AdminProblemDetail(ProblemDetail):
    entry: dict | None
    thinking: str | None
    test_cases: list[AdminTestCase]
    solutions: list[SolutionOut]


# Submissions
class SubmissionCreate(BaseModel):
    problem_slug: Slug
    language: Literal["python"]
    code: str = Field(min_length=1, max_length=64_000)
    mode: Literal["run", "submit"] = "submit"
    custom_inputs: list[Annotated[str, Field(min_length=1, max_length=10_000)]] | None = Field(
        default=None, min_length=1, max_length=10
    )

    @model_validator(mode="after")
    def custom_inputs_only_on_run(self) -> "SubmissionCreate":
        if self.custom_inputs is not None and self.mode != "run":
            raise ValueError("custom_inputs can only be used with mode 'run'")
        return self


class SubmissionSummary(BaseModel):
    id: int
    problem_slug: str
    language: str
    mode: str
    status: str
    created_at: datetime


class CaseResult(BaseModel):
    is_hidden: bool
    passed: bool
    verdict: str | None
    runtime_ms: int | None
    memory_kb: int | None
    # Null for hidden cases.
    input: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    stdout: str | None = None
    stderr: str | None = None


class SubmissionDetail(SubmissionSummary):
    code: str
    results: list[CaseResult]


# Admin
class AdminUserRow(UserOut):
    solved: int
    attempted: int
    submissions: int
    acceptance_rate: float | None
    last_active: datetime | None


class AdminUserList(BaseModel):
    total_users: int
    total_problems: int
    users: list[AdminUserRow]


class TopicEvaluation(BaseModel):
    slug: str
    name: str
    score: int
    classification: Literal["strength", "developing", "weakness", "not_attempted"]
    solved: int
    attempted: int
    total: int
    submissions: int
    top_failure: str | None


class DifficultyProgress(BaseModel):
    difficulty: Difficulty
    solved: int
    total: int


class RecentSubmission(BaseModel):
    id: int
    title: str
    slug: str
    language: str
    status: str
    created_at: datetime


class UserEvaluation(BaseModel):
    user: UserOut
    solved: int
    attempted: int
    total_problems: int
    submissions: int
    acceptance_rate: float | None
    strengths: list[str]
    weaknesses: list[str]
    not_attempted: list[str]
    difficulty: list[DifficultyProgress]
    topics: list[TopicEvaluation]
    recent_submissions: list[RecentSubmission]


class ProblemRef(BaseModel):
    slug: str
    title: str
    difficulty: str
    topic_name: str


class DayActivity(BaseModel):
    date: date
    submissions: int


class Dashboard(UserEvaluation):
    current_streak: int
    longest_streak: int
    activity: list[DayActivity]
    continue_problem: ProblemRef | None
    next_problem: ProblemRef | None
    solved_slugs: list[str]
    attempted_slugs: list[str]


class Progress(BaseModel):
    solved: list[str]
    attempted: list[str]


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def fits_bcrypt(cls, value: str) -> str:
        if len(value.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return value
