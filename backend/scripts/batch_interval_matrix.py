"""Interval and Matrix problems beyond the flagship pairs. Run: python -m scripts.batch_interval_matrix"""
import random

from scripts.problem_tool import add, lines

rng = random.Random(4004)


def random_meetings(count, span=10**6, longest=5_000):
    meetings = []
    for _ in range(count):
        start = rng.randint(0, span)
        meetings.append([start, start + rng.randint(1, longest)])
    return meetings


def back_to_back(count):
    """Meetings that touch end-to-start: never a clash, never a second room."""
    starts = sorted(rng.sample(range(0, 10**6), count + 1))
    meetings = [[starts[i], starts[i + 1]] for i in range(count)]
    rng.shuffle(meetings)
    return meetings


def letters(rows, cols, alphabet="ABCDE"):
    return [[rng.choice(alphabet) for _ in range(cols)] for _ in range(rows)]


ROOMS_NOTE = "A meeting ending at time `t` does **not** clash with one starting at `t`."

PROBLEMS = [
    {
        "topic": "interval",
        "title": "Non-overlapping Intervals",
        "slug": "non-overlapping-intervals",
        "difficulty": "Medium",
        "order": 3,
        "entry": {
            "method": "eraseOverlapIntervals",
            "params": [{"name": "intervals", "type": "List[List[int]]"}],
            "returns": "int",
        },
        "description": "Given a list of intervals `[start, end]`, return the **fewest** intervals you must remove so that the rest don't overlap.\n\nIntervals that only touch, such as `[1, 2]` and `[2, 3]`, do **not** overlap here.\n\n**Input format:** one line, `intervals` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= intervals.length <= 10^5\n- -5 * 10^4 <= start < end <= 5 * 10^4",
        "examples": [
            (lines([[1, 3], [2, 4], [3, 5], [1, 2]]), "At most two can stay, for example [1, 2] and [3, 5], so two must go."),
            (lines([[1, 5], [1, 5], [1, 5]]), "Three identical intervals: keep one, remove two."),
            (lines([[1, 2], [2, 3]]), "Touching isn't overlapping, so nothing needs removing."),
        ],
        "hidden": [
            lines([[0, 1]]),
            lines([[1, 100], [2, 3], [4, 5], [6, 7]]),  # one long interval blocks three short ones
            lines([[-50_000, 50_000], [0, 1]]),
            lines([[1, 2], [1, 3], [1, 4], [1, 5]]),
            lines([[s, s + rng.randint(1, 50)] for s in (rng.randint(-50_000, 49_900) for _ in range(30_000))]),
            lines([[i, i + 1] for i in range(-15_000, 15_000)]),
        ],
    },
    {
        "topic": "interval",
        "title": "Meeting Rooms",
        "slug": "meeting-rooms",
        "difficulty": "Easy",
        "order": 4,
        "entry": {
            "method": "canAttendMeetings",
            "params": [{"name": "intervals", "type": "List[List[int]]"}],
            "returns": "bool",
        },
        "description": f"Each interval `[start, end]` is a meeting. Can one person attend **all** of them? That's true exactly when no two meetings overlap.\n\n{ROOMS_NOTE}\n\n**Input format:** one line, `intervals` as a JSON array (possibly empty).\n\n**Output format:** `true` or `false`.",
        "constraints": "- 0 <= intervals.length <= 10^4\n- 0 <= start < end <= 10^6",
        "examples": [
            (lines([[9, 10], [13, 15], [10, 12]]), "Sorted by start: 9-10, 10-12, 13-15. Each ends before the next begins."),
            (lines([[1, 5], [4, 8]]), "The second meeting starts before the first ends."),
            (lines([]), "No meetings, so nothing can clash."),
        ],
        "hidden": [
            lines([[3, 4]]),
            lines([[5, 10], [0, 5]]),
            lines([[0, 10], [2, 3]]),  # one meeting entirely inside another
            lines([[1, 2], [3, 4], [2, 3]]),
            lines(back_to_back(10_000)),
            lines(back_to_back(9_999) + [[500_000, 500_001]]),
        ],
    },
    {
        "topic": "interval",
        "title": "Meeting Rooms II",
        "slug": "meeting-rooms-ii",
        "difficulty": "Medium",
        "order": 5,
        "entry": {
            "method": "minMeetingRooms",
            "params": [{"name": "intervals", "type": "List[List[int]]"}],
            "returns": "int",
        },
        "description": f"Each interval `[start, end]` is a meeting that needs a room for its whole duration. Return the **minimum number of rooms** needed to hold every meeting.\n\n{ROOMS_NOTE} So a room freed at `t` can be reused by a meeting starting at `t`.\n\n**Input format:** one line, `intervals` as a JSON array.\n\n**Output format:** a single integer.",
        "constraints": "- 1 <= intervals.length <= 10^4\n- 0 <= start < end <= 10^6",
        "examples": [
            (lines([[0, 30], [5, 10], [15, 20]]), "The long meeting needs its own room; the two short ones can share another."),
            (lines([[7, 10], [2, 4]]), "They don't overlap, so one room is enough."),
            (lines([[1, 5], [5, 9], [2, 6]]), "At time 5 one room frees up exactly as another meeting starts: 2 rooms."),
        ],
        "hidden": [
            lines([[0, 1]]),
            lines([[1, 10], [1, 10], [1, 10]]),
            lines([[1, 3], [2, 4], [3, 5], [4, 6]]),
            lines(back_to_back(10_000)),
            lines([[0, 10**6]] * 50 + [[1, 2]]),
            lines(random_meetings(10_000)),
        ],
    },
    {
        "topic": "matrix",
        "title": "Spiral Matrix",
        "slug": "spiral-matrix",
        "difficulty": "Medium",
        "order": 2,
        "entry": {
            "method": "spiralOrder",
            "params": [{"name": "matrix", "type": "List[List[int]]"}],
            "returns": "List[int]",
        },
        "description": "Return every element of an `m × n` matrix in **clockwise spiral order**: across the top row, down the right column, back along the bottom row, up the left column, then the same again one layer further in.\n\n**Input format:** one line, the matrix as a JSON array of rows.\n\n**Output format:** a JSON array of integers.",
        "constraints": "- 1 <= m, n <= 10\n- -100 <= matrix[i][j] <= 100",
        "examples": [
            (lines([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), "Outer ring 1, 2, 3, 6, 9, 8, 7, 4, then the centre 5."),
            (lines([[1, 2, 3, 4], [5, 6, 7, 8]]), "Two rows: across the top, then back along the bottom."),
            (lines([[7], [8], [9]]), "A single column is read top to bottom."),
        ],
        "hidden": [
            lines([[5]]),
            lines([[1, 2, 3, 4, 5]]),
            lines([[1, 2], [3, 4]]),
            lines([[r * 4 + c for c in range(4)] for r in range(5)]),  # taller than wide
            lines([[r * 10 + c for c in range(10)] for r in range(3)]),  # wider than tall
            lines([[rng.randint(-100, 100) for _ in range(10)] for _ in range(10)]),
            lines([[rng.randint(-100, 100) for _ in range(9)] for _ in range(7)]),
        ],
    },
    {
        "topic": "matrix",
        "title": "Word Search",
        "slug": "word-search",
        "difficulty": "Medium",
        "order": 4,
        "entry": {
            "method": "exist",
            "params": [{"name": "board", "type": "List[List[str]]"}, {"name": "word", "type": "str"}],
            "returns": "bool",
        },
        "description": "A grid of letters `board` is given. Decide whether `word` can be traced through it by moving between **horizontally or vertically adjacent** cells, using each cell at most once.\n\n**Input format:** line 1 is `board` as a JSON array of rows of single-character strings; line 2 is `word` as a JSON string.\n\n**Output format:** `true` or `false`.",
        "constraints": "- 1 <= rows, cols <= 6\n- 1 <= word.length <= 15\n- `board` and `word` contain only English letters",
        "examples": [
            (lines([["C", "A", "T"], ["X", "R", "S"], ["Q", "T", "E"]], "CARTE"), "C → A → R → T → E, moving right, down, down, right."),
            (lines([["C", "A", "T"], ["X", "R", "S"], ["Q", "T", "E"]], "CATS"), "C → A → T → S works: S is directly below T."),
            (lines([["A", "B"], ["C", "D"]], "ABA"), "The A can't be used twice."),
        ],
        "hidden": [
            lines([["A"]], "A"),
            lines([["A"]], "B"),
            lines([["A", "B"], ["C", "D"]], "ABDC"),
            lines([["A", "B"], ["C", "D"]], "ACDB"),
            lines([["A"] * 6 for _ in range(6)], "A" * 14 + "B"),  # exhaustive search without pruning
            lines([["A"] * 6 for _ in range(6)], "A" * 15),
            lines(letters(6, 6), "ABCDEABCDE"),
            lines(letters(6, 6, "AB"), "ABABABABAB"),
        ],
    },
]

if __name__ == "__main__":
    add(PROBLEMS)
