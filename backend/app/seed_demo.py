"""Fake users and submissions for trying the admin portal before the Phase 2 judge exists. Local dev only.

Replaces only the demo_* users listed below. Run after app.seed with: python -m app.seed_demo
"""
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import Submission, Topic, User
from app.security import hash_password

# username -> {topic slug: (problems solved, failed submissions, failure verdict)}
PROFILES = {
    "demo_array_ace": {
        "array": (2, 0, "Wrong Answer"),
        "binary": (2, 1, "Wrong Answer"),
        "string": (2, 1, "Runtime Error"),
        "dynamic-programming": (0, 5, "TLE"),
        "graph": (1, 7, "TLE"),
    },
    "demo_dp_learner": {
        "dynamic-programming": (2, 2, "Wrong Answer"),
        "tree": (1, 2, "Runtime Error"),
        "array": (1, 4, "TLE"),
    },
    "demo_newcomer": {"array": (0, 3, "Wrong Answer")},
    "demo_no_submissions": {},
}


def main() -> None:
    now = datetime.now(UTC)
    # Hashing a random password leaves these accounts impossible to log in to.
    unusable_hash = hash_password(secrets.token_urlsafe(32))
    with SessionLocal() as db:
        db.execute(delete(User).where(User.username.in_(PROFILES)))
        topics = {topic.slug: topic for topic in db.scalars(select(Topic))}
        if not topics:
            raise SystemExit("No topics found. Run python -m app.seed first.")
        for username, profile in PROFILES.items():
            user = User(username=username, email=f"{username}@example.com", password_hash=unusable_hash)
            db.add(user)
            db.flush()
            age = 0
            for slug, (solved, failed, verdict) in profile.items():
                problems = topics[slug].problems
                for i in range(failed):
                    # Failures land on the first unsolved problem, or the last solved one if all are solved.
                    problem = problems[min(solved, len(problems) - 1)]
                    age += 1
                    db.add(
                        Submission(
                            user_id=user.id,
                            problem_id=problem.id,
                            language="python",
                            code="# demo",
                            status=verdict,
                            created_at=now - timedelta(hours=age + 24),
                        )
                    )
                for problem in problems[:solved]:
                    age += 1
                    db.add(
                        Submission(
                            user_id=user.id,
                            problem_id=problem.id,
                            language="python",
                            code="# demo",
                            status="Accepted",
                            created_at=now - timedelta(hours=age),
                        )
                    )
        db.commit()
    print(f"Seeded {len(PROFILES)} demo users.")


if __name__ == "__main__":
    main()
