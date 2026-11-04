"""Dynamic programming problems beyond the flagship pair. Run: python -m scripts.batch_dp"""
import random
import string

from scripts.problem_tool import add, lines
from tests.reference_solutions import combination_sum_iv, decode_ways

rng = random.Random(3003)
INT32_MAX = 2**31 - 1


def word(length, alphabet="abc"):
    return "".join(rng.choice(alphabet) for _ in range(length))


def decodable(length):
    """A digit string whose decoding count still fits in 32 bits."""
    while True:
        s = "".join(rng.choice("1122233456789") for _ in range(length))
        s = s.replace("00", "10")
        if s[0] != "0" and 0 < decode_ways(s) <= INT32_MAX:
            return s


def combination_case(count, target):
    """Distinct values whose ordered-combination count fits in 32 bits."""
    while True:
        nums = sorted(rng.sample(range(5, 200), count))
        if 0 < combination_sum_iv(nums, target) <= INT32_MAX:
            return lines(nums, target)


PROBLEMS = [
    {
        "topic": "dynamic-programming",
        "title": "Longest Increasing Subsequence",
        "slug": "longest-increasing-subsequence",
        "difficulty": "Medium",
        "order": 3,
        "entry": {"method": "lengthOfLIS", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "A subsequence keeps some elements of `nums` in their original order, possibly skipping others. Return the length of the longest subsequence whose values are **strictly increasing**.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 2500\n- -10^4 <= nums[i] <= 10^4",
        "examples": [
            (lines([5, 2, 8, 6, 3, 6, 9, 7]), "One longest choice is 2, 3, 6, 9 (others have the same length)."),
            (lines([4, 4, 4]), "Strictly increasing, so equal values can't both be used."),
            (lines([1, 2, 3]), None),
        ],
        "hidden": [
            lines([7]),
            lines([9, 8, 7, 6]),
            lines([1, 3, 2, 4, 3, 5]),
            lines([0, -1, -2, 10, 1, 2, 3]),
            lines(list(range(2500))),
            lines([rng.randint(-10_000, 10_000) for _ in range(2500)]),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "Longest Common Subsequence",
        "slug": "longest-common-subsequence",
        "difficulty": "Medium",
        "order": 4,
        "entry": {
            "method": "longestCommonSubsequence",
            "params": [{"name": "text1", "type": "str"}, {"name": "text2", "type": "str"}],
            "returns": "int",
        },
        "description": "Return the length of the longest sequence of characters that appears, in order but not necessarily contiguously, in **both** `text1` and `text2`. Return `0` if they share nothing.\n\n**Input format:** line 1 is `text1` as a JSON string; line 2 is `text2`.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= text1.length, text2.length <= 1000\n- Both contain only lowercase English letters",
        "examples": [
            (lines("pancake", "planet"), "\"pane\" appears in order in both."),
            (lines("abc", "xyz"), "No common characters."),
            (lines("loop", "pool"), "\"oo\" and \"lo\" share the best length, 2."),
        ],
        "hidden": [
            lines("a", "a"),
            lines("a", "b"),
            lines("abcde", "ace"),
            lines("aaaa", "aa"),
            lines(word(1000), word(1000)),
            lines(word(1000, string.ascii_lowercase), word(1000, string.ascii_lowercase)),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "Word Break",
        "slug": "word-break",
        "difficulty": "Medium",
        "order": 5,
        "entry": {
            "method": "wordBreak",
            "params": [{"name": "s", "type": "str"}, {"name": "wordDict", "type": "List[str]"}],
            "returns": "bool",
        },
        "description": "Decide whether `s` can be split into a sequence of one or more words from `wordDict`. Words may be reused any number of times.\n\n**Input format:** line 1 is `s` as a JSON string; line 2 is `wordDict` as a JSON array of strings.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= s.length <= 300\n- 1 <= wordDict.length <= 1000\n- 1 <= wordDict[i].length <= 20\n- Lowercase English letters only; dictionary words are distinct",
        "examples": [
            (lines("sunflowerpot", ["sun", "flower", "pot", "sunflower"]), "\"sun flower pot\" works (so does \"sunflower pot\")."),
            (lines("catdog", ["ca", "dog", "cats"]), "No word covers the \"t\" before \"dog\"."),
            (lines("abab", ["ab"]), "Words can repeat."),
        ],
        "hidden": [
            lines("a", ["a"]),
            lines("a", ["b"]),
            lines("aaaaaaab", ["a", "aa", "aaa"]),
            lines("goalspecial", ["go", "goal", "goals", "special"]),
            lines("a" * 299 + "b", ["a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa"]),  # exponential for plain recursion
            lines("ab" * 150, ["a", "b", "ab", "ba"]),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "Combination Sum IV",
        "slug": "combination-sum-iv",
        "difficulty": "Medium",
        "order": 6,
        "entry": {
            "method": "combinationSum4",
            "params": [{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}],
            "returns": "int",
        },
        "description": "Given distinct positive integers `nums` and a `target`, count the **ordered** sequences of numbers from `nums` (each usable any number of times) that add up to `target`. Different orders count separately: `1 + 2` and `2 + 1` are two sequences. The answer fits in a 32-bit signed integer.\n\n**Input format:** line 1 is `nums` as a JSON array; line 2 is `target`.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 200\n- 1 <= nums[i] <= 1000, all distinct\n- 1 <= target <= 1000\n- The answer fits in a 32-bit signed integer",
        "examples": [
            (lines([1, 2], 3), "1+1+1, 1+2 and 2+1."),
            (lines([5], 3), "No sequence reaches 3."),
            (lines([2, 3], 7), "2+2+3, 2+3+2 and 3+2+2."),
        ],
        "hidden": [
            lines([1], 1),
            lines([4, 7], 1),
            lines([1, 2, 3], 4),
            lines([3, 4, 7], 14),
            combination_case(6, 300),
            combination_case(20, 600),
            combination_case(3, 1000),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "House Robber",
        "slug": "house-robber",
        "difficulty": "Medium",
        "order": 7,
        "entry": {"method": "rob", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "Houses stand in a row, and `nums[i]` is the money in house `i`. You may take money from any houses, except that you can never take from **two adjacent houses**. Return the most money you can collect.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= 400",
        "examples": [
            (lines([3, 10, 4, 6, 2]), "Take 10 and 6: 16."),
            (lines([8]), None),
            (lines([5, 1, 1, 5]), "Take the first and last houses: 10."),
        ],
        "hidden": [
            lines([0, 0]),
            lines([2, 9]),
            lines([4, 1, 2, 7, 5, 3, 1]),
            lines([400] * 10_000),
            lines([rng.randint(0, 400) for _ in range(10_000)]),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "House Robber II",
        "slug": "house-robber-ii",
        "difficulty": "Medium",
        "order": 8,
        "entry": {"method": "rob", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "The same rule as **House Robber**: no two adjacent houses. But now the houses stand in a **circle**, so the first and last houses are also neighbours. Return the most money you can collect.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= 400",
        "examples": [
            (lines([5, 1, 1, 5]), "The first and last houses now touch, so at most one of the 5s: 6."),
            (lines([7]), "A single house has no neighbours."),
            (lines([2, 3, 2]), None),
        ],
        "hidden": [
            lines([1, 2]),
            lines([0, 0, 0]),
            lines([9, 1, 1, 9, 1]),
            lines([1, 3, 1, 3, 100]),
            lines([400] * 9_999),
            lines([rng.randint(0, 400) for _ in range(10_000)]),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "Decode Ways",
        "slug": "decode-ways",
        "difficulty": "Medium",
        "order": 9,
        "entry": {"method": "numDecodings", "params": [{"name": "s", "type": "str"}], "returns": "int"},
        "description": "Letters are encoded as numbers: `A` → `1`, `B` → `2`, …, `Z` → `26`. Given a string of digits `s`, count the ways to split it into pieces that are each a valid code (`1` to `26`, with no leading zero) and so decode it back into letters.\n\nThe answer fits in a 32-bit signed integer.\n\n**Input format:** one line, `s` as a JSON string.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= s.length <= 100\n- `s` contains only digits\n- The answer fits in a 32-bit signed integer",
        "examples": [
            (lines("123"), "1 2 3 (ABC), 12 3 (LC), 1 23 (AW)."),
            (lines("206"), "Only 20 6 works: \"06\" has a leading zero and \"2 06\" isn't allowed."),
            (lines("30"), "\"30\" is too big and \"0\" alone isn't a code."),
        ],
        "hidden": [
            lines("0"),
            lines("10"),
            lines("1001"),
            lines("27"),
            lines("1" * 45),
            lines(decodable(100)),
            lines(decodable(80)),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "Unique Paths",
        "slug": "unique-paths",
        "difficulty": "Medium",
        "order": 10,
        "entry": {
            "method": "uniquePaths",
            "params": [{"name": "m", "type": "int"}, {"name": "n", "type": "int"}],
            "returns": "int",
        },
        "description": "A robot starts in the top-left corner of an `m × n` grid and must reach the bottom-right corner, moving only **right** or **down**. Count the different paths it can take. The answer fits in a 32-bit signed integer.\n\n**Input format:** line 1 is `m` (rows); line 2 is `n` (columns).\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= m, n <= 100\n- The answer is at most 2 × 10^9",
        "examples": [
            (lines(3, 3), "Each path makes 2 right moves and 2 down moves in some order: 6 orders."),
            (lines(1, 5), "A single row has only one path."),
            (lines(3, 7), None),
        ],
        "hidden": [
            lines(1, 1),
            lines(2, 2),
            lines(100, 1),
            lines(10, 10),
            lines(17, 17),
            lines(23, 12),
        ],
    },
    {
        "topic": "dynamic-programming",
        "title": "Jump Game",
        "slug": "jump-game",
        "difficulty": "Medium",
        "order": 11,
        "entry": {"method": "canJump", "params": [{"name": "nums", "type": "List[int]"}], "returns": "bool"},
        "description": "You start at index `0`. From index `i` you may jump forward by any distance from `1` to `nums[i]`. Decide whether you can reach the **last index**.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= 10^5",
        "examples": [
            (lines([2, 0, 3, 1, 0]), "Jump 2 to index 2, then 2 more to the end."),
            (lines([1, 1, 0, 4]), "Every route gets stuck on the 0 at index 2."),
            (lines([0]), "You're already on the last index."),
        ],
        "hidden": [
            lines([0, 1]),
            lines([5, 0, 0, 0, 0, 0]),
            lines([3, 2, 1, 0, 4]),
            lines([1] * 10_000),
            lines([1] * 5_000 + [0] + [1] * 4_999),
            lines([rng.randint(0, 2) for _ in range(10_000)]),
        ],
    },
]

if __name__ == "__main__":
    add(PROBLEMS)
