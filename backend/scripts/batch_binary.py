"""Binary problems beyond the flagship pair. Run: python -m scripts.batch_binary"""
import random

from scripts.problem_tool import add, lines

rng = random.Random(2002)


def missing_from(n, missing):
    values = [value for value in range(n + 1) if value != missing]
    rng.shuffle(values)
    return values


PROBLEMS = [
    {
        "topic": "binary",
        "title": "Sum of Two Integers",
        "slug": "sum-of-two-integers",
        "difficulty": "Medium",
        "order": 1,
        "entry": {
            "method": "getSum",
            "params": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}],
            "returns": "int",
        },
        "description": "Return `a + b` **without using the `+` or `−` operators**. Build the sum from bitwise operations instead, treating the numbers as 32-bit two's complement integers.\n\nThe judge can't see which operators you used, so this one is on your honour. It's the point of the exercise.\n\n**Input format:** line 1 is `a`; line 2 is `b`.\n\n**Output format:** a single integer.",
        "constraints": "- -1000 <= a, b <= 1000",
        "examples": [
            (lines(2, 3), None),
            (lines(-4, 9), "Negative numbers work too, as long as you keep to 32 bits."),
            (lines(-6, -2), None),
        ],
        "hidden": [
            lines(0, 0),
            lines(-1000, 1000),
            lines(1000, 1000),
            lines(-1000, -1000),
            lines(-1, 1),
            lines(7, -12),
            lines(255, 1),  # a long carry chain
        ],
    },
    {
        "topic": "binary",
        "title": "Missing Number",
        "slug": "missing-number",
        "difficulty": "Easy",
        "order": 4,
        "entry": {"method": "missingNumber", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "`nums` holds `n` distinct numbers taken from the range `0` to `n`, so exactly one number in that range is missing. Return it.\n\nCan you do it in O(n) time and O(1) extra space?\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= n <= 10^4 (n = nums.length)\n- 0 <= nums[i] <= n\n- All values are distinct",
        "examples": [
            (lines([3, 0, 1]), "n = 3, so the range is 0 to 3, and 2 is missing."),
            (lines([0, 1]), "The missing number can be n itself."),
            (lines([1]), "The missing number can be 0."),
        ],
        "hidden": [
            lines([0]),
            lines([2, 0, 1, 4]),
            lines(missing_from(10_000, 0)),
            lines(missing_from(10_000, 10_000)),
            lines(missing_from(10_000, 4_321)),
            lines(missing_from(9_999, 5_000)),
        ],
    },
    {
        "topic": "binary",
        "title": "Reverse Bits",
        "slug": "reverse-bits",
        "difficulty": "Easy",
        "order": 5,
        "entry": {"method": "reverseBits", "params": [{"name": "n", "type": "int"}], "returns": "int"},
        "description": "Treat `n` as a 32-bit unsigned integer. Reverse the order of its 32 bits (bit 0 becomes bit 31, bit 1 becomes bit 30, and so on) and return the result as an unsigned integer.\n\n**Input format:** one line, the integer `n`.\n\n**Output format:** a single integer.",
        "constraints": "- 0 <= n <= 2^32 − 1",
        "examples": [
            (lines(1), "Bit 0 moves to bit 31: 1 becomes 2^31 = 2147483648."),
            (lines(6), "110 has its 1 bits at positions 1 and 2; they move to positions 30 and 29."),
            (lines(0), None),
        ],
        "hidden": [
            lines(4_294_967_295),
            lines(2_147_483_648),
            lines(0b1010_1010_1010_1010_1010_1010_1010_1010),
            lines(0xF000_000F),
            lines(rng.randrange(2**32)),
            lines(rng.randrange(2**32)),
        ],
    },
]

if __name__ == "__main__":
    add(PROBLEMS)
