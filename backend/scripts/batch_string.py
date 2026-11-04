"""String problems beyond the flagship pair. Run: python -m scripts.batch_string"""
import random
import string

from scripts.problem_tool import add, lines

rng = random.Random(6006)


def text(length, alphabet=string.ascii_lowercase):
    return "".join(rng.choice(alphabet) for _ in range(length))


def anagram_of(word):
    letters = list(word)
    rng.shuffle(letters)
    return "".join(letters)


def anagram_groups(count, length):
    bases = [text(length) for _ in range(count // 4)]
    words = [anagram_of(rng.choice(bases)) for _ in range(count)]
    return words


def palindrome_heavy(length):
    half = text(length // 2, "ab")
    return half + half[::-1] + text(length - 2 * (length // 2), "ab")


PROBLEMS = [
    {
        "topic": "string",
        "title": "Longest Repeating Character Replacement",
        "slug": "longest-repeating-character-replacement",
        "difficulty": "Medium",
        "order": 2,
        "entry": {
            "method": "characterReplacement",
            "params": [{"name": "s", "type": "str"}, {"name": "k", "type": "int"}],
            "returns": "int",
        },
        "description": "You may change **at most `k`** characters of `s` into any other uppercase letter. Return the length of the longest substring you can make in which every character is the same.\n\n**Input format:** line 1 is `s` as a JSON string; line 2 is `k`.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= s.length <= 10^5\n- `s` contains only uppercase English letters\n- 0 <= k <= s.length",
        "examples": [
            (lines("ABAB", 2), "Change both B's (or both A's): \"AAAA\"."),
            (lines("AABABBA", 1), "Change the middle A: \"AABBBBA\" contains \"BBBB\"."),
            (lines("XYZ", 0), "No changes allowed: runs of length 1."),
        ],
        "hidden": [
            lines("A", 0),
            lines("A", 1),
            lines("AAAA", 2),
            lines("ABCDE", 1),
            lines(text(30_000, "AB"), 100),
            lines(text(30_000, string.ascii_uppercase), 5_000),
            lines(text(30_000, "ABC"), 0),
        ],
    },
    {
        "topic": "string",
        "title": "Minimum Window Substring",
        "slug": "minimum-window-substring",
        "difficulty": "Hard",
        "order": 3,
        "entry": {
            "method": "minWindow",
            "params": [{"name": "s", "type": "str"}, {"name": "t", "type": "str"}],
            "returns": "str",
        },
        "description": "Return the shortest substring of `s` that contains **every character of `t`, including repeats** (if `t` has two `a`s, the window needs at least two). If no such window exists, return `\"\"`. If several shortest windows exist, return the one that **starts first**.\n\n**Input format:** line 1 is `s` as a JSON string; line 2 is `t`.\n\n**Output format:** a JSON string.",
        "constraints": "- 1 <= s.length, t.length <= 10^5\n- `s` and `t` contain English letters",
        "examples": [
            (lines("XADOBECODEBANC", "ABC"), "\"BANC\" is the shortest window holding an A, a B and a C."),
            (lines("a", "aa"), "Two a's are needed, but s has only one."),
            (lines("hello", "l"), "Ties go to the earliest window: the first \"l\"."),
        ],
        "hidden": [
            lines("a", "a"),
            lines("a", "b"),
            lines("ab", "b"),
            lines("aaflslflsldkalskaaa", "aaa"),
            lines("abcabdebac", "cda"),
            lines(text(30_000, "abcde"), "abcdeedcba"),
            lines(text(30_000) + "z", "zz"),
            lines(text(30_000, "ab") + "c", text(500, "ab") + "c"),
        ],
    },
    {
        "topic": "string",
        "title": "Valid Anagram",
        "slug": "valid-anagram",
        "difficulty": "Easy",
        "order": 4,
        "entry": {
            "method": "isAnagram",
            "params": [{"name": "s", "type": "str"}, {"name": "t", "type": "str"}],
            "returns": "bool",
        },
        "description": "Return `true` if `t` uses exactly the same letters as `s`, each the same number of times, just possibly in a different order.\n\n**Input format:** line 1 is `s` as a JSON string; line 2 is `t`.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= s.length, t.length <= 5 * 10^4\n- Lowercase English letters only",
        "examples": [
            (lines("listen", "silent"), None),
            (lines("rat", "car"), "r, a, t versus c, a, r."),
            (lines("aab", "abb"), "Same letters, but different counts."),
        ],
        "hidden": [
            lines("a", "a"),
            lines("a", "ab"),
            lines("ab", "ba"),
            lines("abc", "abcd"),
            lines(*(lambda w: (w, anagram_of(w)))(text(50_000))),
            lines(text(50_000), text(50_000)),
        ],
    },
    {
        "topic": "string",
        "title": "Group Anagrams",
        "slug": "group-anagrams",
        "difficulty": "Medium",
        "order": 5,
        "entry": {
            "method": "groupAnagrams",
            "params": [{"name": "strs", "type": "List[str]"}],
            "returns": "List[List[str]]",
            "normalize": "sorted_lists",
        },
        "description": "Group the strings that are **anagrams** of each other (the same letters with the same counts). Return the groups in any order, with the words inside each group in any order.\n\n**Input format:** one line, `strs` as a JSON array of strings.\n\n**Output format:** a JSON array of groups. (The judge sorts your answer before comparing.)",
        "constraints": "- 1 <= strs.length <= 10^4\n- 0 <= strs[i].length <= 100\n- Lowercase English letters only",
        "examples": [
            (lines(["eat", "tea", "tan", "ate", "nat", "bat"]), None),
            (lines([""]), "The empty string is a group on its own."),
            (lines(["ab", "ba", "abc"]), None),
        ],
        "hidden": [
            lines(["a"]),
            lines(["", ""]),
            lines(["abc", "bca", "cab", "abcd"]),
            lines(["aab", "aba", "abb"]),
            lines(anagram_groups(10_000, 6)),
            lines([text(rng.randint(0, 100)) for _ in range(3_000)]),
        ],
    },
    {
        "topic": "string",
        "title": "Valid Palindrome",
        "slug": "valid-palindrome",
        "difficulty": "Easy",
        "order": 7,
        "entry": {"method": "isPalindrome", "params": [{"name": "s", "type": "str"}], "returns": "bool"},
        "description": "Ignore every character that isn't a letter or a digit, and treat upper- and lowercase letters as the same. Does what's left read the same forwards and backwards?\n\n**Input format:** one line, `s` as a JSON string.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= s.length <= 2 * 10^5\n- `s` contains printable ASCII characters",
        "examples": [
            (lines("Never odd or even."), "Cleaned: \"neveroddoreven\"."),
            (lines("race a car"), "Cleaned: \"raceacar\", which isn't a palindrome."),
            (lines(" ?! "), "Nothing is left, and an empty string is a palindrome."),
        ],
        "hidden": [
            lines("a"),
            lines("0P"),  # a digit and a letter: not equal
            lines("Aa"),
            lines("1a2b2A1"),
            lines(("Ab3" + "," * 5) * 10_000 + ("3bA" * 10_000)[::-1][::-1]),
            lines("x" * 100_000 + "y" + "x" * 99_999),
        ],
    },
    {
        "topic": "string",
        "title": "Longest Palindromic Substring",
        "slug": "longest-palindromic-substring",
        "difficulty": "Medium",
        "order": 8,
        "entry": {"method": "longestPalindrome", "params": [{"name": "s", "type": "str"}], "returns": "str"},
        "description": "Return the longest substring of `s` that reads the same forwards and backwards. If several have the longest length, return the one that **starts first**.\n\n**Input format:** one line, `s` as a JSON string.\n\n**Output format:** a JSON string.",
        "constraints": "- 1 <= s.length <= 1000\n- `s` contains letters and digits",
        "examples": [
            (lines("xabay"), "\"aba\" is centred on the b."),
            (lines("cbbd"), "Even-length palindromes count: \"bb\"."),
            (lines("abc"), "Every single letter is a palindrome; the first one wins the tie."),
        ],
        "hidden": [
            lines("a"),
            lines("aa"),
            lines("abacdfgdcaba"),
            lines("racecarxyz"),
            lines("a" * 1000),
            lines(palindrome_heavy(1000)),
            lines(text(1000, "ab")),
        ],
    },
    {
        "topic": "string",
        "title": "Palindromic Substrings",
        "slug": "palindromic-substrings",
        "difficulty": "Medium",
        "order": 9,
        "entry": {"method": "countSubstrings", "params": [{"name": "s", "type": "str"}], "returns": "int"},
        "description": "Count the substrings of `s` that are palindromes. Substrings at different positions count separately, even if they contain the same letters.\n\n**Input format:** one line, `s` as a JSON string.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= s.length <= 1000\n- Lowercase English letters only",
        "examples": [
            (lines("abc"), "Just the three single letters."),
            (lines("aaa"), "Three a's, two \"aa\"s and one \"aaa\"."),
            (lines("abba"), "a, b, b, a, \"bb\" and \"abba\"."),
        ],
        "hidden": [
            lines("z"),
            lines("ab"),
            lines("racecar"),
            lines("a" * 1000),
            lines(text(1000, "ab")),
            lines(text(1000)),
        ],
    },
    {
        "topic": "string",
        "title": "Encode and Decode Strings",
        "slug": "encode-and-decode-strings",
        "difficulty": "Medium",
        "order": 10,
        "entry": {
            "codec": "Codec",
            "encode": "encode",
            "decode": "decode",
            "params": [{"name": "strs", "type": "List[str]"}],
            "returns": "List[str]",
        },
        "description": "Design a `Codec` with two methods:\n\n- `encode(strs)` turns a list of strings into **one** string;\n- `decode(data)` turns that string back into the **exact** original list.\n\nThe strings may contain any printable character, including any separator you might pick, and may be empty. The judge calls `decode(encode(strs))` and compares the result with `strs`.\n\n**Input format:** one line, `strs` as a JSON array of strings.\n\n**Output format:** the decoded list as a JSON array.",
        "constraints": "- 0 <= strs.length <= 200\n- 0 <= strs[i].length <= 200\n- Strings contain printable ASCII characters",
        "examples": [
            (lines(["hello", "world"]), None),
            (lines(["", "a,b", "#"]), "Empty strings and separator-like characters must survive."),
            (lines([]), "An empty list must decode back to an empty list."),
        ],
        "hidden": [
            lines([""]),
            lines(["", ""]),
            lines(["4#abc", "#", "##", "1"]),  # looks like length prefixes
            lines(["\\", "\\\\", "\\#"]),
            lines(["".join(chr(rng.randint(32, 126)) for _ in range(200)) for _ in range(200)]),
            lines([text(rng.randint(0, 5), "#,;|") for _ in range(200)]),
        ],
    },
]

if __name__ == "__main__":
    add(PROBLEMS)
