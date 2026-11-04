"""Keeps topic notes to one format, and makes sure every Python snippet in them still runs."""
import re
from pathlib import Path

import pytest

NOTES_DIR = Path(__file__).resolve().parents[1] / "content" / "notes"
NOTES = sorted(NOTES_DIR.glob("*.md"))
REQUIRED_SECTIONS = ["## The idea", "## Built-in functions", "## Pitfalls"]
PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def test_there_are_notes():
    assert NOTES


@pytest.mark.parametrize("path", NOTES, ids=lambda path: path.stem)
def test_notes_follow_the_format(path):
    text = path.read_text("utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in text, f"missing {section!r}"
    assert re.search(r"^## Worked example: ", text, re.MULTILINE), "missing a worked example"
    # The page shows the topic name as the title, so notes start at the second level.
    assert not re.search(r"^# ", text, re.MULTILINE), "use ## headings, not #"
    table = text.split("## Built-in functions", 1)[1]
    assert "| Python | C++ | Java |" in table, "built-ins need a column per language"


@pytest.mark.parametrize("path", NOTES, ids=lambda path: path.stem)
def test_python_snippets_run(path):
    blocks = PYTHON_BLOCK.findall(path.read_text("utf-8"))
    assert blocks, "expected at least one runnable Python example"
    namespace = {}
    # Blocks run in order and share a namespace, the way a reader goes through the page.
    for block in blocks:
        exec(compile(block, f"{path.name}", "exec"), namespace)
