"""Turns LeetCode-style user code (class Solution) into a program the sandbox can run.

A problem's `entry` describes how to call the code:
  {"method": "twoSum", "params": [{"name": "nums", "type": "List[int]"}, ...], "returns": "List[int]"}
  {"class": "MedianFinder", "operations": {"add": {"method": "addNum", "params": ...}, ...}}

ListNode/TreeNode types are built from and converted back to JSON arrays. `"returns": "None"` means the
method edits its first argument in place, and that argument is the answer. `"normalize": "sorted_lists"`
accepts a list of lists in any order (each inner list is sorted, then the whole list); `"sorted"` sorts
only the outer list.

Other shapes:
  "List[Optional[ListNode]]"   a list of linked lists, given as a list of arrays
  "Optional[Node]"             a graph, given as an adjacency list (node values 1..n); a returned graph must
                               be a copy, not the input's own nodes
  "TreeNodeRef"                a node of the tree passed as the first argument, given by its value
  {"cycle": true, ...}         a linked list given as values plus the index its tail links back to (-1: none)
  {"codec": "Codec", "encode": ..., "decode": ...}   decode(encode(value)) must rebuild the value

The answer is printed after a marker line, so anything the user prints stays debug output.
"""
import json

RESULT_MARKER = "\x1e__RESULT__\x1e"

_WRAPPER = r'''
import bisect, collections, functools, heapq, itertools, json, math, string, sys
from collections import Counter, defaultdict, deque
from typing import *

sys.setrecursionlimit(20000)


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def _build_list(values):
    head = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def _list_values(node):
    values = []
    while node:
        values.append(node.val)
        node = node.next
        if len(values) > 200_000:
            raise ValueError("the returned list never ends: it contains a cycle")
    return values


def _build_tree(values):
    if not values:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if values[i] is not None:
            node.left = TreeNode(values[i])
            queue.append(node.left)
        i += 1
        if i < len(values) and values[i] is not None:
            node.right = TreeNode(values[i])
            queue.append(node.right)
        i += 1
    return root


def _tree_values(root):
    values = []
    queue = deque([root] if root else [])
    while queue:
        node = queue.popleft()
        values.append(node.val if node else None)
        if node:
            queue.extend((node.left, node.right))
    while values and values[-1] is None:
        values.pop()
    return values


class Node:
    """A graph node, for problems such as Clone Graph."""

    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


_ORIGINAL_GRAPH_NODES = set()


def _build_graph(adjacency):
    """adjacency[i] lists the neighbours (1-based values) of the node with value i + 1."""
    if not adjacency:
        return None
    nodes = [Node(i + 1) for i in range(len(adjacency))]
    for node, neighbours in zip(nodes, adjacency):
        node.neighbors = [nodes[j - 1] for j in neighbours]
    _ORIGINAL_GRAPH_NODES.update(id(node) for node in nodes)
    return nodes[0]


def _graph_values(node):
    if node is None:
        return []
    found = {node.val: node}
    queue = deque([node])
    while queue:
        for neighbour in queue.popleft().neighbors:
            if neighbour.val not in found:
                found[neighbour.val] = neighbour
                queue.append(neighbour)
    if any(id(item) in _ORIGINAL_GRAPH_NODES for item in found.values()):
        return "returned the original nodes instead of a copy"
    return [[neighbour.val for neighbour in found[value].neighbors] for value in range(1, len(found) + 1)]


def _find_tree_node(root, value):
    queue = deque([root] if root else [])
    while queue:
        node = queue.popleft()
        if node.val == value:
            return node
        queue.extend(child for child in (node.left, node.right) if child)
    return None


def _from_json(value, type_name, args=()):
    if type_name.startswith("List[") and "ListNode" in type_name:
        return [_build_list(values) for values in value]
    if "ListNode" in type_name:
        return _build_list(value)
    if type_name == "TreeNodeRef":
        # A node inside the tree passed as the first argument, given by its (unique) value.
        return _find_tree_node(args[0], value)
    if "TreeNode" in type_name:
        return _build_tree(value)
    if type_name in ("Node", "Optional[Node]"):
        return _build_graph(value)
    return value


def _to_json(value, type_name):
    if "ListNode" in type_name:
        return _list_values(value)
    if type_name == "TreeNodeRef":
        return value.val if value else None
    if "TreeNode" in type_name:
        return _tree_values(value)
    if type_name in ("Node", "Optional[Node]"):
        return _graph_values(value)
    return value


_ENTRY = json.loads(__ENTRY__)
# Read up front, so a stray input() in user code can't consume the test case.
_LINES = [line for line in sys.stdin.read().split("\n") if line.strip()]
exec(compile(__CODE__, "solution.py", "exec"))


def _solve():
    if "class" in _ENTRY:
        instance = globals()[_ENTRY["class"]]()
        results = []
        for name, *args in json.loads(_LINES[0]):
            value = getattr(instance, _ENTRY["operations"][name]["method"])(*args)
            if value is not None:
                results.append(value)
        return results

    params = _ENTRY["params"]

    if "codec" in _ENTRY:
        # Round trip: the encoded form must be a real string, and decoding it must rebuild the value.
        codec = globals()[_ENTRY["codec"]]()
        encoded = getattr(codec, _ENTRY["encode"])(_from_json(json.loads(_LINES[0]), params[0]["type"]))
        if not isinstance(encoded, str):
            raise TypeError(f"{_ENTRY['encode']} must return a str, not {type(encoded).__name__}")
        return _to_json(getattr(codec, _ENTRY["decode"])(encoded), _ENTRY["returns"])

    if _ENTRY.get("cycle"):
        # Line 1 is the list's values; line 2 is the index the tail links back to (-1 for no cycle).
        values, position = json.loads(_LINES[0]), json.loads(_LINES[1])
        head = _build_list(values)
        if position >= 0:
            tail, target = head, None
            index = 0
            while tail.next:
                if index == position:
                    target = tail
                tail, index = tail.next, index + 1
            tail.next = target if target else tail
        return getattr(Solution(), _ENTRY["method"])(head)

    args = []
    for line, param in zip(_LINES, params, strict=True):
        args.append(_from_json(json.loads(line), param["type"], args))
    value = getattr(Solution(), _ENTRY["method"])(*args)
    if _ENTRY["returns"] == "None":
        return _to_json(args[0], params[0]["type"])
    return _to_json(value, _ENTRY["returns"])


_answer = _solve()
if _ENTRY.get("normalize") == "sorted_lists":
    # Order doesn't matter for this problem, so compare a canonical form: each inner list sorted, then the outer list.
    _answer = sorted(sorted(item) for item in _answer)
elif _ENTRY.get("normalize") == "sorted":
    # Only the order of the items doesn't matter (each item, such as a cell [r, c], keeps its own order).
    _answer = sorted(_answer)
sys.stdout.write("\n" + __MARKER__ + json.dumps(_answer, separators=(",", ":")) + "\n")
'''


def wrap(entry: dict | None, code: str) -> str:
    """Problems with no entry take a plain stdin/stdout program."""
    if entry is None:
        return code
    return (
        _WRAPPER.replace("__ENTRY__", repr(json.dumps(entry)))
        .replace("__MARKER__", repr(RESULT_MARKER))
        .replace("__CODE__", repr(code))
    )


def split_output(entry: dict | None, stdout: str) -> tuple[str, str]:
    """Returns (debug output, answer)."""
    if entry is None:
        return "", stdout
    debug, marker, answer = stdout.rpartition(RESULT_MARKER)
    if not marker:
        return stdout, ""
    return debug.rstrip("\n"), answer.strip()


def _shown_type(type_name: str) -> str:
    # TreeNodeRef is a driver detail; the user just receives a TreeNode.
    return type_name.replace("TreeNodeRef", "TreeNode")


def _signature(method: dict, returns: str | None) -> list[str]:
    params = "".join(f", {param['name']}: {_shown_type(param['type'])}" for param in method.get("params", []))
    arrow = f" -> {_shown_type(returns)}" if returns else ""
    return [f"    def {method['method']}(self{params}){arrow}:", "        pass"]


def starter_code(entry: dict | None) -> str:
    if entry is None:
        return "# Read the test case from stdin and print the answer.\n"
    if "codec" in entry:
        value_type = entry["params"][0]["type"]
        encode = {"method": entry["encode"], "params": entry["params"]}
        decode = {"method": entry["decode"], "params": [{"name": "data", "type": "str"}]}
        lines = [f"class {entry['codec']}:", *_signature(encode, "str"), "", *_signature(decode, value_type)]
    elif "class" in entry:
        lines = [f"class {entry['class']}:", "    def __init__(self):", "        pass"]
        for operation in entry["operations"].values():
            lines += ["", *_signature(operation, operation.get("returns"))]
    else:
        lines = ["class Solution:", *_signature(entry, entry["returns"])]
    return "\n".join(lines) + "\n"
