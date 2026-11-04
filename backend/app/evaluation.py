"""Turns a user's judged submissions into per-topic scores and strengths/weaknesses.

Topic score (0-100) = 70% coverage + 30% efficiency
- coverage: difficulty-weighted share of the topic's problems solved
- efficiency: problems solved per judged submission in the topic (1.0 = every solve was first try)
"""
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Protocol

ACCEPTED = "Accepted"
WRONG_ANSWER = "Wrong Answer"
TLE = "TLE"
RUNTIME_ERROR = "Runtime Error"
# Only these count toward a user's stats. Platform failures and unfinished runs must not.
JUDGED_VERDICTS = (ACCEPTED, WRONG_ANSWER, TLE, RUNTIME_ERROR)
PENDING = "pending"
RUNNING = "running"
SYSTEM_ERROR = "System Error"
FINISHED = "Finished"  # Ran without failing on a custom input, which has nothing to compare against
DIFFICULTY_WEIGHTS = {"Easy": 1, "Medium": 2, "Hard": 3}
STRENGTH_MIN_SCORE = 70
WEAKNESS_MAX_SCORE = 40


class ProblemInfo(Protocol):
    id: int
    difficulty: str
    topic_slug: str
    topic_name: str


def classify(score: int, attempted: int) -> str:
    if attempted == 0:
        return "not_attempted"
    if score >= STRENGTH_MIN_SCORE:
        return "strength"
    if score < WEAKNESS_MAX_SCORE:
        return "weakness"
    return "developing"


def evaluate(problems: Iterable[ProblemInfo], statuses: Mapping[int, Counter]) -> dict:
    """`statuses` maps problem id -> Counter of judged verdicts for one user. Topics keep `problems` order."""
    by_topic: dict[str, list[ProblemInfo]] = {}
    for problem in problems:
        by_topic.setdefault(problem.topic_slug, []).append(problem)
    all_problems = [problem for group in by_topic.values() for problem in group]

    def solved(problem: ProblemInfo) -> bool:
        return statuses.get(problem.id, Counter())[ACCEPTED] > 0

    topics = []
    for slug, group in by_topic.items():
        verdicts = sum((statuses.get(problem.id, Counter()) for problem in group), Counter())
        submissions = verdicts.total()
        solved_problems = [problem for problem in group if solved(problem)]
        total_weight = sum(DIFFICULTY_WEIGHTS[problem.difficulty] for problem in group)
        coverage = sum(DIFFICULTY_WEIGHTS[problem.difficulty] for problem in solved_problems) / total_weight
        efficiency = len(solved_problems) / submissions if submissions else 0
        score = round(100 * (0.7 * coverage + 0.3 * efficiency))
        attempted = sum(1 for problem in group if problem.id in statuses)
        failures = Counter({status: count for status, count in verdicts.items() if status != ACCEPTED})
        topics.append(
            {
                "slug": slug,
                "name": group[0].topic_name,
                "score": score,
                "classification": classify(score, attempted),
                "solved": len(solved_problems),
                "attempted": attempted,
                "total": len(group),
                "submissions": submissions,
                "top_failure": failures.most_common(1)[0][0] if failures else None,
            }
        )

    def names(classification: str) -> list[str]:
        matches = [topic for topic in topics if topic["classification"] == classification]
        # Best first for strengths, worst first for weaknesses.
        matches.sort(key=lambda topic: topic["score"], reverse=classification == "strength")
        return [topic["name"] for topic in matches]

    return {
        "topics": topics,
        "strengths": names("strength"),
        "weaknesses": names("weakness"),
        "not_attempted": names("not_attempted"),
        "difficulty": [
            {
                "difficulty": difficulty,
                "solved": sum(1 for p in all_problems if p.difficulty == difficulty and solved(p)),
                "total": sum(1 for p in all_problems if p.difficulty == difficulty),
            }
            for difficulty in DIFFICULTY_WEIGHTS
        ],
    }
