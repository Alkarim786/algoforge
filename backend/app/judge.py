"""Compares program output to expected output, independent of the language's print formatting."""
import json
import math
from typing import Any

from app.evaluation import ACCEPTED, FINISHED, RUNTIME_ERROR, TLE, WRONG_ANSWER

FLOAT_TOLERANCE = 1e-5


def _parse(text: str) -> tuple[bool, Any]:
    stripped = text.strip()
    # Python prints True/False where other languages print true/false.
    if stripped in ("True", "False"):
        stripped = stripped.lower()
    try:
        return True, json.loads(stripped)
    except (ValueError, RecursionError):
        return False, None


def _equal(actual: Any, expected: Any) -> bool:
    # bool is an int subclass in Python, but `true` is not a correct answer for 1.
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        if isinstance(actual, int) and isinstance(expected, int):
            return actual == expected
        try:
            return math.isclose(actual, expected, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE)
        except OverflowError:
            return False
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(map(_equal, actual, expected))
    return type(actual) is type(expected) and actual == expected


def outputs_match(actual: str, expected: str) -> bool:
    actual_ok, actual_value = _parse(actual)
    expected_ok, expected_value = _parse(expected)
    if actual_ok and expected_ok:
        try:
            return _equal(actual_value, expected_value)
        except RecursionError:
            return False
    return actual.split() == expected.split()


def case_verdict(outcome: str, actual: str, expected: str) -> str:
    if outcome == "tle":
        return TLE
    if outcome == "runtime_error":
        return RUNTIME_ERROR
    return ACCEPTED if outputs_match(actual, expected) else WRONG_ANSWER


def custom_case_verdict(outcome: str) -> str:
    """A custom input has no expected output, so only a crash or timeout can fail it."""
    return {"tle": TLE, "runtime_error": RUNTIME_ERROR}.get(outcome, FINISHED)


def overall_verdict(verdicts: list[str]) -> str:
    """The first failing case decides, in test case order."""
    for verdict in verdicts:
        if verdict not in (ACCEPTED, FINISHED):
            return verdict
    return FINISHED if FINISHED in verdicts else ACCEPTED
