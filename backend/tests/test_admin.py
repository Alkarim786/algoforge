from collections import Counter
from types import SimpleNamespace

import pytest

from app.evaluation import classify, evaluate
from app.models import Problem, Submission, Topic, User


def info(id, topic, difficulty="Easy"):
    return SimpleNamespace(id=id, difficulty=difficulty, topic_slug=topic, topic_name=topic.title())


@pytest.fixture
def world(db):
    array = Topic(name="Array", slug="array", order=1)
    heap = Topic(name="Heap", slug="heap", order=2)
    db.add_all([array, heap])
    db.flush()
    p1 = Problem(topic_id=array.id, title="A", slug="a", difficulty="Easy", description="d")
    p2 = Problem(topic_id=heap.id, title="B", slug="b", difficulty="Hard", description="d")
    strong = User(username="strong", email="strong@example.com", password_hash="x")
    idle = User(username="idle_100%", email="idle@example.com", password_hash="x")
    db.add_all([p1, p2, strong, idle])
    db.flush()

    def submit(problem, verdict):
        db.add(Submission(user_id=strong.id, problem_id=problem.id, language="python", code="SECRET", status=verdict))

    submit(p1, "Accepted")
    submit(p1, "Accepted")  # a repeat solve must not count twice
    submit(p2, "TLE")
    submit(p2, "TLE")
    submit(p2, "pending")  # not judged yet: must be ignored
    db.commit()
    return SimpleNamespace(strong=strong, idle=idle)


@pytest.mark.parametrize(
    "score,attempted,expected",
    [
        (0, 0, "not_attempted"),
        (0, 1, "weakness"),
        (39, 1, "weakness"),
        (40, 1, "developing"),
        (69, 1, "developing"),
        (70, 1, "strength"),
    ],
)
def test_classify_boundaries(score, attempted, expected):
    assert classify(score, attempted) == expected


def test_score_weights_coverage_by_difficulty_and_rewards_first_try():
    problems = [info(1, "x", "Easy"), info(2, "x", "Hard")]
    # Easy solved first try, Hard untouched: coverage 1/4, efficiency 1.
    assert evaluate(problems, {1: Counter(Accepted=1)})["topics"][0]["score"] == 48
    # Everything solved, but 4 submissions for 2 problems: coverage 1, efficiency 0.5.
    both = {1: Counter(Accepted=1), 2: Counter({"Accepted": 1, "Wrong Answer": 2})}
    topic = evaluate(problems, both)["topics"][0]
    assert topic["score"] == 85
    assert topic["top_failure"] == "Wrong Answer"


def test_strengths_best_first_weaknesses_worst_first():
    problems = [info(1, "a"), info(2, "a"), info(3, "b"), info(4, "c"), info(5, "d"), info(6, "e")]
    statuses = {
        1: Counter(Accepted=1),
        2: Counter({"Accepted": 1, "TLE": 1}),  # a: 90
        3: Counter(Accepted=1),  # b: 100
        4: Counter(TLE=1),  # c: 0
    }
    result = evaluate(problems, statuses)
    assert result["strengths"] == ["B", "A"]
    assert result["weaknesses"] == ["C"]
    assert result["not_attempted"] == ["D", "E"]


def test_admin_endpoints_require_key(client, world):
    for headers in ({}, {"X-Admin-Key": "wrong"}):
        assert client.get("/admin/users", headers=headers).status_code == 403
        assert client.get(f"/admin/users/{world.strong.id}/evaluation", headers=headers).status_code == 403


def test_user_list(client, admin_headers, world):
    body = client.get("/admin/users", headers=admin_headers).json()
    assert (body["total_users"], body["total_problems"]) == (2, 2)
    top, bottom = body["users"]
    assert top["username"] == "strong"
    assert (top["solved"], top["attempted"], top["submissions"], top["acceptance_rate"]) == (1, 2, 4, 0.5)
    assert (bottom["solved"], bottom["submissions"], bottom["acceptance_rate"]) == (0, 0, None)


def test_user_list_search_treats_wildcards_literally(client, admin_headers, world):
    search = lambda term: client.get("/admin/users", params={"search": term}, headers=admin_headers).json()
    assert [user["username"] for user in search("100%")["users"]] == ["idle_100%"]
    assert search("%")["total_users"] == 1
    assert search("STRONG@")["total_users"] == 1


def test_evaluation(client, admin_headers, world):
    response = client.get(f"/admin/users/{world.strong.id}/evaluation", headers=admin_headers)
    body = response.json()
    assert "SECRET" not in response.text and "password" not in response.text
    assert (body["solved"], body["attempted"], body["total_problems"]) == (1, 2, 2)
    assert body["strengths"] == ["Array"]
    assert body["weaknesses"] == ["Heap"]
    heap = body["topics"][1]
    assert (heap["score"], heap["top_failure"], heap["submissions"]) == (0, "TLE", 2)
    assert body["difficulty"] == [
        {"difficulty": "Easy", "solved": 1, "total": 1},
        {"difficulty": "Medium", "solved": 0, "total": 0},
        {"difficulty": "Hard", "solved": 0, "total": 1},
    ]
    assert len(body["recent_submissions"]) == 5


def test_evaluation_with_no_submissions_and_missing_user(client, admin_headers, world):
    body = client.get(f"/admin/users/{world.idle.id}/evaluation", headers=admin_headers).json()
    assert body["acceptance_rate"] is None
    assert body["not_attempted"] == ["Array", "Heap"]
    assert client.get("/admin/users/99999/evaluation", headers=admin_headers).status_code == 404
