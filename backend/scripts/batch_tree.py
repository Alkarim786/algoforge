"""Tree problems beyond the flagship pair. Run: python -m scripts.batch_tree"""
import random

from scripts.problem_tool import add, lines
from tests.reference_solutions import _Tree, _values

rng = random.Random(7007)

LEVEL_ORDER = (
    "Trees are written in level order as a JSON array, with `null` for a missing child; children of `null` "
    "entries are omitted."
)


def random_tree(count, low=-1000, high=1000, unique=False):
    """A random tree shape: each new node hangs off a random free child slot."""
    values = rng.sample(range(low, high + 1), count) if unique else [rng.randint(low, high) for _ in range(count)]
    root = _Tree(values[0])
    slots = [(root, "left"), (root, "right")]
    for value in values[1:]:
        parent, side = slots.pop(rng.randrange(len(slots)))
        child = _Tree(value)
        setattr(parent, side, child)
        slots += [(child, "left"), (child, "right")]
    return root


def bst(values):
    root = None
    for value in values:
        node, parent = root, None
        while node:
            parent, node = node, (node.left if value < node.val else node.right)
        child = _Tree(value)
        if parent is None:
            root = child
        elif value < parent.val:
            parent.left = child
        else:
            parent.right = child
    return root


def chain(count, side="right"):
    root = node = _Tree(1)
    for value in range(2, count + 1):
        setattr(node, side, _Tree(value))
        node = getattr(node, side)
    return root


def orders(root):
    pre, ino = [], []

    def walk(node):
        if node:
            pre.append(node.val)
            walk(node.left)
            ino.append(node.val)
            walk(node.right)

    walk(root)
    return pre, ino


def subtree_values(root):
    nodes, stack = [], [root]
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack += [child for child in (node.left, node.right) if child]
    return _values(rng.choice(nodes))


def random_board(size, alphabet="abcde"):
    return [[rng.choice(alphabet) for _ in range(size)] for _ in range(size)]


def board_paths(board, count, length):
    """Words traced along real paths of the board, so some searches succeed."""
    rows, cols = len(board), len(board[0])
    words = set()
    while len(words) < count:
        r, c = rng.randrange(rows), rng.randrange(cols)
        seen, word = {(r, c)}, board[r][c]
        for _ in range(length - 1):
            options = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if 0 <= r + dr < rows and 0 <= c + dc < cols and (r + dr, c + dc) not in seen]
            if not options:
                break
            r, c = rng.choice(options)
            seen.add((r, c))
            word += board[r][c]
        words.add(word)
    return sorted(words)


def trie_ops(count):
    words = ["".join(rng.choice("abc") for _ in range(rng.randint(1, 6))) for _ in range(count // 3)]
    ops = []
    for _ in range(count):
        word = rng.choice(words)
        kind = rng.choice(["insert", "search", "startsWith"])
        ops.append([kind, word if kind != "startsWith" else word[: rng.randint(1, len(word))]])
    return ops


def dictionary_ops(count):
    words = ["".join(rng.choice("abcd") for _ in range(rng.randint(1, 5))) for _ in range(count // 3)]
    ops = []
    for _ in range(count):
        word = rng.choice(words)
        if rng.random() < 0.4:
            ops.append(["addWord", word])
        else:
            pattern = "".join("." if rng.random() < 0.3 else char for char in word)
            ops.append(["search", pattern])
    return ops


big_bst = bst(rng.sample(range(-10**4, 10**4), 2000))
BIG_BST_VALUES = [value for value in _values(big_bst) if value is not None]
skewed_bst = bst(list(range(1, 3001)))

PROBLEMS = [
    {
        "topic": "tree",
        "title": "Same Tree",
        "slug": "same-tree",
        "difficulty": "Easy",
        "order": 2,
        "entry": {
            "method": "isSameTree",
            "params": [{"name": "p", "type": "Optional[TreeNode]"}, {"name": "q", "type": "Optional[TreeNode]"}],
            "returns": "bool",
        },
        "description": f"Decide whether two binary trees are identical: the same shape, with the same value in every position.\n\n**Input format:** lines 1 and 2 are the two trees. {LEVEL_ORDER}\n\n**Output format:** `true` or `false`.",
        "constraints": "- 0 <= nodes in each tree <= 100\n- -10^4 <= node value <= 10^4",
        "examples": [
            (lines([1, 2, 3], [1, 2, 3]), None),
            (lines([1, 2], [1, None, 2]), "The 2 is a left child in one tree and a right child in the other."),
            (lines([], []), "Two empty trees are the same."),
        ],
        "hidden": [
            lines([1], []),
            lines([1, 2, 1], [1, 1, 2]),
            lines([5, 4, 7, None, None, 6], [5, 4, 7, None, None, 6]),
            lines(_values(random_tree(100)), _values(random_tree(100))),
            (lambda t: lines(t, t))(_values(random_tree(100))),
            (lambda t: lines(t, t[:-1] + [t[-1] + 1]))(_values(random_tree(100))),  # differ only in the last value
        ],
    },
    {
        "topic": "tree",
        "title": "Invert Binary Tree",
        "slug": "invert-binary-tree",
        "difficulty": "Easy",
        "order": 3,
        "entry": {"method": "invertTree", "params": [{"name": "root", "type": "Optional[TreeNode]"}], "returns": "Optional[TreeNode]"},
        "description": f"Mirror a binary tree: swap the left and right children of **every** node, and return the root.\n\n**Input format:** one line, the tree. {LEVEL_ORDER}\n\n**Output format:** the mirrored tree in the same format.",
        "constraints": "- 0 <= number of nodes <= 100\n- -100 <= node value <= 100",
        "examples": [
            (lines([4, 2, 7, 1, 3, 6, 9]), "Every level reads right to left."),
            (lines([2, 1]), "The single left child becomes a right child."),
            (lines([]), None),
        ],
        "hidden": [
            lines([1]),
            lines([1, None, 2]),
            lines([1, 2, 3, 4, None, None, 5]),
            lines(_values(random_tree(100, -100, 100))),
            lines(_values(chain(100, "left"))),
        ],
    },
    {
        "topic": "tree",
        "title": "Binary Tree Maximum Path Sum",
        "slug": "binary-tree-maximum-path-sum",
        "difficulty": "Hard",
        "order": 4,
        "entry": {"method": "maxPathSum", "params": [{"name": "root", "type": "Optional[TreeNode]"}], "returns": "int"},
        "description": f"A **path** is a sequence of nodes where each pair of neighbours is connected by an edge, and no node appears twice. It doesn't have to pass through the root, and it may go up through a node and back down the other side. It contains at least one node.\n\nReturn the largest sum of values along any path.\n\n**Input format:** one line, the tree. {LEVEL_ORDER}\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= number of nodes <= 3 * 10^4\n- -1000 <= node value <= 1000",
        "examples": [
            (lines([1, 2, 3]), "2 → 1 → 3 sums to 6."),
            (lines([-10, 9, 20, None, None, 15, 7]), "15 → 20 → 7 avoids the negative root: 42."),
            (lines([-3]), "A path has at least one node, even a negative one."),
        ],
        "hidden": [
            lines([-2, -1]),
            lines([2, -1]),
            lines([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1]),
            lines([-1000] * 15),
            lines(_values(random_tree(30_000))),
            lines(_values(chain(5_000, "right"))),
        ],
    },
    {
        "topic": "tree",
        "title": "Binary Tree Level Order Traversal",
        "slug": "binary-tree-level-order-traversal",
        "difficulty": "Medium",
        "order": 5,
        "entry": {"method": "levelOrder", "params": [{"name": "root", "type": "Optional[TreeNode]"}], "returns": "List[List[int]]"},
        "description": f"Return the tree's values **level by level**: one list per depth, from the root down, each read left to right.\n\n**Input format:** one line, the tree. {LEVEL_ORDER}\n\n**Output format:** a JSON array of levels.",
        "constraints": "- 0 <= number of nodes <= 2000\n- -1000 <= node value <= 1000",
        "examples": [
            (lines([3, 9, 20, None, None, 15, 7]), None),
            (lines([1]), None),
            (lines([]), "No nodes, no levels."),
        ],
        "hidden": [
            lines([1, 2, None, 3, None, 4]),
            lines([1, None, 2, None, 3]),
            lines([0, 0, 0, 0, 0, 0, 0]),
            lines(_values(random_tree(2000))),
            lines(_values(chain(2000, "left"))),
        ],
    },
    {
        "topic": "tree",
        "title": "Serialize and Deserialize Binary Tree",
        "slug": "serialize-and-deserialize-binary-tree",
        "difficulty": "Hard",
        "order": 6,
        "entry": {
            "codec": "Codec",
            "encode": "serialize",
            "decode": "deserialize",
            "params": [{"name": "root", "type": "Optional[TreeNode]"}],
            "returns": "Optional[TreeNode]",
        },
        "description": f"Design a `Codec`:\n\n- `serialize(root)` turns a binary tree into a **string**, in any format you like;\n- `deserialize(data)` rebuilds the exact same tree from that string.\n\nThe judge calls `deserialize(serialize(root))` and compares the rebuilt tree with the original.\n\n**Input format:** one line, the tree. {LEVEL_ORDER}\n\n**Output format:** the rebuilt tree in the same format.",
        "constraints": "- 0 <= number of nodes <= 10^4\n- -1000 <= node value <= 1000",
        "examples": [
            (lines([1, 2, 3, None, None, 4, 5]), None),
            (lines([]), "The empty tree must round-trip too."),
            (lines([-7, None, -7]), "Negative and repeated values."),
        ],
        "hidden": [
            lines([0]),
            lines([1, 2]),
            lines([1, None, 2, 3]),
            lines(_values(random_tree(10_000))),
            lines(_values(chain(3_000, "left"))),
        ],
    },
    {
        "topic": "tree",
        "title": "Subtree of Another Tree",
        "slug": "subtree-of-another-tree",
        "difficulty": "Easy",
        "order": 7,
        "entry": {
            "method": "isSubtree",
            "params": [{"name": "root", "type": "Optional[TreeNode]"}, {"name": "subRoot", "type": "Optional[TreeNode]"}],
            "returns": "bool",
        },
        "description": f"Decide whether `subRoot` appears inside `root` as a **complete subtree**: some node of `root` together with *all* of its descendants, matching `subRoot` exactly in shape and values.\n\n**Input format:** line 1 is `root`; line 2 is `subRoot`. {LEVEL_ORDER}\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= nodes in root <= 2000\n- 1 <= nodes in subRoot <= 1000\n- -10^4 <= node value <= 10^4",
        "examples": [
            (lines([3, 4, 5, 1, 2], [4, 1, 2]), "The node 4 and everything below it matches."),
            (lines([3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]), "Node 4's subtree has an extra 0, so it doesn't match exactly."),
            (lines([1, 1], [1]), "The leaf 1 is a complete subtree."),
        ],
        "hidden": [
            lines([1], [2]),
            lines([1, 2, 3], [1, 2]),
            lines([2, 2, None, 2, None, 2], [2, 2]),
            (lambda tree: lines(_values(tree), subtree_values(tree)))(random_tree(2000, -5, 5)),
            lines(_values(random_tree(2000, 0, 1)), _values(random_tree(15, 0, 1))),
            lines(_values(chain(2000, "left")), _values(chain(1000, "left"))),
        ],
    },
    {
        "topic": "tree",
        "title": "Construct Binary Tree from Preorder and Inorder Traversal",
        "slug": "construct-binary-tree-from-preorder-and-inorder-traversal",
        "difficulty": "Medium",
        "order": 8,
        "entry": {
            "method": "buildTree",
            "params": [{"name": "preorder", "type": "List[int]"}, {"name": "inorder", "type": "List[int]"}],
            "returns": "Optional[TreeNode]",
        },
        "description": f"You are given a binary tree's **preorder** traversal (node, left, right) and its **inorder** traversal (left, node, right). All values are distinct. Rebuild the tree and return its root.\n\n**Input format:** line 1 is `preorder`; line 2 is `inorder`, both JSON arrays.\n\n**Output format:** the tree. {LEVEL_ORDER}",
        "constraints": "- 1 <= number of nodes <= 3000\n- -3000 <= node value <= 3000, all distinct\n- The two traversals come from the same tree",
        "examples": [
            (lines([3, 9, 20, 15, 7], [9, 3, 15, 20, 7]), "3 is the root; 9 is to its left in the inorder list, and 15, 20, 7 to its right."),
            (lines([5], [5]), None),
            (lines([1, 2], [1, 2]), "2 comes after 1 in the inorder list, so it's a right child."),
        ],
        "hidden": [
            lines([1, 2], [2, 1]),
            lines([1, 2, 3], [3, 2, 1]),
            lines(*orders(random_tree(3000, -3000, 3000, unique=True))),
            lines(*orders(chain(3000, "right"))),
            lines(*orders(random_tree(500, -3000, 3000, unique=True))),
        ],
    },
    {
        "topic": "tree",
        "title": "Kth Smallest Element in a BST",
        "slug": "kth-smallest-element-in-a-bst",
        "difficulty": "Medium",
        "order": 10,
        "entry": {
            "method": "kthSmallest",
            "params": [{"name": "root", "type": "Optional[TreeNode]"}, {"name": "k", "type": "int"}],
            "returns": "int",
        },
        "description": f"Given the root of a binary search tree and an integer `k`, return the `k`-th smallest value in the tree (counting from 1).\n\n**Input format:** line 1 is the tree; line 2 is `k`. {LEVEL_ORDER}\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= k <= number of nodes <= 10^4\n- 0 <= node value <= 10^4, all distinct",
        "examples": [
            (lines([5, 3, 6, 2, 4, None, None, 1], 3), "In sorted order: 1, 2, 3, 4, 5, 6. The third is 3."),
            (lines([5, 3, 6, 2, 4, None, None, 1], 1), None),
            (lines([7], 1), None),
        ],
        "hidden": [
            lines([2, 1, 3], 3),
            lines([1, None, 2], 2),
            lines(_values(bst(rng.sample(range(10**4), 10**4))), 1),
            lines(_values(bst(rng.sample(range(10**4), 10**4))), 7_777),
            lines(_values(bst(list(range(3000, 0, -1)))), 2_999),
        ],
    },
    {
        "topic": "tree",
        "title": "Lowest Common Ancestor of a Binary Search Tree",
        "slug": "lowest-common-ancestor-of-a-binary-search-tree",
        "difficulty": "Medium",
        "order": 11,
        "entry": {
            "method": "lowestCommonAncestor",
            "params": [
                {"name": "root", "type": "TreeNode"},
                {"name": "p", "type": "TreeNodeRef"},
                {"name": "q", "type": "TreeNodeRef"},
            ],
            "returns": "TreeNodeRef",
        },
        "description": f"In a binary search tree, find the **lowest common ancestor** of nodes `p` and `q`: the deepest node that has both as descendants. A node counts as a descendant of itself.\n\nYour function receives the root and the two **nodes** `p` and `q`, and returns the ancestor node.\n\n**Input format:** line 1 is the tree; lines 2 and 3 are the values of `p` and `q` (all values are distinct). {LEVEL_ORDER}\n\n**Output format:** the ancestor's value.",
        "constraints": "- 2 <= number of nodes <= 10^4\n- -10^4 <= node value <= 10^4, all distinct\n- `p` and `q` are different nodes in the tree",
        "examples": [
            (lines([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8), "2 is on the left of 6 and 8 on the right, so they split at 6."),
            (lines([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4), "4 is below 2, and a node is its own descendant."),
            (lines([2, 1], 2, 1), None),
        ],
        "hidden": [
            lines([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 3, 5),
            lines([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 0, 9),
            lines(_values(big_bst), big_bst.val, max(BIG_BST_VALUES)),  # the root is one of the two nodes
            lines(_values(big_bst), *rng.sample(BIG_BST_VALUES, 2)),
            lines(_values(skewed_bst), 2_999, 3_000),
            lines(_values(skewed_bst), 1, 3_000),
        ],
    },
    {
        "topic": "tree",
        "title": "Implement Trie (Prefix Tree)",
        "slug": "implement-trie-prefix-tree",
        "difficulty": "Medium",
        "order": 12,
        "entry": {
            "class": "Trie",
            "operations": {
                "insert": {"method": "insert", "params": [{"name": "word", "type": "str"}], "returns": "None"},
                "search": {"method": "search", "params": [{"name": "word", "type": "str"}], "returns": "bool"},
                "startsWith": {"method": "startsWith", "params": [{"name": "prefix", "type": "str"}], "returns": "bool"},
            },
        },
        "description": "Implement a `Trie` (prefix tree) for lowercase words with three operations:\n\n- `insert(word)` adds a word;\n- `search(word)` returns whether that exact word was inserted;\n- `startsWith(prefix)` returns whether any inserted word begins with `prefix`.\n\n**Input format:** one line, a JSON array of operations in order, each `[name, argument]`, such as `[\"insert\", \"apple\"]`.\n\n**Output format:** a JSON array with the result of every `search` and `startsWith` call, in order.",
        "constraints": "- 1 <= word.length, prefix.length <= 2000\n- Lowercase English letters only\n- At most 3 * 10^4 operations",
        "examples": [
            (lines([["insert", "apple"], ["search", "apple"], ["search", "app"], ["startsWith", "app"], ["insert", "app"], ["search", "app"]]), "\"app\" is only a prefix until it's inserted as a word."),
            (lines([["search", "a"]]), "Nothing has been inserted yet."),
            (lines([["insert", "ab"], ["startsWith", "ab"], ["startsWith", "abc"]]), "A word is a prefix of itself."),
        ],
        "hidden": [
            lines([["insert", "a"], ["search", "a"], ["startsWith", "a"], ["search", "b"]]),
            lines([["insert", "abc"], ["insert", "abd"], ["search", "ab"], ["startsWith", "ab"]]),
            lines([["insert", "x" * 2000], ["startsWith", "x" * 1999], ["search", "x" * 1999]]),
            lines(trie_ops(3_000)),
            lines(trie_ops(30_000)),
        ],
    },
    {
        "topic": "tree",
        "title": "Design Add and Search Words Data Structure",
        "slug": "design-add-and-search-words-data-structure",
        "difficulty": "Medium",
        "order": 13,
        "entry": {
            "class": "WordDictionary",
            "operations": {
                "addWord": {"method": "addWord", "params": [{"name": "word", "type": "str"}], "returns": "None"},
                "search": {"method": "search", "params": [{"name": "word", "type": "str"}], "returns": "bool"},
            },
        },
        "description": "Design a `WordDictionary`:\n\n- `addWord(word)` adds a word;\n- `search(pattern)` returns whether any added word matches `pattern` exactly, where a `.` in the pattern matches **any one** letter.\n\n**Input format:** one line, a JSON array of operations in order, each `[name, argument]`.\n\n**Output format:** a JSON array with the result of every `search` call, in order.",
        "constraints": "- 1 <= word.length <= 25\n- Words are lowercase letters; patterns are lowercase letters and `.`\n- At most 10^4 operations; at most 2 dots per pattern",
        "examples": [
            (lines([["addWord", "bad"], ["addWord", "dad"], ["search", "pad"], ["search", "bad"], ["search", ".ad"], ["search", "b.."]]), None),
            (lines([["addWord", "a"], ["search", ".."]]), "A dot must match exactly one letter."),
            (lines([["search", "."]]), None),
        ],
        "hidden": [
            lines([["addWord", "ab"], ["search", "a."], ["search", ".b"], ["search", "."]]),
            lines([["addWord", "abc"], ["search", "abc."], ["search", "ab"]]),
            lines(dictionary_ops(2_000)),
            lines(dictionary_ops(10_000)),
            lines([["addWord", "a" * 25]] + [["search", "a" * 23 + ".."]] * 5_000),
        ],
    },
    {
        "topic": "tree",
        "title": "Word Search II",
        "slug": "word-search-ii",
        "difficulty": "Hard",
        "order": 14,
        "entry": {
            "method": "findWords",
            "params": [{"name": "board", "type": "List[List[str]]"}, {"name": "words", "type": "List[str]"}],
            "returns": "List[str]",
            "normalize": "sorted",
        },
        "description": "Given a grid of letters and a list of words, return every word that can be traced through the grid by moving between **horizontally or vertically adjacent** cells, using each cell at most once per word. Return the words in any order, each once.\n\n**Input format:** line 1 is `board` as a JSON array of rows of single-character strings; line 2 is `words` as a JSON array.\n\n**Output format:** a JSON array of strings. (The judge sorts your answer before comparing.)",
        "constraints": "- 1 <= rows, cols <= 12\n- 1 <= words.length <= 1000\n- 1 <= words[i].length <= 10\n- Lowercase English letters only; words are distinct",
        "examples": [
            (lines([["o", "a", "t"], ["e", "t", "h"], ["i", "h", "k"]], ["oath", "eat", "hike", "tea"]), "Only \"oath\" can be traced (o → a → t → h). The others need letters that aren't adjacent in the right order."),
            (lines([["a", "b"], ["c", "d"]], ["abcb"]), "The b would have to be used twice."),
            (lines([["a"]], ["a", "aa"]), None),
        ],
        "hidden": [
            lines([["a", "b"], ["c", "d"]], ["ab", "ac", "ad", "abdc", "acdb"]),
            lines([["a", "a"]], ["aaa"]),
            (lambda board: lines(board, board_paths(board, 400, 8) + ["zzz", "abcdeabcde"]))(random_board(12)),
            (lambda board: lines(board, board_paths(board, 1000, 10)))(random_board(12, "ab")),
            lines([["a"] * 12 for _ in range(12)], ["a" * n for n in range(1, 11)]),
        ],
    },
]

if __name__ == "__main__":
    add(PROBLEMS)
