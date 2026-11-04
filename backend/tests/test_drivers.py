"""Runs every flagship problem's driver for real (as a local subprocess, no sandbox needed)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app import drivers
from app.seed import load_problems
from tests.reference_solutions import SOLUTIONS

PROBLEMS = load_problems()
REFERENCE_SOURCE = (Path(__file__).parent / "reference_solutions.py").read_text("utf-8")
TWO_SUM = next(p for p in PROBLEMS if p.slug == "two-sum").entry


def execute(entry, code, stdin):
    program = drivers.wrap(entry, code)
    return subprocess.run([sys.executable, "-c", program], input=stdin, capture_output=True, text=True, timeout=20)


def adapter(entry, slug):
    """A class Solution that converts node types to plain values and calls the reference solution."""
    function = SOLUTIONS[slug].__name__
    if "class" in entry:
        return f"""{REFERENCE_SOURCE}
class MedianFinder:
    def __init__(self):
        self.ops = []
    def addNum(self, num):
        self.ops.append(["add", num])
    def findMedian(self):
        return {function}(self.ops + [["median"]])[0]
"""
    convert = "[_to_json(a, p['type']) for a, p in zip(args, _ENTRY['params'])]"
    if entry["returns"] == "None" and "ListNode" in entry["params"][0]["type"]:
        # In-place linked-list problems: write the reference's values back into the existing nodes.
        body = f"node = args[0]\n        for value in {function}(*{convert}):\n            node.val, node = value, node.next"
    elif entry["returns"] == "None":
        body = f"args[0][:] = {function}(*{convert})"
    else:
        body = f"return _from_json({function}(*{convert}), {entry['returns']!r})"
    return f"{REFERENCE_SOURCE}\nclass Solution:\n    def {entry['method']}(self, *args):\n        {body}\n"


def test_every_flagship_has_an_entry():
    assert all(problem.entry for problem in PROBLEMS)


def adaptable(problem):
    """The generic adapter only covers plain method calls and MedianFinder. The other shapes (cycles, codecs,
    graphs, design classes) are exercised end to end by test_solutions.py, using each guide's own code."""
    entry = problem.entry
    if "cycle" in entry or "codec" in entry:
        return False
    if "class" in entry:
        return entry["class"] == "MedianFinder"
    types = [param["type"] for param in entry["params"]] + [entry["returns"]]
    return not any(t in ("TreeNodeRef", "Node", "Optional[Node]") or t.startswith("List[Optional[ListNode") for t in types)


@pytest.mark.parametrize("problem", [p for p in PROBLEMS if adaptable(p)], ids=lambda p: p.slug)
def test_driver_produces_expected_output_for_examples(problem):
    code = adapter(problem.entry, problem.slug)
    for example in problem.examples:
        completed = execute(problem.entry, code, example.input)
        assert completed.returncode == 0, completed.stderr
        _, answer = drivers.split_output(problem.entry, completed.stdout)
        assert json.loads(answer) == json.loads(example.output), example.input


@pytest.mark.parametrize("problem", PROBLEMS, ids=lambda p: p.slug)
def test_starter_code_compiles_and_names_the_method(problem):
    starter = drivers.starter_code(problem.entry)
    compile(starter, "starter", "exec")
    entry = problem.entry
    if "codec" in entry:
        methods = [entry["encode"], entry["decode"]]
    elif "class" in entry:
        methods = [op["method"] for op in entry["operations"].values()]
    else:
        methods = [entry["method"]]
    assert all(f"def {method}(self" in starter for method in methods)


def test_prints_stay_out_of_the_answer():
    code = "class Solution:\n    def twoSum(self, nums, target):\n        print('debug', nums)\n        return [0, 1]\n"
    completed = execute(TWO_SUM, code, "[7,7]\n14")
    assert drivers.split_output(TWO_SUM, completed.stdout) == ("debug [7, 7]", "[0,1]")


def test_traceback_uses_the_users_line_numbers():
    code = "class Solution:\n    def twoSum(self, nums, target):\n        x = 1\n        raise ValueError('boom')\n"
    completed = execute(TWO_SUM, code, "[7,7]\n14")
    assert completed.returncode != 0
    assert 'File "solution.py", line 4' in completed.stderr


def test_user_code_with_quotes_and_placeholders_survives_wrapping():
    code = (
        "class Solution:\n    def twoSum(self, nums, target):\n"
        "        print(\"__CODE__ ''' __ENTRY__ __MARKER__ \\n\")\n        return [0, 1]\n"
    )
    completed = execute(TWO_SUM, code, "[7,7]\n14")
    assert completed.returncode == 0, completed.stderr
    assert drivers.split_output(TWO_SUM, completed.stdout)[1] == "[0,1]"


def test_missing_answer_is_not_treated_as_output():
    assert drivers.split_output(TWO_SUM, "only debug") == ("only debug", "")


def test_cycle_input_links_the_tail():
    entry = {"method": "hasCycle", "params": [{"name": "head", "type": "Optional[ListNode]"}], "returns": "bool", "cycle": True}
    code = "class Solution:\n    def hasCycle(self, head):\n        seen = set()\n        while head:\n            if id(head) in seen:\n                return True\n            seen.add(id(head))\n            head = head.next\n        return False\n"
    for stdin, expected in (("[1,2,3]\n0", "true"), ("[1,2,3]\n2", "true"), ("[1,2,3]\n-1", "false"), ("[]\n-1", "false")):
        _, answer = drivers.split_output(entry, execute(entry, code, stdin).stdout)
        assert answer == expected, stdin


def test_codec_round_trip_requires_a_string():
    entry = {"codec": "Codec", "encode": "encode", "decode": "decode", "params": [{"name": "strs", "type": "List[str]"}], "returns": "List[str]"}
    good = "class Codec:\n    def encode(self, strs):\n        return json.dumps(strs)\n    def decode(self, data):\n        return json.loads(data)\n"
    cheat = "class Codec:\n    def encode(self, strs):\n        return strs\n    def decode(self, data):\n        return data\n"
    assert drivers.split_output(entry, execute(entry, good, '["a",""]').stdout)[1] == '["a",""]'
    completed = execute(entry, cheat, '["a",""]')
    assert completed.returncode != 0 and "must return a str" in completed.stderr


def test_graph_clone_must_not_reuse_nodes():
    entry = {"method": "cloneGraph", "params": [{"name": "node", "type": "Optional[Node]"}], "returns": "Optional[Node]"}
    honest = "class Solution:\n    def cloneGraph(self, node):\n        copies = {}\n        def copy(n):\n            if n.val not in copies:\n                copies[n.val] = Node(n.val)\n                copies[n.val].neighbors = [copy(m) for m in n.neighbors]\n            return copies[n.val]\n        return copy(node) if node else None\n"
    lazy = "class Solution:\n    def cloneGraph(self, node):\n        return node\n"
    stdin = "[[2,3],[1,3],[1,2]]"
    assert drivers.split_output(entry, execute(entry, honest, stdin).stdout)[1] == "[[2,3],[1,3],[1,2]]"
    assert "instead of a copy" in drivers.split_output(entry, execute(entry, lazy, stdin).stdout)[1]


def test_tree_node_reference_and_starter_type():
    entry = {
        "method": "lowestCommonAncestor",
        "params": [{"name": "root", "type": "TreeNode"}, {"name": "p", "type": "TreeNodeRef"}, {"name": "q", "type": "TreeNodeRef"}],
        "returns": "TreeNodeRef",
    }
    code = "class Solution:\n    def lowestCommonAncestor(self, root, p, q):\n        return p\n"
    assert drivers.split_output(entry, execute(entry, code, "[6,2,8]\n2\n8").stdout)[1] == "2"
    assert "TreeNodeRef" not in drivers.starter_code(entry)


def test_returned_cycle_is_an_error_not_a_hang():
    entry = {"method": "reverseList", "params": [{"name": "head", "type": "Optional[ListNode]"}], "returns": "Optional[ListNode]"}
    code = "class Solution:\n    def reverseList(self, head):\n        head.next.next = head\n        return head\n"
    completed = execute(entry, code, "[1,2]")
    assert completed.returncode != 0 and "cycle" in completed.stderr


def test_problem_without_entry_is_a_plain_program():
    assert drivers.wrap(None, "print(1)") == "print(1)"
    assert drivers.split_output(None, "1\n") == ("", "1\n")
