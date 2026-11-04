"""Turns Pydantic's validation errors into sentences people can act on.

FastAPI's default 422 body says things like "String should match pattern '^[A-Za-z0-9_-]{3,32}$'". The handler in
main.py replaces it with {"detail": "<one readable sentence per problem>", "errors": [{"field", "message"}]}; the
frontend shows `detail`.
"""
import re

LABELS = {
    "username": "Username",
    "email": "Email",
    "password": "Password",
    "current_password": "Current password",
    "new_password": "New password",
    "title": "Title",
    "slug": "Slug",
    "topic_slug": "Topic",
    "problem_slug": "Problem",
    "name": "Name",
    "difficulty": "Difficulty",
    "description": "Statement",
    "order": "Position",
    "order_within_topic": "Position in topic",
    "entry": "How the code is called",
    "code": "Code",
    "language": "Language",
    "mode": "Mode",
    "custom_inputs": "Custom test cases",
    "input": "Input",
    "expected_output": "Expected output",
    "output": "Output",
    "time_complexity": "Time complexity",
    "space_complexity": "Space complexity",
    "line_notes": "Line notes",
    "role": "Role",
    "portal": "Sign-in type",
    "limit": "Limit",
    "offset": "Offset",
}

SLUG_RULE = "Use lowercase letters, numbers and single hyphens, like two-sum."
PATTERNS = {
    "username": "Usernames are 3 to 32 characters and can use letters, numbers, hyphens (-) and underscores (_).",
    "slug": SLUG_RULE,
    "topic_slug": SLUG_RULE,
    "problem_slug": SLUG_RULE,
}
EMAIL = "Enter an email address like name@example.com."


def _field(loc: tuple) -> tuple[str, str]:
    """(key, readable label) for an error location such as ("body", "examples", 0, "input")."""
    names = [part for part in loc if isinstance(part, str) and part not in ("body", "query", "path", "header")]
    key = names[-1] if names else ""
    label = LABELS.get(key, key.replace("_", " ").capitalize() or "This value")
    index = next((part for part in reversed(loc) if isinstance(part, int)), None)
    if index is not None and len(names) > 1:
        parent = LABELS.get(names[-2], names[-2].replace("_", " ").rstrip("s").capitalize())
        label = f"{parent} {index + 1}: {label.lower()}"
    return key, label


def _sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    return text if text.endswith((".", "!", "?")) else text + "."


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def friendly(error: dict) -> tuple[str, str]:
    """(field, message) for one Pydantic error."""
    key, label = _field(tuple(error.get("loc", ())))
    kind = error.get("type", "")
    ctx = error.get("ctx") or {}

    if key == "email" and kind in ("value_error", "string_pattern_mismatch"):
        return key, EMAIL
    if kind == "missing":
        return key, f"{label} is required."
    if kind == "string_pattern_mismatch":
        return key, PATTERNS.get(key, f"{label} isn't in the right format.")
    if kind == "string_too_short":
        minimum = ctx.get("min_length", 1)
        return key, f"{label} can't be empty." if minimum <= 1 else f"{label} needs at least {_plural(minimum, 'character')}."
    if kind == "string_too_long":
        return key, f"{label} can be at most {_plural(ctx.get('max_length', 0), 'character')}."
    if kind == "too_short":
        return key, f"{label} needs at least {_plural(ctx.get('min_length', 1), 'item')}."
    if kind == "too_long":
        return key, f"{label} can have at most {_plural(ctx.get('max_length', 0), 'item')}."
    if kind in ("literal_error", "enum"):
        options = re.findall(r"'([^']*)'", str(ctx.get("expected", "")))
        choices = ", ".join(options[:-1]) + f" or {options[-1]}" if len(options) > 1 else (options[0] if options else "")
        return key, f"{label} must be {choices}." if choices else f"{label} isn't one of the allowed values."
    if kind in ("int_parsing", "int_type", "int_from_float"):
        return key, f"{label} must be a whole number."
    if kind in ("greater_than_equal", "greater_than"):
        return key, f"{label} must be {ctx.get('ge', ctx.get('gt'))} or more."
    if kind in ("less_than_equal", "less_than"):
        return key, f"{label} must be {ctx.get('le', ctx.get('lt'))} or less."
    if kind in ("bool_parsing", "bool_type"):
        return key, f"{label} must be true or false."
    if kind in ("string_type", "dict_type", "list_type", "model_type", "model_attributes_type"):
        return key, f"{label} has the wrong kind of value."
    if kind == "json_invalid":
        return key, "The request couldn't be read. Please try again."
    if kind in ("value_error", "assertion_error"):
        message = str(error.get("msg", "")).removeprefix("Value error, ").removeprefix("Assertion failed, ")
        return key, _sentence(message)
    return key, _sentence(f"{label}: {error.get('msg', 'invalid value')}")


def friendly_errors(errors: list[dict]) -> dict:
    items = []
    for error in errors:
        field, message = friendly(error)
        if message not in (item["message"] for item in items):
            items.append({"field": field, "message": message})
    return {"detail": " ".join(item["message"] for item in items[:3]), "errors": items}
