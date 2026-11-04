"""Array problems beyond the flagship pair. Run: python -m scripts.batch_array"""
import random

from scripts.problem_tool import add, lines

rng = random.Random(1001)


def rotated(values, shift):
    return values[shift:] + values[:shift]


def distinct_sorted(count, low=-10**4, high=10**4):
    return sorted(rng.sample(range(low, high), count))


PROBLEMS = [
    {
        "topic": "array",
        "title": "Best Time to Buy and Sell Stock",
        "slug": "best-time-to-buy-and-sell-stock",
        "difficulty": "Easy",
        "order": 2,
        "entry": {"method": "maxProfit", "params": [{"name": "prices", "type": "List[int]"}], "returns": "int"},
        "description": "`prices[i]` is a stock's price on day `i`. You may buy one share on one day and sell it on a **later** day. Return the largest profit you can make, or `0` if no trade makes money.\n\n**Input format:** one line, `prices` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= prices.length <= 10^5\n- 0 <= prices[i] <= 10^4",
        "examples": [
            (lines([8, 3, 6, 1, 7, 5]), "Buy at 1 (day 3), sell at 7 (day 4): profit 6."),
            (lines([9, 7, 4, 2]), "Prices only fall, so the best choice is not to trade."),
            (lines([2, 2, 2]), "No price rises above the buying price."),
        ],
        "hidden": [
            lines([5]),
            lines([1, 10_000]),
            lines([3, 9, 1, 4]),  # the overall minimum comes after the best pair
            lines([0, 0, 0, 1]),
            lines(list(range(10_000, 0, -1))),
            lines([rng.randint(0, 10_000) for _ in range(30_000)]),
        ],
    },
    {
        "topic": "array",
        "title": "Contains Duplicate",
        "slug": "contains-duplicate",
        "difficulty": "Easy",
        "order": 3,
        "entry": {"method": "containsDuplicate", "params": [{"name": "nums", "type": "List[int]"}], "returns": "bool"},
        "description": "Given a list of integers `nums`, return `true` if any value appears more than once, and `false` if every value is distinct.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= nums.length <= 10^5\n- -10^9 <= nums[i] <= 10^9",
        "examples": [
            (lines([4, 1, 7, 1]), "1 appears twice."),
            (lines([5, 2, 8]), "All three values are different."),
            (lines([-3, -3]), None),
        ],
        "hidden": [
            lines([0]),
            lines([10**9, -10**9]),
            lines(rng.sample(range(-10**9, 10**9), 30_000)),
            lines(rng.sample(range(10**6), 29_999) + [7]),
            lines(list(range(30_000)) + [29_999]),  # the repeat is the very last element
        ],
    },
    {
        "topic": "array",
        "title": "Product of Array Except Self",
        "slug": "product-of-array-except-self",
        "difficulty": "Medium",
        "order": 4,
        "entry": {"method": "productExceptSelf", "params": [{"name": "nums", "type": "List[int]"}], "returns": "List[int]"},
        "description": "Given a list of integers `nums`, build a list where position `i` holds the product of every element **except** `nums[i]`.\n\nSolve it in O(n) time **without using division**. Every answer fits in a 32-bit signed integer.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a JSON array of integers.",
        "constraints": "- 2 <= nums.length <= 10^5\n- -30 <= nums[i] <= 30\n- Every product of a prefix or suffix fits in a 32-bit signed integer",
        "examples": [
            (lines([2, 3, 4, 5]), "For index 0: 3 × 4 × 5 = 60."),
            (lines([3, 0, 2]), "Only the zero's own position avoids multiplying by zero."),
            (lines([-1, 2, -3]), None),
        ],
        "hidden": [
            lines([7, 9]),
            lines([0, 0, 5]),  # two zeros: every product is zero
            lines([0, 4, 0, 1]),
            lines([1, -1, 1, -1, 1]),
            lines([1] * 29_990 + [2] * 10),
            lines([rng.choice([1, -1]) for _ in range(30_000)]),
            lines([1] * 15_000 + [0] + [-1] * 14_999),
        ],
    },
    {
        "topic": "array",
        "title": "Maximum Product Subarray",
        "slug": "maximum-product-subarray",
        "difficulty": "Medium",
        "order": 6,
        "entry": {"method": "maxProduct", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "Given a list of integers `nums`, choose a non-empty run of consecutive elements whose product is as large as possible, and return that product. The answer fits in a 32-bit signed integer.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 2 * 10^4\n- -10 <= nums[i] <= 10\n- The product of any run fits in a 32-bit signed integer",
        "examples": [
            (lines([2, -4, -3, 1]), "The run [2, -4, -3] multiplies to 24: two negatives cancel."),
            (lines([-2, 0, -1]), "Any run crossing the zero is 0, and the single elements are negative."),
            (lines([3, -1, 4]), "A single negative splits the array: 4 is best."),
        ],
        "hidden": [
            lines([-5]),
            lines([0, 0]),
            lines([-2, -3, -4]),  # odd number of negatives
            lines([-1, -1, -1, -1]),
            lines([2, 0, 3, -2, 4]),
            lines([rng.choice([1, -1, 1, 1]) for _ in range(20_000)]),
            lines([1] * 9_990 + [2] * 10 + [0] + [-2] * 9 + [1] * 9_990),
        ],
    },
    {
        "topic": "array",
        "title": "Find Minimum in Rotated Sorted Array",
        "slug": "find-minimum-in-rotated-sorted-array",
        "difficulty": "Medium",
        "order": 7,
        "entry": {"method": "findMin", "params": [{"name": "nums", "type": "List[int]"}], "returns": "int"},
        "description": "A list of **distinct** integers was sorted in increasing order, then rotated: some number of elements were moved from the front to the back, keeping their order. For example, `[1, 3, 5, 8]` might become `[5, 8, 1, 3]`.\n\nReturn the smallest element in O(log n) time.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 5000\n- -5000 <= nums[i] <= 5000\n- All values are distinct\n- `nums` is a sorted list rotated between 0 and n − 1 times",
        "examples": [
            (lines([6, 9, 12, 2, 4]), "The list was rotated after 12; the minimum is 2."),
            (lines([1, 5, 7]), "Not rotated at all: the first element is the minimum."),
            (lines([3, 1]), None),
        ],
        "hidden": [
            lines([42]),
            lines([2, 3, 4, 5, 1]),  # minimum at the very end
            lines([5, 1, 2, 3, 4]),
            lines(rotated(distinct_sorted(5000, -5000, 5000), 1)),
            lines(rotated(distinct_sorted(5000, -5000, 5000), 4999)),
            lines(rotated(distinct_sorted(4999, -5000, 5000), 2500)),
        ],
    },
    {
        "topic": "array",
        "title": "Search in Rotated Sorted Array",
        "slug": "search-in-rotated-sorted-array",
        "difficulty": "Medium",
        "order": 8,
        "entry": {
            "method": "search",
            "params": [{"name": "nums", "type": "List[int]"}, {"name": "target", "type": "int"}],
            "returns": "int",
        },
        "description": "A list of **distinct** integers was sorted in increasing order and then rotated at an unknown point, for example `[1, 3, 5, 8]` becoming `[5, 8, 1, 3]`.\n\nReturn the index of `target`, or `-1` if it isn't present, in O(log n) time.\n\n**Input format:** line 1 is `nums` as a JSON array; line 2 is `target`.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= nums.length <= 5000\n- -10^4 <= nums[i], target <= 10^4\n- All values are distinct\n- `nums` is a sorted list, possibly rotated",
        "examples": [
            (lines([9, 13, 20, 1, 4, 6], 4), "4 sits at index 4, in the part after the rotation point."),
            (lines([9, 13, 20, 1, 4, 6], 10), "10 isn't in the list."),
            (lines([7], 7), None),
        ],
        "hidden": [
            lines([7], 3),
            lines([3, 1], 1),
            lines([1, 3], 3),
            lines([5, 6, 7, 1, 2, 3, 4], 7),  # last element of the left half
            lines([5, 6, 7, 1, 2, 3, 4], 1),  # the rotation point itself
            lines(rotated(distinct_sorted(5000), 1234), rotated(distinct_sorted(5000), 1234)[4321]),
            lines(rotated(distinct_sorted(5000), 4000), 10_001),
        ],
    },
    {
        "topic": "array",
        "title": "3Sum",
        "slug": "3sum",
        "difficulty": "Medium",
        "order": 9,
        "entry": {
            "method": "threeSum",
            "params": [{"name": "nums", "type": "List[int]"}],
            "returns": "List[List[int]]",
            "normalize": "sorted_lists",
        },
        "description": "Given a list of integers `nums`, find every **distinct** triplet of values taken from three different positions that adds up to zero. Two triplets are the same if they contain the same three values.\n\nReturn the triplets in any order; within a triplet the order doesn't matter either.\n\n**Input format:** one line, `nums` as a JSON array.\n\n**Output format:** a JSON array of triplets. (The judge sorts your answer before comparing, so any order is accepted.)",
        "constraints": "- 3 <= nums.length <= 3000\n- -10^5 <= nums[i] <= 10^5",
        "examples": [
            (lines([-2, 0, 1, 1, 2, -1]), "Three different triplets add to zero; [-1, 0, 1] counts once even though it can be formed in two ways."),
            (lines([1, 2, -5]), "No three values add to zero."),
            (lines([0, 0, 0, 0]), "Only one distinct triplet, however many zeros there are."),
        ],
        "hidden": [
            lines([0, 0, 0]),
            lines([-1, 0, 1]),
            lines([-4, 2, 2, 2]),
            lines([3, -3, 0, 3, -3, 0, 0]),
            lines([-100_000, 50_000, 50_000, 1]),
            lines([0] * 3000),
            lines([rng.randint(-30_000, 30_000) for _ in range(1500)]),
            lines([rng.randint(-50, 50) for _ in range(1500)]),
        ],
    },
    {
        "topic": "array",
        "title": "Container With Most Water",
        "slug": "container-with-most-water",
        "difficulty": "Medium",
        "order": 10,
        "entry": {"method": "maxArea", "params": [{"name": "height", "type": "List[int]"}], "returns": "int"},
        "description": "`height[i]` is the height of a vertical wall standing at position `i`. Any two walls, with the ground between them, form a container. The water it holds is the distance between the walls times the **shorter** wall's height.\n\nReturn the most water any container can hold.\n\n**Input format:** one line, `height` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 2 <= height.length <= 10^5\n- 0 <= height[i] <= 10^4",
        "examples": [
            (lines([2, 7, 3, 6, 4, 8]), "Walls at positions 1 and 5: width 4 × height min(7, 8) = 28."),
            (lines([5, 5]), "Width 1 × height 5."),
            (lines([0, 9, 0]), "Any container uses a wall of height 0 or has width 1 with a 0 wall."),
        ],
        "hidden": [
            lines([1, 1]),
            lines([0, 0, 0]),
            lines([10_000, 1, 1, 1, 10_000]),
            lines([1, 2, 3, 4, 5, 6]),
            lines(list(range(1, 30_001))),
            lines([rng.randint(0, 10_000) for _ in range(30_000)]),
        ],
    },
]

if __name__ == "__main__":
    add(PROBLEMS)
