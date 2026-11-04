"""Solution guides must parse, and every approach's code must pass the problem's real test cases."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app import drivers
from app.seed import load_problems, seed
from app.solution_content import parse_solution

SOLUTIONS_DIR = Path(__file__).resolve().parents[1] / "content" / "solutions"
GUIDES = sorted(SOLUTIONS_DIR.glob("*.md"))
PROBLEMS = {problem.slug: problem for problem in load_problems()}
# Brute force is meant to be too slow for stress inputs, so it only has to pass the small cases.
BRUTE_FORCE_MAX_INPUT = 2_000
BRUTE_FORCE_TIMEOUT = 10

CASES = [
    (path.stem, approach)
    for path in GUIDES
    for approach in parse_solution(path.read_text("utf-8"))["approaches"]
]


def test_guides_belong_to_real_problems():
    assert GUIDES
    assert {path.stem for path in GUIDES} <= set(PROBLEMS)


@pytest.mark.parametrize("path", GUIDES, ids=lambda path: path.stem)
def test_guide_has_thinking_and_diagrams(path):
    guide = parse_solution(path.read_text("utf-8"))
    assert len(guide["thinking"]) > 200
    assert "```mermaid" in guide["thinking"], "How to think needs at least one diagram"
    for approach in guide["approaches"]:
        assert approach["flowchart_mermaid"].startswith("flowchart")
        assert approach["explanation"], "each approach needs an explanation"


@pytest.mark.parametrize(
    "slug,approach", CASES, ids=[f"{slug}-{approach['approach_type']}" for slug, approach in CASES]
)
def test_approach_code_passes_test_cases(slug, approach):
    problem = PROBLEMS[slug]
    program = drivers.wrap(problem.entry, approach["code"]["python"])
    cases = [
        case
        for case in problem.test_cases
        if approach["approach_type"] == "optimized" or len(case.input) <= BRUTE_FORCE_MAX_INPUT
    ]
    brute = approach["approach_type"] == "brute_force"
    passed = 0
    for case in cases:
        try:
            completed = subprocess.run(
                [sys.executable, "-c", program],
                input=case.input,
                capture_output=True,
                text=True,
                timeout=BRUTE_FORCE_TIMEOUT if brute else 60,
            )
        except subprocess.TimeoutExpired:
            # Brute force is allowed to be too slow (that's the lesson); it just mustn't be wrong.
            assert brute, f"optimized solution timed out on {case.input[:200]}"
            continue
        assert completed.returncode == 0, completed.stderr[-1000:]
        _, answer = drivers.split_output(problem.entry, completed.stdout)
        assert json.loads(answer) == json.loads(case.expected_output), case.input[:200]
        passed += 1
    assert passed >= 3, f"only {passed} cases finished"


def test_parser_rejects_line_notes_outside_the_code():
    text = (SOLUTIONS_DIR / "two-sum.md").read_text("utf-8").replace("- `3` Remember", "- `30` Remember", 1)
    with pytest.raises(ValueError, match="outside lines"):
        parse_solution(text)


def test_solutions_are_seeded_and_served(client, db):
    seed(db)
    body = client.get("/problems/two-sum/solutions").json()
    assert "```mermaid" in body["thinking"]
    assert [approach["approach_type"] for approach in body["approaches"]] == ["brute_force", "optimized"]
    first_note = body["approaches"][1]["line_notes"][0]
    assert (first_note["start"], first_note["end"]) == (3, 3)
    assert client.get("/problems/nope/solutions").status_code == 404


def test_problem_without_a_guide_has_no_solutions(client, admin_headers):
    client.post("/topics", json={"name": "T", "slug": "t"}, headers=admin_headers)
    problem = {"topic_slug": "t", "title": "P", "slug": "p", "difficulty": "Easy", "description": "d"}
    client.post("/problems", json=problem, headers=admin_headers)
    assert client.get("/problems/p/solutions").json() == {"thinking": None, "approaches": []}
