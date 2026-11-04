import pytest

from app.judge import case_verdict, outputs_match, overall_verdict


@pytest.mark.parametrize(
    "actual,expected",
    [
        ("[1, 3]\n", "[1,3]"),
        ("  8  ", "8"),
        ("True", "true"),
        ("false\n", "false"),
        ("[6.500001,4]", "[6.5,4.0]"),
        ("hello  world", "hello world"),
    ],
)
def test_equivalent_outputs_match(actual, expected):
    assert outputs_match(actual, expected)


@pytest.mark.parametrize(
    "actual,expected",
    [
        ("[3,1]", "[1,3]"),
        ("[1,3,4]", "[1,3]"),
        ("1", "true"),
        ("true", "1"),
        ("8", "9"),
        ("7.9", "8.0"),
        ("", "8"),
        ("NaN", "1.0"),
        ("1e999", "1.0"),
        ("[" * 100_000, "[1]"),
        ("9" * 10_000, "8"),
    ],
)
def test_different_outputs_do_not_match(actual, expected):
    assert not outputs_match(actual, expected)


def test_case_verdicts():
    assert case_verdict("ok", "1", "1") == "Accepted"
    assert case_verdict("ok", "2", "1") == "Wrong Answer"
    assert case_verdict("tle", "1", "1") == "TLE"
    assert case_verdict("runtime_error", "1", "1") == "Runtime Error"


def test_first_failure_decides():
    assert overall_verdict(["Accepted", "Accepted"]) == "Accepted"
    assert overall_verdict(["Accepted", "TLE", "Wrong Answer"]) == "TLE"
