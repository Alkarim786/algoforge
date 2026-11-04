"""A user's progress: shared by the admin evaluation and the learner's own dashboard."""
from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.evaluation import ACCEPTED, JUDGED_VERDICTS, evaluate
from app.models import Problem, Submission, Topic, User

# Run-mode submissions and platform failures never count toward progress.
JUDGED_SUBMISSION = (Submission.kind == "submit") & Submission.status.in_(JUDGED_VERDICTS)
ACTIVITY_DAYS = 14


def problem_rows(db: Session) -> list:
    """Every problem in study order: topic order, then order within the topic."""
    return db.execute(
        select(
            Problem.id,
            Problem.slug,
            Problem.title,
            Problem.difficulty,
            Topic.slug.label("topic_slug"),
            Topic.name.label("topic_name"),
        )
        .join(Problem.topic)
        .order_by(Topic.order, Topic.id, Problem.order_within_topic, Problem.id)
    ).all()


def verdicts_by_problem(db: Session, user_id: int) -> dict[int, Counter]:
    statuses: dict[int, Counter] = defaultdict(Counter)
    rows = db.execute(
        select(Submission.problem_id, Submission.status, func.count())
        .where(Submission.user_id == user_id, JUDGED_SUBMISSION)
        .group_by(Submission.problem_id, Submission.status)
    )
    for problem_id, verdict, count in rows:
        statuses[problem_id][verdict] = count
    return statuses


def user_evaluation(db: Session, user: User) -> dict:
    problems = problem_rows(db)
    statuses = verdicts_by_problem(db, user.id)
    recent = db.execute(
        select(Submission.id, Problem.title, Problem.slug, Submission.language, Submission.status, Submission.created_at)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(Submission.user_id == user.id, Submission.kind == "submit")
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(10)
    )
    submissions = sum(counts.total() for counts in statuses.values())
    accepted = sum(counts[ACCEPTED] for counts in statuses.values())
    return {
        "user": user,
        "solved": sum(1 for counts in statuses.values() if counts[ACCEPTED]),
        "attempted": len(statuses),
        "total_problems": len(problems),
        "submissions": submissions,
        "acceptance_rate": round(accepted / submissions, 3) if submissions else None,
        "recent_submissions": [row._mapping for row in recent],
        **evaluate(problems, statuses),
    }


def streaks(active_days: set[date], today: date) -> tuple[int, int]:
    """(current, longest) runs of consecutive active days. The current run may end yesterday,
    so a streak isn't lost just because today's practice hasn't happened yet."""
    longest = run = 0
    previous = None
    for day in sorted(active_days):
        run = run + 1 if previous == day - timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    current = 0
    day = today if today in active_days else today - timedelta(days=1)
    while day in active_days:
        current += 1
        day -= timedelta(days=1)
    return current, longest


def _ref(row) -> dict:
    return {"slug": row.slug, "title": row.title, "difficulty": row.difficulty, "topic_name": row.topic_name}


def dashboard(db: Session, user: User, today: date) -> dict:
    evaluation = user_evaluation(db, user)
    problems = problem_rows(db)
    statuses = verdicts_by_problem(db, user.id)
    solved_ids = {problem_id for problem_id, counts in statuses.items() if counts[ACCEPTED]}

    per_day = dict(
        db.execute(
            select(cast(Submission.created_at, Date), func.count())
            .where(Submission.user_id == user.id, JUDGED_SUBMISSION)
            .group_by(cast(Submission.created_at, Date))
        ).all()
    )
    current_streak, longest_streak = streaks(set(per_day), today)
    activity = [
        {"date": day, "submissions": per_day.get(day, 0)}
        for day in (today - timedelta(days=offset) for offset in range(ACTIVITY_DAYS - 1, -1, -1))
    ]

    # "Continue": the most recently attempted problem that isn't solved yet.
    last_unsolved_id = db.scalar(
        select(Submission.problem_id)
        .where(Submission.user_id == user.id, JUDGED_SUBMISSION, Submission.problem_id.not_in(solved_ids or [-1]))
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .limit(1)
    )
    by_id = {row.id: row for row in problems}
    # "Next": the first untouched problem in study order.
    next_row = next((row for row in problems if row.id not in statuses), None)

    return {
        **evaluation,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "activity": activity,
        "continue_problem": _ref(by_id[last_unsolved_id]) if last_unsolved_id in by_id else None,
        "next_problem": _ref(next_row) if next_row else None,
        "solved_slugs": [row.slug for row in problems if row.id in solved_ids],
        "attempted_slugs": [row.slug for row in problems if row.id in statuses and row.id not in solved_ids],
    }
