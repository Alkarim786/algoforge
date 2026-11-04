"""Adds problems to content/ with expected outputs computed by tests/reference_solutions.py.

Each problem is a dict: topic, title, slug, difficulty, order, description, constraints, entry,
examples [(stdin, explanation or None)], hidden [stdin]. Outputs are never typed by hand, so they
can't disagree with the reference solution. Re-running replaces a problem with the same slug.

Run from backend/ (for example in the worker container): python -m scripts.<batch module>
"""
import json
import sys
from pathlib import Path

sys.setrecursionlimit(100_000)

from tests.reference_solutions import SOLUTIONS  # noqa: E402

CONTENT = Path(__file__).resolve().parents[1] / "content"


def dump(value) -> str:
    return json.dumps(value, separators=(",", ":"))


def lines(*values) -> str:
    """One JSON value per line: the stdin format every problem uses."""
    return "\n".join(dump(value) for value in values)


def solve(slug: str, stdin: str) -> str:
    return dump(SOLUTIONS[slug](*[json.loads(line) for line in stdin.split("\n")]))


def add(problems: list[dict]) -> None:
    entries_path = CONTENT / "entries.json"
    entries = json.loads(entries_path.read_text("utf-8"))
    by_topic: dict[str, list[dict]] = {}
    for problem in problems:
        by_topic.setdefault(problem["topic"], []).append(problem)

    for topic, items in by_topic.items():
        path = CONTENT / "problems" / f"{topic}.json"
        existing = json.loads(path.read_text("utf-8"))
        for problem in items:
            slug = problem["slug"]
            examples = []
            for stdin, explanation in problem["examples"]:
                example = {"input": stdin, "output": solve(slug, stdin)}
                if explanation:
                    example["explanation"] = explanation
                examples.append(example)
            cases = [{"input": example["input"], "expected_output": example["output"]} for example in examples]
            cases += [{"input": stdin, "expected_output": solve(slug, stdin), "is_hidden": True} for stdin in problem["hidden"]]
            inputs = [case["input"] for case in cases]
            assert len(set(inputs)) == len(inputs), f"{slug}: duplicate test inputs"
            assert len(problem["hidden"]) >= 5, f"{slug}: needs at least 5 hidden cases"

            existing = [item for item in existing if item["slug"] != slug]
            existing.append(
                {
                    "title": problem["title"],
                    "slug": slug,
                    "difficulty": problem["difficulty"],
                    "order_within_topic": problem["order"],
                    "is_flagship": False,
                    "description": problem["description"],
                    "constraints": problem["constraints"],
                    "examples": examples,
                    "test_cases": cases,
                }
            )
            entries[slug] = problem["entry"]
            largest = max(len(stdin) for stdin in inputs)
            print(f"{slug}: {len(cases)} cases, largest input {largest:,} chars")
            for example in examples:
                print(f"    {example['input'][:70].replace(chr(10), ' | ')}  ->  {example['output'][:60]}")
        existing.sort(key=lambda item: item["order_within_topic"])
        path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", "utf-8")

    entries_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", "utf-8")
