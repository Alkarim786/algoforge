from app.models import Problem, Submission, TestCase, User

TOPIC = {"name": "Array", "slug": "array", "order": 1}
PROBLEM = {"topic_slug": "array", "title": "Two Sum", "slug": "two-sum", "difficulty": "Easy", "description": "d"}


def test_writes_require_admin_key(client):
    for headers in ({}, {"X-Admin-Key": "wrong"}):
        assert client.post("/topics", json=TOPIC, headers=headers).status_code == 403
        assert client.patch("/topics/array", json={}, headers=headers).status_code == 403
        assert client.delete("/topics/array", headers=headers).status_code == 403
        assert client.post("/problems", json=PROBLEM, headers=headers).status_code == 403
        assert client.patch("/problems/two-sum", json={}, headers=headers).status_code == 403
        assert client.delete("/problems/two-sum", headers=headers).status_code == 403


def test_topic_crud(client, admin_headers):
    assert client.post("/topics", json=TOPIC, headers=admin_headers).status_code == 201
    assert client.post("/topics", json=TOPIC, headers=admin_headers).status_code == 409
    assert client.post("/topics", json={**TOPIC, "name": "B", "slug": "Not A Slug"}, headers=admin_headers).status_code == 422

    updated = client.patch("/topics/array", json={"notes_content": "# Notes"}, headers=admin_headers)
    assert updated.json()["notes_content"] == "# Notes"
    assert client.get("/topics").json()[0]["slug"] == "array"
    assert client.get("/topics/array").json()["problems"] == []

    assert client.delete("/topics/array", headers=admin_headers).status_code == 204
    assert client.get("/topics/array").status_code == 404


def test_problem_crud(client, admin_headers):
    assert client.post("/problems", json=PROBLEM, headers=admin_headers).status_code == 422  # unknown topic
    client.post("/topics", json=TOPIC, headers=admin_headers)
    created = client.post("/problems", json=PROBLEM, headers=admin_headers)
    assert created.status_code == 201
    assert created.json()["topic_slug"] == "array"
    assert client.post("/problems", json=PROBLEM, headers=admin_headers).status_code == 409
    assert client.post("/problems", json={**PROBLEM, "slug": "x", "difficulty": "Nope"}, headers=admin_headers).status_code == 422

    updated = client.patch("/problems/two-sum", json={"title": "New", "slug": "new"}, headers=admin_headers)
    assert updated.status_code == 200
    assert updated.json()["slug"] == "new"
    assert client.patch("/problems/new", json={"title": None}, headers=admin_headers).status_code == 409

    assert client.delete("/topics/array", headers=admin_headers).status_code == 409  # still has a problem
    assert client.delete("/problems/new", headers=admin_headers).status_code == 204
    assert client.get("/problems/new").status_code == 404


def test_problem_filters(client, admin_headers):
    client.post("/topics", json=TOPIC, headers=admin_headers)
    client.post("/topics", json={"name": "Heap", "slug": "heap", "order": 2}, headers=admin_headers)
    client.post("/problems", json=PROBLEM, headers=admin_headers)
    client.post(
        "/problems", json={**PROBLEM, "topic_slug": "heap", "slug": "hard-one", "difficulty": "Hard"}, headers=admin_headers
    )
    assert [p["slug"] for p in client.get("/problems").json()] == ["two-sum", "hard-one"]
    assert [p["slug"] for p in client.get("/problems", params={"topic": "heap"}).json()] == ["hard-one"]
    assert [p["slug"] for p in client.get("/problems", params={"difficulty": "Easy"}).json()] == ["two-sum"]
    assert len(client.get("/problems", params={"limit": 1, "offset": 1}).json()) == 1
    assert client.get("/problems", params={"limit": 0}).status_code == 422


def test_hidden_cases_never_exposed(client, admin_headers, db):
    client.post("/topics", json=TOPIC, headers=admin_headers)
    problem_id = client.post("/problems", json=PROBLEM, headers=admin_headers).json()["id"]
    db.add_all(
        [
            TestCase(problem_id=problem_id, input="visible-in", expected_output="visible-out"),
            TestCase(problem_id=problem_id, input="secret-in", expected_output="secret-out", is_hidden=True),
        ]
    )
    db.commit()

    for response in (
        client.get("/problems/two-sum"),
        client.get("/problems"),
        client.get("/topics/array"),
        client.patch("/problems/two-sum", json={"title": "T"}, headers=admin_headers),
    ):
        assert "secret" not in response.text
    assert client.get("/problems/two-sum").json()["sample_test_cases"][0]["input"] == "visible-in"


def test_problem_with_submissions_cannot_be_deleted(client, admin_headers, db):
    client.post("/topics", json=TOPIC, headers=admin_headers)
    problem_id = client.post("/problems", json=PROBLEM, headers=admin_headers).json()["id"]
    user = User(username="karim", email="k@example.com", password_hash="x")
    db.add(user)
    db.flush()
    db.add(Submission(user_id=user.id, problem_id=problem_id, language="python", code="pass"))
    db.commit()

    assert client.delete("/problems/two-sum", headers=admin_headers).status_code == 409
    assert db.get(Problem, problem_id) is not None
