"""Checks for content typed in by admins, so a bad entry or test case is rejected on save instead of
breaking the judge later. The shapes are the ones described in app/drivers.py."""
import json
import re

# Types end up in generated starter code, so only plain type expressions are allowed.
TYPE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\[\], ]{0,59}$")
NORMALIZE_OPTIONS = (None, "sorted", "sorted_lists")


def _identifier(value, what: str) -> None:
    if not isinstance(value, str) or not value.isidentifier():
        raise ValueError(f"{what} must be a Python identifier, got {value!r}")


def _type(value, what: str) -> None:
    if not isinstance(value, str) or not TYPE_PATTERN.match(value):
        raise ValueError(f"{what} must be a type such as 'List[int]', got {value!r}")


def _params(params, what: str) -> None:
    if not isinstance(params, list):
        raise ValueError(f"{what} params must be a list")
    for index, param in enumerate(params):
        if not isinstance(param, dict) or set(param) != {"name", "type"}:
            raise ValueError(f"{what} param {index + 1} must be {{\"name\": ..., \"type\": ...}}")
        _identifier(param["name"], f"{what} param name")
        _type(param["type"], f"{what} param '{param['name']}' type")


def _keys(entry: dict, required: set, optional: set = frozenset()) -> None:
    missing = required - set(entry)
    unknown = set(entry) - required - optional
    if missing:
        raise ValueError(f"entry is missing {sorted(missing)}")
    if unknown:
        raise ValueError(f"entry has unknown keys {sorted(unknown)}")


def validate_entry(entry) -> None:
    """Raises ValueError if `entry` isn't one of the shapes the driver understands."""
    if entry is None:
        return
    if not isinstance(entry, dict):
        raise ValueError("entry must be a JSON object")
    if "class" in entry:
        _keys(entry, {"class", "operations"})
        _identifier(entry["class"], "class")
        operations = entry["operations"]
        if not isinstance(operations, dict) or not operations:
            raise ValueError("operations must be a non-empty object")
        for name, operation in operations.items():
            if not isinstance(operation, dict):
                raise ValueError(f"operation '{name}' must be an object")
            _keys(operation, {"method"}, {"params", "returns"})
            _identifier(operation["method"], f"operation '{name}' method")
            _params(operation.get("params", []), f"operation '{name}'")
            if "returns" in operation:
                _type(operation["returns"], f"operation '{name}' returns")
    elif "codec" in entry:
        _keys(entry, {"codec", "encode", "decode", "params", "returns"})
        for key in ("codec", "encode", "decode"):
            _identifier(entry[key], key)
        _params(entry["params"], "codec")
        if len(entry["params"]) != 1:
            raise ValueError("a codec takes exactly one param")
        _type(entry["returns"], "returns")
    else:
        _keys(entry, {"method", "params", "returns"}, {"cycle", "normalize"})
        _identifier(entry["method"], "method")
        _params(entry["params"], "method")
        _type(entry["returns"], "returns")
        if entry.get("normalize") not in NORMALIZE_OPTIONS:
            raise ValueError(f"normalize must be one of {NORMALIZE_OPTIONS[1:]}")
        if "cycle" in entry and (entry["cycle"] is not True or len(entry["params"]) != 1):
            raise ValueError("cycle must be true, with exactly one ListNode param")


def _expected_lines(entry: dict) -> int:
    if "class" in entry or "codec" in entry:
        return 1
    if entry.get("cycle"):
        return 2
    return len(entry["params"])


def check_case(entry: dict | None, input_text: str, expected_output: str) -> tuple[str, str]:
    """Returns the case's (input, expected_output) in the stored format, or raises ValueError.

    Problems with an entry take one JSON value per input line and a JSON answer; both are stored compact.
    Problems without one are plain stdin/stdout programs, so the text is kept as typed.
    """
    if entry is None:
        return input_text.strip("\n"), expected_output.strip()
    lines = [line for line in input_text.split("\n") if line.strip()]
    values = []
    for number, line in enumerate(lines, start=1):
        try:
            values.append(json.loads(line))
        except ValueError:
            raise ValueError(f"input line {number} isn't valid JSON: {line.strip()[:60]}") from None
    wanted = _expected_lines(entry)
    if len(values) != wanted:
        raise ValueError(f"input needs {wanted} line{'s' if wanted != 1 else ''} (one JSON value each), got {len(values)}")
    if "class" in entry:
        calls = values[0]
        if not isinstance(calls, list) or not all(isinstance(call, list) and call for call in calls):
            raise ValueError('input must be a list of calls, such as [["insert", "apple"], ["search", "apple"]]')
        unknown = sorted({str(call[0]) for call in calls} - set(entry["operations"]))
        if unknown:
            raise ValueError(f"unknown operations {unknown}; this class has {sorted(entry['operations'])}")
    try:
        expected = json.loads(expected_output)
    except ValueError:
        raise ValueError("expected output isn't valid JSON (use true/false, double-quoted strings, [ ])") from None
    compact = lambda value: json.dumps(value, separators=(",", ":"))  # noqa: E731
    return "\n".join(compact(value) for value in values), compact(expected)
