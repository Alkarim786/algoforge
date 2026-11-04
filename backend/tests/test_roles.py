"""Student and admin accounts, the admin sign-in, and admin content editing."""
import pytest

from app.content_checks import check_case, validate_entry
from app.create_admin import create_admin
from app.models import User
from app.seed import load_problems
from app.security import hash_password

PASSWORD = "correct-horse"
ENTRY = {"method": "addTwo", "params": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}], "returns": "int"}
PROBLEM = {"topic_slug": "array", "title": "Add Two", "slug": "add-two", "difficulty": "Easy", "description": "d", "entry": ENTRY}
SOLUTION = {
    "title": "Just add",
    "time_complexity": "O(1)",
    "space_complexity": "O(1)",
    "explanation": "Add them.",
    "code": "class Solution:\n    def addTwo(self, a: int, b: int) -> int:\n        return a + b\n",
    "line_notes": [{"start": 3, "end": 3, "note": "The sum."}],
    "flowchart_mermaid": "flowchart TD\n    A --> B",
}


def sign_in(client, username, portal=None):
    params = {"portal": portal} if portal else {}
    return client.post("/auth/login", data={"username": username, "password": PASSWORD}, params=params)


def bearer(client, username, portal=None):
    return {"Authorization": f"Bearer {sign_in(client, username, portal).json()['access_token']}"}


@pytest.fixture
def accounts(db):
    admin = User(username="boss", email="boss@example.com", password_hash=hash_password(PASSWORD), role="admin")
    student = User(username="kid", email="kid@example.com", password_hash=hash_password(PASSWORD))
    db.add_all([admin, student])
    db.commit()
    return admin, student


@pytest.fixture
def problem(client, admin_headers):
    client.post("/topics", json={"name": "Array", "slug": "array", "order": 1}, headers=admin_headers)
    assert client.post("/problems", json=PROBLEM, headers=admin_headers).status_code == 201
    return PROBLEM["slug"]


def test_signup_always_makes_a_student(client):
    body = {"username": "new", "email": "new@example.com", "password": PASSWORD, "role": "admin"}
    assert client.post("/auth/signup", json=body).json()["role"] == "student"


def test_admin_sign_in_rejects_students(client, accounts):
    assert sign_in(client, "kid", "admin").status_code == 403
    assert sign_in(client, "kid").status_code == 200
    assert sign_in(client, "boss", "admin").status_code == 200
    assert sign_in(client, "boss").status_code == 200  # admins can use the student sign-in too
    assert sign_in(client, "kid", "teacher").status_code == 422


def test_admin_endpoints_by_role(client, accounts, problem):
    student, admin = bearer(client, "kid"), bearer(client, "boss", "admin")
    for path in ("/admin/users", "/admin/problems", f"/admin/problems/{problem}"):
        assert client.get(path, headers=student).status_code == 403
        assert client.get(path).status_code == 403
        assert client.get(path, headers=admin).status_code == 200
    assert client.patch(f"/problems/{problem}", json={"title": "X"}, headers=student).status_code == 403
    assert client.patch(f"/problems/{problem}", json={"title": "X"}, headers=admin).status_code == 200
    assert client.get("/auth/me", headers=admin).json()["role"] == "admin"


def test_role_changes(client, accounts):
    admin_user, student_user = accounts
    admin = bearer(client, "boss", "admin")
    students = client.get("/admin/users", params={"role": "student"}, headers=admin).json()
    assert [user["username"] for user in students["users"]] == ["kid"]

    promoted = client.patch(f"/admin/users/{student_user.id}/role", json={"role": "admin"}, headers=admin)
    assert promoted.json()["role"] == "admin"
    assert sign_in(client, "kid", "admin").status_code == 200
    demote_self = client.patch(f"/admin/users/{admin_user.id}/role", json={"role": "student"}, headers=admin)
    assert demote_self.status_code == 400
    assert client.patch(f"/admin/users/{student_user.id}/role", json={"role": "owner"}, headers=admin).status_code == 422


def test_create_admin_command(db):
    user, created = create_admin(db, "root", "Root@Example.com", PASSWORD)
    assert created and user.role == "admin" and user.email == "root@example.com"
    db.add(User(username="kid", email="kid@example.com", password_hash=hash_password(PASSWORD)))
    db.commit()
    user, created = create_admin(db, "kid", "kid@example.com", None)  # promote, keeping the password
    assert not created and user.role == "admin"
    with pytest.raises(ValueError):
        create_admin(db, "kid", "root@example.com", None)  # two different accounts
    with pytest.raises(ValueError):
        create_admin(db, "nobody", "nobody@example.com", None)  # a new account needs a password


def test_entry_validation(client, admin_headers, problem):
    bad_entries = [
        {"method": "f", "params": [], "returns": "int", "extra": 1},
        {"method": "not valid", "params": [], "returns": "int"},
        {"method": "f", "params": [{"name": "a", "type": "int; import os"}], "returns": "int"},
        {"method": "f", "params": [], "returns": "int", "normalize": "shuffled"},
        {"class": "Box", "operations": {}},
        "just a string",
    ]
    for entry in bad_entries:
        assert client.patch(f"/problems/{problem}", json={"entry": entry}, headers=admin_headers).status_code == 422
    for existing in load_problems():
        validate_entry(existing.entry)  # every shipped entry is valid


def test_every_shipped_case_passes_the_admin_checks():
    for existing in load_problems():
        for case in existing.test_cases:
            assert check_case(existing.entry, case.input, case.expected_output) == (case.input, case.expected_output)


def test_test_case_editing(client, admin_headers, problem):
    add = lambda body: client.post(f"/admin/problems/{problem}/test-cases", json=body, headers=admin_headers)  # noqa: E731
    created = add({"input": "2\n 3 \n", "expected_output": " 5 ", "is_hidden": True})
    assert created.status_code == 201
    case = created.json()
    assert (case["input"], case["expected_output"], case["is_hidden"]) == ("2\n3", "5", True)

    assert add({"input": "2", "expected_output": "5"}).status_code == 422  # one line, needs two
    assert add({"input": "2\n[3", "expected_output": "5"}).status_code == 422  # not JSON
    assert add({"input": "2\n3", "expected_output": "five"}).status_code == 422

    # Hidden cases show up for admins only.
    assert client.get(f"/problems/{problem}").json()["sample_test_cases"] == []
    detail = client.get(f"/admin/problems/{problem}", headers=admin_headers).json()
    assert [c["is_hidden"] for c in detail["test_cases"]] == [True]

    updated = client.patch(f"/admin/test-cases/{case['id']}", json={"is_hidden": False}, headers=admin_headers).json()
    assert updated["is_hidden"] is False
    assert client.get(f"/problems/{problem}").json()["sample_test_cases"][0]["input"] == "2\n3"
    assert client.patch(f"/admin/test-cases/{case['id']}", json={"expected_output": "?"}, headers=admin_headers).status_code == 422
    assert client.delete(f"/admin/test-cases/{case['id']}", headers=admin_headers).status_code == 204
    assert client.delete(f"/admin/test-cases/{case['id']}", headers=admin_headers).status_code == 404

    rows = client.get("/admin/problems", headers=admin_headers).json()
    assert rows[0]["slug"] == problem and (rows[0]["visible_cases"], rows[0]["hidden_cases"]) == (0, 0)


def test_class_cases_are_checked_against_operations(client, admin_headers, problem):
    entry = {"class": "Box", "operations": {"put": {"method": "put", "params": [{"name": "x", "type": "int"}]}}}
    client.patch(f"/problems/{problem}", json={"entry": entry}, headers=admin_headers)
    add = lambda body: client.post(f"/admin/problems/{problem}/test-cases", json=body, headers=admin_headers)  # noqa: E731
    assert add({"input": '[["put", 1]]', "expected_output": "[]"}).status_code == 201
    assert add({"input": '[["take", 1]]', "expected_output": "[]"}).status_code == 422


def test_solution_editing(client, admin_headers, problem):
    path = f"/admin/problems/{problem}/solutions"
    assert client.put(f"{path}/optimized", json=SOLUTION, headers=admin_headers).status_code == 200
    brute = {**SOLUTION, "title": "Count up"}
    assert client.put(f"{path}/brute_force", json=brute, headers=admin_headers).status_code == 200
    client.patch(f"/problems/{problem}", json={"thinking": "Think."}, headers=admin_headers)

    guide = client.get(f"/problems/{problem}/solutions").json()
    assert guide["thinking"] == "Think."
    assert [a["approach_type"] for a in guide["approaches"]] == ["brute_force", "optimized"]
    assert guide["approaches"][1]["code"] == {"python": SOLUTION["code"]}

    edited = client.put(f"{path}/optimized", json={**SOLUTION, "title": "Plus"}, headers=admin_headers)
    assert edited.json()["title"] == "Plus"
    assert client.put(f"{path}/greedy", json=SOLUTION, headers=admin_headers).status_code == 422
    bad_notes = {**SOLUTION, "line_notes": [{"start": 2, "end": 9, "note": "x"}]}
    assert client.put(f"{path}/optimized", json=bad_notes, headers=admin_headers).status_code == 422
    too_long = {**SOLUTION, "time_complexity": "O(" + "n" * 60 + ")"}
    assert client.put(f"{path}/optimized", json=too_long, headers=admin_headers).status_code == 422

    assert client.delete(f"{path}/brute_force", headers=admin_headers).status_code == 204
    assert client.delete(f"{path}/brute_force", headers=admin_headers).status_code == 404
    assert len(client.get(f"/problems/{problem}/solutions").json()["approaches"]) == 1
