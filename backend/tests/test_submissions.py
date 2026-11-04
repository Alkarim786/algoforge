import pytest
from redis import RedisError

from app import worker
from app.models import Problem, Submission, TestCase, Topic
from app.routers import submissions as submissions_router
from app.sandbox import CaseRun, SandboxError, SandboxKilled

GOOD = "CORRECT"
ECHO_SECRET = "ECHO"


def fake_run_code(language, code, inputs):
    """Stands in for Docker here; test_sandbox.py covers the real one."""
    if code == GOOD:
        return [CaseRun("ok", value * 2, "", 5, 100) for value in inputs]
    if code == ECHO_SECRET:
        return [CaseRun("ok", value, value, 5, 100) for value in inputs]
    if code == "NUL":
        return [CaseRun("ok", "a\x00b", "c\x00d", 5, 100) for _ in inputs]
    if code == "TLE":
        return [CaseRun("tle", "", "", 2000, 100)]
    if code == "CRASH":
        return [CaseRun("runtime_error", "", "Traceback", 5, 100) for _ in inputs]
    if code == "KILLED":
        raise SandboxKilled
    raise SandboxError("docker is down")


@pytest.fixture(autouse=True)
def synchronous_judge(monkeypatch):
    monkeypatch.setattr(worker, "run_code", fake_run_code)
    monkeypatch.setattr(submissions_router, "enqueue", worker.judge_submission)


@pytest.fixture
def problem(db):
    topic = Topic(name="Array", slug="array", order=1)
    db.add(topic)
    db.flush()
    problem = Problem(topic_id=topic.id, title="P", slug="p", difficulty="Easy", description="d")
    db.add(problem)
    db.flush()
    db.add_all(
        [
            TestCase(problem_id=problem.id, input="vis", expected_output="visvis"),
            TestCase(problem_id=problem.id, input="SECRET", expected_output="SECRETSECRET", is_hidden=True),
        ]
    )
    db.commit()
    return problem


def auth(client, username="karim"):
    password = "correct-horse"
    client.post("/auth/signup", json={"username": username, "email": f"{username}@example.com", "password": password})
    token = client.post("/auth/login", data={"username": username, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def submit(client, headers, code=GOOD, mode="submit", slug="p"):
    return client.post(
        "/submissions", json={"problem_slug": slug, "language": "python", "code": code, "mode": mode}, headers=headers
    )


def detail(client, headers, response):
    return client.get(f"/submissions/{response.json()['id']}", headers=headers)


def test_requires_login(client, problem):
    assert client.post("/submissions", json={}).status_code == 401
    assert client.get("/submissions").status_code == 401


def test_validation(client, problem):
    headers = auth(client)
    assert submit(client, headers, slug="nope").status_code == 404
    assert submit(client, headers, code="").status_code == 422
    assert submit(client, headers, code="x" * 64_001).status_code == 422
    bad_language = {"problem_slug": "p", "language": "cobol", "code": "x"}
    assert client.post("/submissions", json=bad_language, headers=headers).status_code == 422


def test_problem_without_cases_is_rejected(client, problem, db):
    db.add(Problem(topic_id=problem.topic_id, title="Q", slug="q", difficulty="Easy", description="d"))
    db.commit()
    assert submit(client, auth(client), slug="q").status_code == 409


def test_submit_runs_all_cases_and_masks_hidden_ones(client, problem):
    headers = auth(client)
    response = submit(client, headers)
    assert response.status_code == 202
    result = detail(client, headers, response)
    body = result.json()
    assert body["status"] == "Accepted"
    assert [case["is_hidden"] for case in body["results"]] == [False, True]
    assert body["results"][0]["expected_output"] == "visvis"
    assert body["results"][1]["passed"] is True
    assert body["results"][1]["input"] is None
    assert "SECRET" not in result.text


def test_hidden_output_and_stderr_never_returned(client, problem):
    headers = auth(client)
    result = detail(client, headers, submit(client, headers, code=ECHO_SECRET))
    assert result.json()["status"] == "Wrong Answer"
    assert "SECRET" not in result.text


def test_run_mode_uses_visible_cases_only(client, problem):
    headers = auth(client)
    body = detail(client, headers, submit(client, headers, mode="run")).json()
    assert body["mode"] == "run"
    assert len(body["results"]) == 1


def test_custom_inputs_compare_only_against_visible_cases(client, problem):
    headers = auth(client)
    payload = {"problem_slug": "p", "language": "python", "code": GOOD, "mode": "run"}
    response = client.post(
        "/submissions", json={**payload, "custom_inputs": ["vis", "mine", "SECRET"]}, headers=headers
    )
    body = detail(client, headers, response).json()
    assert body["status"] == "Finished"
    assert [case["verdict"] for case in body["results"]] == ["Accepted", "Finished", "Finished"]
    assert body["results"][0]["expected_output"] == "visvis"
    assert body["results"][1]["input"] == "mine"
    # Typing a hidden input must not reveal that it's a hidden case, or its expected output.
    assert body["results"][2]["expected_output"] is None
    assert body["results"][2]["is_hidden"] is False
    assert "SECRETSECRET" not in response.text


def test_custom_inputs_rejected_on_submit(client, problem):
    payload = {"problem_slug": "p", "language": "python", "code": GOOD, "mode": "submit", "custom_inputs": ["x"]}
    assert client.post("/submissions", json=payload, headers=auth(client)).status_code == 422


def test_custom_inputs_work_without_stored_cases(client, problem, db):
    db.add(Problem(topic_id=problem.topic_id, title="Q", slug="q", difficulty="Easy", description="d"))
    db.commit()
    headers = auth(client)
    payload = {"problem_slug": "q", "language": "python", "code": GOOD, "mode": "run", "custom_inputs": ["x"]}
    response = client.post("/submissions", json=payload, headers=headers)
    assert detail(client, headers, response).json()["status"] == "Finished"
    assert client.get("/problems/q").json()["can_submit"] is False


def test_verdicts(client, problem):
    headers = auth(client)
    assert detail(client, headers, submit(client, headers, code="TLE")).json()["status"] == "TLE"
    assert detail(client, headers, submit(client, headers, code="CRASH")).json()["status"] == "Runtime Error"
    assert detail(client, headers, submit(client, headers, code="KILLED")).json()["status"] == "Runtime Error"


def test_platform_failure_is_not_blamed_on_user(client, problem, admin_headers):
    headers = auth(client)
    assert detail(client, headers, submit(client, headers, code="BROKEN")).json()["status"] == "System Error"
    row = client.get("/admin/users", headers=admin_headers).json()["users"][0]
    assert row["submissions"] == 0


def test_nul_bytes_in_output_are_stored(client, problem):
    headers = auth(client)
    body = detail(client, headers, submit(client, headers, code="NUL")).json()
    assert "b" in body["results"][0]["actual_output"]


def test_other_users_submissions_are_invisible(client, problem):
    owner = auth(client, "owner")
    response = submit(client, owner)
    assert detail(client, auth(client, "stranger"), response).status_code == 404


def test_history_and_run_mode_excluded_from_stats(client, problem, admin_headers):
    headers = auth(client)
    submit(client, headers, mode="run")
    submit(client, headers, code="CRASH")
    history = client.get("/submissions", headers=headers).json()
    assert [item["status"] for item in history] == ["Runtime Error"]

    row = client.get("/admin/users", headers=admin_headers).json()["users"][0]
    assert (row["solved"], row["submissions"]) == (0, 1)
    evaluation = client.get(f"/admin/users/{row['id']}/evaluation", headers=admin_headers).json()
    assert evaluation["solved"] == 0
    assert len(evaluation["recent_submissions"]) == 1


def test_in_flight_limit(client, problem, monkeypatch):
    monkeypatch.setattr(submissions_router, "enqueue", lambda _: None)
    headers = auth(client)
    assert [submit(client, headers).status_code for _ in range(4)] == [202, 202, 202, 429]


def test_queue_outage_returns_503(client, problem, monkeypatch, db):
    def down(_):
        raise RedisError

    monkeypatch.setattr(submissions_router, "enqueue", down)
    assert submit(client, auth(client)).status_code == 503
    assert db.query(Submission).one().status == "System Error"


def test_rerun_of_finished_job_is_ignored(client, problem):
    headers = auth(client)
    response = submit(client, headers)
    worker.judge_submission(response.json()["id"])
    assert len(detail(client, headers, response).json()["results"]) == 2
