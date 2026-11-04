import json
from collections import Counter

import pytest
from sqlalchemy import func, select

from app.models import Problem, TestCase, Topic
from app.seed import load_problems, seed
from tests.reference_solutions import SOLUTIONS

FIRST_FOUR = {"two-sum", "maximum-subarray", "number-of-1-bits", "counting-bits"}
PROBLEMS = load_problems()


def solve(slug: str, stdin: str) -> str:
    args = [json.loads(line) for line in stdin.split("\n")]
    return json.dumps(SOLUTIONS[slug](*args), separators=(",", ":"))


def test_seed_counts_and_is_idempotent(db):
    first = seed(db)
    assert first[:2] == (10, len(PROBLEMS))
    case_ids = set(db.scalars(select(TestCase.id)))

    assert seed(db) == first
    assert db.scalar(select(func.count()).select_from(Topic)) == 10
    assert db.scalar(select(func.count()).select_from(Problem)) == len(PROBLEMS)
    assert set(db.scalars(select(TestCase.id))) == case_ids  # ids survive, so stored results stay valid


def test_two_flagships_per_topic():
    flagships = [problem for problem in PROBLEMS if problem.is_flagship]
    assert set(Counter(problem.topic_slug for problem in flagships).values()) == {2}
    assert len(flagships) == 20


def test_every_problem_has_a_reference_solution_and_hidden_cases():
    assert {problem.slug for problem in PROBLEMS} == set(SOLUTIONS)
    for problem in PROBLEMS:
        assert sum(case.is_hidden for case in problem.test_cases) >= 5, problem.slug
        assert sum(not case.is_hidden for case in problem.test_cases) >= 3, problem.slug


@pytest.mark.parametrize("slug", sorted(FIRST_FOUR))
def test_first_four_have_required_cases(slug):
    problem = next(p for p in PROBLEMS if p.slug == slug)
    hidden = [case for case in problem.test_cases if case.is_hidden]
    visible = [case for case in problem.test_cases if not case.is_hidden]
    assert len(visible) >= 3
    assert len(hidden) >= 5
    assert len({case.input for case in problem.test_cases}) == len(problem.test_cases)


@pytest.mark.parametrize("problem", PROBLEMS, ids=lambda p: p.slug)
def test_examples_match_reference_solution(problem):
    assert len(problem.examples) >= 3
    for example in problem.examples:
        assert solve(problem.slug, example.input) == example.output, example.input


@pytest.mark.parametrize("problem", [p for p in PROBLEMS if p.test_cases], ids=lambda p: p.slug)
def test_test_cases_match_reference_solution(problem):
    for case in problem.test_cases:
        assert solve(problem.slug, case.input) == case.expected_output, case.input


def test_two_sum_cases_have_exactly_one_answer():
    problem = next(p for p in PROBLEMS if p.slug == "two-sum")
    for case in problem.test_cases:
        nums, target = (json.loads(line) for line in case.input.split("\n"))
        pairs = [(i, j) for i in range(len(nums)) for j in range(i + 1, len(nums)) if nums[i] + nums[j] == target]
        assert len(pairs) == 1, case.input
