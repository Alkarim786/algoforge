"""Parses a problem's solution guide from content/solutions/<slug>.md.

Format (checked by tests/test_solutions.py):

    ## How to think
    <markdown; ```mermaid blocks render as diagrams>

    ## Approach 1: <title>
    <!-- approach: brute_force | time: O(n²) | space: O(1) -->
    <the idea, dry run, any markdown>
    ### Code
    ```python
    <code>
    ```
    ### Line by line
    - `1` <note about line 1>
    - `3-5` <note about lines 3 to 5>
    ### Flowchart
    ```mermaid
    <flowchart>
    ```

    ## Approach 2: <title>
    <!-- approach: optimized | ... -->
    ...
"""
import re

APPROACH_HEADING = re.compile(r"^## Approach \d+: (.+)$", re.MULTILINE)
META = re.compile(r"<!--\s*approach:\s*(brute_force|optimized)\s*\|\s*time:\s*(.+?)\s*\|\s*space:\s*(.+?)\s*-->")
LINE_NOTE = re.compile(r"^- `(\d+)(?:-(\d+))?` (.+)$", re.MULTILINE)


def _fenced(language: str, text: str, where: str) -> str:
    match = re.search(rf"```{language}\n(.*?)```", text, re.DOTALL)
    if match is None:
        raise ValueError(f"{where}: expected a ```{language} block")
    return match.group(1)


def _section(body: str, heading: str, where: str) -> tuple[str, str]:
    before, found, after = body.partition(f"### {heading}")
    if not found:
        raise ValueError(f"{where}: missing '### {heading}'")
    return before, after


def parse_solution(text: str) -> dict:
    head, *parts = APPROACH_HEADING.split(text)
    _, found, thinking = head.partition("## How to think")
    if not found:
        raise ValueError("missing '## How to think'")

    approaches = []
    for order, (title, body) in enumerate(zip(parts[0::2], parts[1::2]), start=1):
        where = f"approach {order} ({title.strip()})"
        meta = META.search(body)
        if meta is None:
            raise ValueError(f"{where}: missing '<!-- approach: ... | time: ... | space: ... -->'")
        idea, rest = _section(body[meta.end():], "Code", where)
        code_part, rest = _section(rest, "Line by line", where)
        notes_part, flowchart_part = _section(rest, "Flowchart", where)

        code = _fenced("python", code_part, where)
        line_count = len(code.rstrip("\n").split("\n"))
        line_notes = []
        for match in LINE_NOTE.finditer(notes_part):
            start = int(match.group(1))
            end = int(match.group(2) or start)
            if not 1 <= start <= end <= line_count:
                raise ValueError(f"{where}: line note `{match.group(0)[2:]}` is outside lines 1-{line_count}")
            line_notes.append({"start": start, "end": end, "note": match.group(3).strip()})
        if not line_notes:
            raise ValueError(f"{where}: no line notes found")

        approaches.append(
            {
                "approach_type": meta.group(1),
                "title": title.strip(),
                "time_complexity": meta.group(2),
                "space_complexity": meta.group(3),
                "explanation": idea.strip(),
                "code": {"python": code},
                "line_notes": line_notes,
                "flowchart_mermaid": _fenced("mermaid", flowchart_part, where).strip(),
                "order": order,
            }
        )

    types = [approach["approach_type"] for approach in approaches]
    if sorted(types) != ["brute_force", "optimized"]:
        raise ValueError(f"expected one brute_force and one optimized approach, got {types}")
    return {"thinking": thinking.strip(), "approaches": approaches}
