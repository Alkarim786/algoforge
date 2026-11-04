from datetime import UTC, date, datetime, timedelta

from app.models import Problem, Submission, Topic, User
from app.progress import streaks


def auth(client, username="learner"):
    password = "correct-horse"
    client.post("/auth/signup", json={"username": username, "email": f"{username}@example.com", "password": password})
    token = client.post("/auth/login", data={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_world(db):
    topic = Topic(name="Array", slug="array", order=1)
    db.add(topic)
    db.flush()
    problems = [
        Problem(topic_id=topic.id, title=f"P{i}", slug=f"p{i}", difficulty="Easy", description="d", order_within_topic=i)
        for i in range(3)
    ]
    db.add_all(problems)
    db.commit()
    return problems


def submit(db, user_id, problem, status, days_ago=0, kind="submit"):
    db.add(
        Submission(
            user_id=user_id,
            problem_id=problem.id,
            language="python",
            code="x",
            status=status,
            kind=kind,
            created_at=datetime.now(UTC) - timedelta(days=days_ago),
        )
    )
    db.commit()


def test_streaks():
    today = date(2026, 11, 3)
    day = lambda n: today - timedelta(days=n)  # noqa: E731
    assert streaks(set(), today) == (0, 0)
    assert streaks({day(0), day(1), day(2)}, today) == (3, 3)
    assert streaks({day(1), day(2)}, today) == (2, 2)  # not broken until a whole day is missed
    assert streaks({day(2), day(3), day(4), day(5)}, today) == (0, 4)


def test_dashboard_requires_login(client):
    assert client.get("/me/dashboard").status_code == 401
    assert client.get("/me/progress").status_code == 401


def test_dashboard(client, db):
    headers = auth(client)
    user_id = db.query(User).one().id
    p0, p1, p2 = make_world(db)
    submit(db, user_id, p0, "Wrong Answer", days_ago=1)
    submit(db, user_id, p0, "Accepted", days_ago=0)
    submit(db, user_id, p1, "TLE", days_ago=0)
    submit(db, user_id, p2, "Accepted", kind="run")  # runs never count

    body = client.get("/me/dashboard", headers=headers).json()
    assert (body["solved"], body["attempted"], body["total_problems"]) == (1, 2, 3)
    assert body["current_streak"] == 2
    assert len(body["activity"]) == 14
    assert body["activity"][-1]["submissions"] == 2
    assert body["continue_problem"]["slug"] == "p1"
    assert body["next_problem"]["slug"] == "p2"
    assert body["solved_slugs"] == ["p0"]
    assert body["attempted_slugs"] == ["p1"]
    assert body["user"]["username"] == "learner"

    assert client.get("/me/progress", headers=headers).json() == {"solved": ["p0"], "attempted": ["p1"]}


def test_new_user_dashboard(client, db):
    headers = auth(client)
    make_world(db)
    body = client.get("/me/dashboard", headers=headers).json()
    assert body["current_streak"] == 0
    assert body["continue_problem"] is None
    assert body["next_problem"]["slug"] == "p0"


def test_change_password(client):
    headers = auth(client)
    wrong = {"current_password": "nope-nope", "new_password": "brand-new-pass"}
    assert client.post("/auth/change-password", json=wrong, headers=headers).status_code == 400
    short = {"current_password": "correct-horse", "new_password": "short"}
    assert client.post("/auth/change-password", json=short, headers=headers).status_code == 422
    good = {"current_password": "correct-horse", "new_password": "brand-new-pass"}
    assert client.post("/auth/change-password", json=good, headers=headers).status_code == 204
    assert client.post("/auth/login", data={"username": "learner", "password": "correct-horse"}).status_code == 401
    assert client.post("/auth/login", data={"username": "learner", "password": "brand-new-pass"}).status_code == 200
