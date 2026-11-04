"""Linked List and Graph problems beyond the flagship pairs. Run: python -m scripts.batch_list_graph"""
import random
import string

from scripts.problem_tool import add, lines

rng = random.Random(5005)


def sorted_values(count, low=-10**4, high=10**4):
    return sorted(rng.randint(low, high) for _ in range(count))


def random_connected_graph(n, extra_edges):
    """Adjacency list (1-based) of a connected undirected graph: a random spanning tree plus extra edges."""
    edges = {(rng.randrange(i) + 1, i + 1) for i in range(1, n)}
    while len(edges) < n - 1 + extra_edges:
        a, b = rng.sample(range(1, n + 1), 2)
        edges.add((min(a, b), max(a, b)))
    adjacency = [[] for _ in range(n)]
    for a, b in sorted(edges):
        adjacency[a - 1].append(b)
        adjacency[b - 1].append(a)
    return adjacency


def random_tree_edges(n):
    edges = [[rng.randrange(i), i] for i in range(1, n)]
    rng.shuffle(edges)
    return edges


def alien_words(alphabet, count, length):
    """Words sorted by a secret alphabet order, so the input is always consistent."""
    rank = {char: i for i, char in enumerate(alphabet)}
    words = {"".join(rng.choice(alphabet) for _ in range(rng.randint(1, length))) for _ in range(count)}
    return sorted(words, key=lambda word: [rank[char] for char in word])


ADJACENCY_NOTE = (
    "The graph is given as an adjacency list: line `i` (counting from 1) lists the neighbours of the node with "
    "value `i`. Nodes are numbered `1` to `n`, and the graph is connected. Your function receives node `1` "
    "(or `None` for an empty graph)."
)

PROBLEMS = [
    {
        "topic": "linked-list",
        "title": "Linked List Cycle",
        "slug": "linked-list-cycle",
        "difficulty": "Easy",
        "order": 2,
        "entry": {
            "method": "hasCycle",
            "params": [{"name": "head", "type": "Optional[ListNode]"}],
            "returns": "bool",
            "cycle": True,
        },
        "description": "Given the head of a linked list, decide whether it contains a **cycle**: some node whose `next` pointer leads back to an earlier node, so walking the list never reaches the end.\n\nCan you do it with O(1) extra memory?\n\n**Input format:** line 1 is the list's values as a JSON array; line 2 is `pos`, the index of the node the tail links back to, or `-1` for no cycle. `pos` is only used to build the test list; your function just receives `head`.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 0 <= number of nodes <= 10^4\n- -10^5 <= node value <= 10^5\n- `pos` is `-1` or a valid index",
        "examples": [
            (lines([3, 8, 1, 6], 1), "The tail (6) links back to the node at index 1 (8)."),
            (lines([5, 9], -1), "The list ends normally."),
            (lines([7], 0), "A single node pointing to itself."),
        ],
        "hidden": [
            lines([], -1),
            lines([1], -1),
            lines([1, 2], 0),
            lines(list(range(10_000)), 9_999),  # the tail points to itself
            lines(list(range(10_000)), 0),
            lines(list(range(10_000)), -1),
            lines([rng.randint(-10**5, 10**5) for _ in range(10_000)], 5_000),
        ],
    },
    {
        "topic": "linked-list",
        "title": "Merge k Sorted Lists",
        "slug": "merge-k-sorted-lists",
        "difficulty": "Hard",
        "order": 4,
        "entry": {
            "method": "mergeKLists",
            "params": [{"name": "lists", "type": "List[Optional[ListNode]]"}],
            "returns": "Optional[ListNode]",
        },
        "description": "You are given `k` linked lists, each sorted in non-decreasing order. Merge them into one sorted linked list and return its head.\n\n**Input format:** one line, a JSON array of lists, each written as an array of its values.\n\n**Output format:** the merged list's values as a JSON array.",
        "constraints": "- 0 <= k <= 10^4\n- 0 <= length of each list <= 500\n- Total number of nodes <= 10^4\n- -10^4 <= node value <= 10^4",
        "examples": [
            (lines([[1, 4, 7], [2, 5], [3, 6, 9]]), None),
            (lines([]), "No lists at all."),
            (lines([[], [2], []]), "Empty lists are allowed."),
        ],
        "hidden": [
            lines([[]]),
            lines([[1, 1, 1], [1, 1]]),
            lines([[-5, 0, 5], [-10, 10]]),
            lines([[value] for value in sorted_values(10_000)]),  # 10^4 single-node lists
            lines([sorted_values(500) for _ in range(20)]),
            lines([sorted_values(rng.randint(0, 20)) for _ in range(1_000)]),
        ],
    },
    {
        "topic": "linked-list",
        "title": "Remove Nth Node From End of List",
        "slug": "remove-nth-node-from-end-of-list",
        "difficulty": "Medium",
        "order": 5,
        "entry": {
            "method": "removeNthFromEnd",
            "params": [{"name": "head", "type": "Optional[ListNode]"}, {"name": "n", "type": "int"}],
            "returns": "Optional[ListNode]",
        },
        "description": "Remove the `n`-th node **counting from the end** of a linked list (`n = 1` is the last node), and return the head of the changed list.\n\nCan you do it in one pass?\n\n**Input format:** line 1 is the list's values as a JSON array; line 2 is `n`.\n\n**Output format:** the remaining values as a JSON array.",
        "constraints": "- 1 <= number of nodes <= 10^4\n- 0 <= node value <= 100\n- 1 <= n <= number of nodes",
        "examples": [
            (lines([10, 20, 30, 40, 50], 2), "The second from the end is 40."),
            (lines([7], 1), "Removing the only node leaves an empty list."),
            (lines([4, 9], 2), "n equal to the length removes the head."),
        ],
        "hidden": [
            lines([1, 2], 1),
            lines([1, 2, 3], 3),
            lines([5, 5, 5, 5], 2),
            lines([rng.randint(0, 100) for _ in range(10_000)], 1),
            lines([rng.randint(0, 100) for _ in range(10_000)], 10_000),
            lines([rng.randint(0, 100) for _ in range(9_999)], 4_321),
        ],
    },
    {
        "topic": "linked-list",
        "title": "Reorder List",
        "slug": "reorder-list",
        "difficulty": "Medium",
        "order": 6,
        "entry": {"method": "reorderList", "params": [{"name": "head", "type": "Optional[ListNode]"}], "returns": "None"},
        "description": "A list `L0 → L1 → … → Ln` must be rearranged **in place** into `L0 → Ln → L1 → Ln−1 → L2 → Ln−2 → …`: alternately taking from the front and the back. Change the links, not the values.\n\n**Input format:** one line, the list's values as a JSON array.\n\n**Output format:** the reordered values as a JSON array.",
        "constraints": "- 1 <= number of nodes <= 5 * 10^4\n- 1 <= node value <= 1000",
        "examples": [
            (lines([1, 2, 3, 4, 5]), "Front, back, front, back: 1, 5, 2, 4, then 3 in the middle."),
            (lines([1, 2, 3, 4]), None),
            (lines([9]), None),
        ],
        "hidden": [
            lines([1, 2]),
            lines([3, 1, 2]),
            lines([5, 5, 5, 5, 5]),
            lines(list(range(1, 1001)) * 50),
            lines([rng.randint(1, 1000) for _ in range(49_999)]),
        ],
    },
    {
        "topic": "graph",
        "title": "Clone Graph",
        "slug": "clone-graph",
        "difficulty": "Medium",
        "order": 1,
        "entry": {"method": "cloneGraph", "params": [{"name": "node", "type": "Optional[Node]"}], "returns": "Optional[Node]"},
        "description": "Return a **deep copy** of a connected undirected graph: brand-new `Node` objects with the same values and the same connections. The copy must not share any node with the original.\n\nEach `Node` has a `val` and a list `neighbors`.\n\n" + ADJACENCY_NOTE + "\n\n**Input format:** one line, the adjacency list as a JSON array.\n\n**Output format:** the copied graph's adjacency list.",
        "constraints": "- 0 <= number of nodes <= 100\n- Node values are 1 to n, unique\n- No repeated edges or self-loops; the graph is connected",
        "examples": [
            (lines([[2, 4], [1, 3], [2, 4], [1, 3]]), "A square: 1-2-3-4-1."),
            (lines([[]]), "One node with no neighbours."),
            (lines([]), "An empty graph."),
        ],
        "hidden": [
            lines([[2], [1]]),
            lines([[2, 3], [1, 3], [1, 2]]),
            lines([[2, 3, 4, 5], [1], [1], [1], [1]]),
            lines(random_connected_graph(100, 0)),
            lines(random_connected_graph(100, 300)),
            lines(random_connected_graph(60, 1_000)),
        ],
    },
    {
        "topic": "graph",
        "title": "Pacific Atlantic Water Flow",
        "slug": "pacific-atlantic-water-flow",
        "difficulty": "Medium",
        "order": 3,
        "entry": {
            "method": "pacificAtlantic",
            "params": [{"name": "heights", "type": "List[List[int]]"}],
            "returns": "List[List[int]]",
            "normalize": "sorted",
        },
        "description": "An island is a grid of land heights. The **Pacific** touches the top and left edges, and the **Atlantic** touches the bottom and right edges. Rain flows from a cell to a neighbour (up, down, left, right) whose height is **less than or equal** to its own, and from edge cells into the adjacent ocean.\n\nReturn every cell `[r, c]` from which water can reach **both** oceans, in any order.\n\n**Input format:** one line, `heights` as a JSON array of rows.\n\n**Output format:** a JSON array of `[r, c]` pairs. (The judge sorts your answer before comparing.)",
        "constraints": "- 1 <= rows, cols <= 200\n- 0 <= heights[r][c] <= 10^5",
        "examples": [
            (lines([[1, 2, 3], [8, 9, 4], [7, 6, 5]]), "The high centre and the cells along the spiral reach both oceans."),
            (lines([[4]]), "A single cell touches all four edges."),
            (lines([[2, 2], [2, 2]]), "Flat land: water flows anywhere."),
        ],
        "hidden": [
            lines([[1, 1, 1]]),
            lines([[3], [2], [1]]),
            lines([[1, 2, 1], [2, 0, 2], [1, 2, 1]]),
            lines([[rng.randint(0, 10) for _ in range(200)] for _ in range(200)]),
            lines([[r + c for c in range(150)] for r in range(150)]),
            lines([[rng.randint(0, 10**5) for _ in range(120)] for _ in range(80)]),
        ],
    },
    {
        "topic": "graph",
        "title": "Longest Consecutive Sequence",
        "slug": "longest-consecutive-sequence",
        "difficulty": "Medium",
        "order": 5,
        "entry": {"method": "longestConsecutive", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "Given an **unsorted** list of integers, return the length of the longest run of consecutive values (like 4, 5, 6, 7) that all appear in the list, in any positions.\n\nSolve it in O(n) time.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 0 <= nums.length <= 10^5\n- -10^9 <= nums[i] <= 10^9",
        "examples": [
            (lines([10, 4, 20, 1, 3, 2]), "1, 2, 3, 4 are all present."),
            (lines([]), None),
            (lines([5, 5, 6]), "Duplicates count once: 5, 6."),
        ],
        "hidden": [
            lines([0]),
            lines([-1, 1, 0]),
            lines([10**9, -10**9]),
            lines(rng.sample(range(-15_000, 15_000), 30_000)),  # one long run
            lines(rng.sample(range(-10**9, 10**9, 2), 30_000)),  # all gaps
            lines([rng.randint(-50_000, 50_000) for _ in range(30_000)]),
        ],
    },
    {
        "topic": "graph",
        "title": "Alien Dictionary",
        "slug": "alien-dictionary",
        "difficulty": "Hard",
        "order": 6,
        "entry": {"method": "alienOrder", "params": [{"name": "words", "type": "List[str]"}], "returns": "str"},
        "description": "An alien language uses lowercase English letters in an unknown order. You are given its dictionary: a list of words **sorted by the alien alphabet**.\n\nWork out an order of all the letters that appear in the words that is consistent with the dictionary. If several orders work, return the one that comes **first in ordinary alphabetical order** (so every language gives the same answer). If no order works (the list can't be sorted under any alphabet), return `\"\"`.\n\nWords are compared letter by letter; if one word is a prefix of another, the shorter word comes first.\n\n**Input format:** one line, `words` as a JSON array of strings.\n\n**Output format:** a JSON string.",
        "constraints": "- 1 <= words.length <= 100\n- 1 <= words[i].length <= 100\n- Lowercase English letters only",
        "examples": [
            (lines(["tx", "tz", "zx", "zt"]), "tx before tz gives x < z; tz before zx gives t < z; zx before zt gives x < t. So x, t, z."),
            (lines(["ab", "a"]), "\"a\" is a prefix of \"ab\", so it must come first: no valid order."),
            (lines(["c", "b", "c"]), "c < b and b < c can't both hold."),
        ],
        "hidden": [
            lines(["z"]),
            lines(["zz", "zz"]),
            lines(["abc", "abd", "b"]),  # c, d, a, b only partly ordered: the tie-break decides
            lines(["q", "qa", "qb"]),
            lines(alien_words("qwertyuiopasdfghjklzxcvbnm", 100, 12)),
            lines(alien_words("zyxwv", 100, 100)),
            lines(alien_words("mlkjihgfedcba", 60, 4) + ["a"]),  # breaks the order: a can't come last
        ],
    },
    {
        "topic": "graph",
        "title": "Graph Valid Tree",
        "slug": "graph-valid-tree",
        "difficulty": "Medium",
        "order": 7,
        "entry": {
            "method": "validTree",
            "params": [{"name": "n", "type": "int"}, {"name": "edges", "type": "List[List[int]]"}],
            "returns": "bool",
        },
        "description": "There are `n` nodes labelled `0` to `n − 1`, and `edges` lists undirected edges between them. Decide whether these edges make a **tree**: every node connected, with no cycles.\n\n**Input format:** line 1 is `n`; line 2 is `edges` as a JSON array of pairs.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= n <= 2000\n- 0 <= edges.length <= 5000\n- No repeated edges or self-loops",
        "examples": [
            (lines(5, [[0, 1], [0, 2], [0, 3], [1, 4]]), "Connected, and 4 edges for 5 nodes: a tree."),
            (lines(4, [[0, 1], [1, 2], [2, 0]]), "Nodes 0, 1, 2 form a cycle, and node 3 is cut off."),
            (lines(1, []), "A single node is a tree."),
        ],
        "hidden": [
            lines(2, []),
            lines(2, [[1, 0]]),
            lines(4, [[0, 1], [2, 3]]),  # right edge count would be 3; two separate pieces
            lines(4, [[0, 1], [1, 2], [2, 0], [0, 3]]),
            lines(2000, random_tree_edges(2000)),
            lines(2000, random_tree_edges(2000)[:-1] + [[0, 1999], [1, 1998]]),
        ],
    },
    {
        "topic": "graph",
        "title": "Number of Connected Components in an Undirected Graph",
        "slug": "number-of-connected-components-in-an-undirected-graph",
        "difficulty": "Medium",
        "order": 8,
        "entry": {
            "method": "countComponents",
            "params": [{"name": "n", "type": "int"}, {"name": "edges", "type": "List[List[int]]"}],
            "returns": "int",
        },
        "description": "There are `n` nodes labelled `0` to `n − 1`, and `edges` lists undirected edges between them. Return the number of **connected components**: groups of nodes that can reach each other.\n\n**Input format:** line 1 is `n`; line 2 is `edges` as a JSON array of pairs.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= n <= 2000\n- 0 <= edges.length <= 5000\n- No repeated edges or self-loops",
        "examples": [
            (lines(5, [[0, 1], [1, 2], [3, 4]]), "{0, 1, 2} and {3, 4}."),
            (lines(3, []), "No edges: every node is its own component."),
            (lines(4, [[0, 1], [1, 2], [2, 3], [3, 0]]), "A cycle is still one component."),
        ],
        "hidden": [
            lines(1, []),
            lines(2, [[0, 1]]),
            lines(6, [[0, 1], [2, 3], [4, 5], [1, 2]]),
            lines(2000, []),
            lines(2000, random_tree_edges(2000)),
            lines(2000, [[rng.randrange(2000), rng.randrange(2000)] for _ in range(1500)]),
        ],
    },
]

if __name__ == "__main__":
    # Self-loops would break the "no self-loops" constraint, so drop any the generator produced.
    for problem in PROBLEMS:
        if problem["slug"] == "number-of-connected-components-in-an-undirected-graph":
            last = problem["hidden"][-1].split("\n")
            import json

            edges = {tuple(sorted(edge)) for edge in json.loads(last[1]) if edge[0] != edge[1]}
            problem["hidden"][-1] = lines(2000, [list(edge) for edge in sorted(edges)])
    add(PROBLEMS)
