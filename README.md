# AlgoForge

A topic-organized coding practice platform. See [CLAUDE.md](CLAUDE.md) for the full plan.

▶ **[Watch the 67-second demo](docs/media/algoforge-demo.mp4)**

Built so far: auth, the sandboxed Python judge, the editor, notes for all 10 topics, and 75 problems. Every problem has a "how to think" guide plus brute-force and optimized solutions, each with a dry run, line-by-line notes and a flowchart. There is also a landing page, a study dashboard, a profile page and an admin portal. Python is the only language for now; C++ and Java come later.

## Run

Needs Docker and Python 3 (Python only generates `.env`).

```bash
python scripts/init_env.py
docker compose up -d --build
docker compose exec api python -m app.seed
```

- API docs: http://localhost:8000/docs
- Re-run the seed after editing anything in `backend/content/`; it updates rows in place.

That's the development stack (hot reload, Vite dev server). To put the site live on a server with HTTPS, see [DEPLOY.md](DEPLOY.md): `docker-compose.prod.yml`, Caddy, `scripts/deploy.sh` and `scripts/backup.sh`.

## App

Open http://localhost:5173. Signed out, it's a landing page with the study path; **Sign in** / **Sign up** are at `/login` and `/signup`. Signed in, the same page is your dashboard: streaks, a continue/next problem, solved counts by difficulty, a 14-day activity chart, per-topic progress and assessment (strengths and weaknesses), and recent submissions. `/profile` shows account details and stats, and lets you change your password. `/problems` lists everything by topic, with difficulty and status filters.

Each topic page (`/topics/<slug>`) has the notes followed by its problems. Each problem opens a split-pane editor: the description on the left, Monaco on the right, and Testcase/Result tabs below. **Run** (Ctrl+Enter) uses the cases in the Testcase tab, which you can edit; **Submit** (Ctrl+Shift+Enter) judges against every case, hidden ones included. Running code needs an account. The **Solution** tab shows the guide: how to think about the problem, then Brute Force / Optimized with code, synced line notes, complexity and a flowchart.

Code is LeetCode style: fill in `class Solution`. `print` output appears under Stdout and doesn't affect the verdict. How each problem's method is called lives in `backend/content/entries.json`; see `backend/app/drivers.py`.

The first editor load after starting the stack is slow in dev mode on Docker Desktop for Windows (the file mount is slow); later loads are faster.

## Students and admins

There are two kinds of account. **Students** sign up at `/signup` and sign in at `/login`. **Admins** sign in at `/admin/login`; the sign-in card has a Student / Admin switch. The admin sign-in refuses student accounts, and sign-up always creates a student, so nobody can make themselves an admin.

Create the first admin from the command line. The command asks for a password; run it again on an existing account to promote it.

```bash
docker compose exec api python -m app.create_admin <username> <email>
```

After that, admins can give or remove admin access on any user's page in the console. They can't remove their own.

## Admin console

Sign in at http://localhost:5173/admin/login. Admins also get an **Admin** link in the main site's nav.

- **Students**: every student's solved count, attempts, submissions and acceptance rate. Each student's page shows topic scores, strengths, weaknesses, results by difficulty and recent submissions. The filter also shows admins.
- **Problems**: every problem with its test-case counts and whether it's complete (visible and hidden cases, how to think, both solutions). **+ New problem** and each problem's editor have three tabs:
  - **Details**: title, slug, topic, difficulty, position, flagship, the statement and constraints (markdown with preview), examples, and how the code is called (the entry JSON, with templates and a live preview of the starter code students get).
  - **Test cases**: add, edit, delete, and mark cases visible or hidden. Inputs are checked against the entry (number of lines, valid JSON, known operations) and saved in compact form.
  - **Solution guide**: "How to think", then the brute-force and optimized solutions. Each has a title, complexity, explanation, code in Monaco, line notes (`3-5: note`) and a Mermaid flowchart with a live preview. **Test against all cases** runs the code through the real judge, hidden cases included. **Preview** shows the solution exactly as students see it.

Scripts can still call the admin API with the `X-Admin-Key: <ADMIN_API_KEY>` header instead of an admin's token.

**Edits and the seed:** `python -m app.seed` rewrites the problems that come from `backend/content/` with what's in the files. Admin edits to those 75 problems are overwritten on the next seed, so make lasting changes to them in the content files. Problems created in the console aren't in the files, so the seed leaves them alone.

Topic score = 70% difficulty-weighted problems solved (Easy 1, Medium 2, Hard 3) + 30% solves per submission. 70 or above is a strength, below 40 is a weakness. The rules are in `backend/app/evaluation.py`.

To try the console without real students, add fake `demo_*` users:

```bash
docker compose exec api python -m app.seed_demo
```

## Test

Uses a throwaway `algoforge_test` database, created and dropped by the test run. Run from the worker, which has Docker access, so the sandbox attack tests run too.

```bash
docker compose exec worker pytest
```

## Code execution

`POST /submissions` queues the code in Redis and returns at once. The worker (RQ) runs it in a new container and writes the verdict back. Poll `GET /submissions/{id}` until `status` is no longer `pending` or `running`.

The worker wraps the user's class in a driver that reads the test case from stdin, calls the method and prints the answer after a marker line. Verdicts are `Accepted`, `Wrong Answer`, `TLE` and `Runtime Error`. `System Error` means the platform failed, and it doesn't count against the user.

Each case gets 2 CPU seconds (4 wall-clock) and 256 MB. The container has no network, a read-only filesystem and almost no capabilities. User code runs as an unprivileged user and everything it leaves behind is wiped between cases. See `sandbox/python/harness.py` and `backend/app/sandbox.py`.

The worker mounts the Docker socket, which gives it root-equivalent access to the host. User code never runs in the worker itself, but keep the worker off any machine you aren't willing to expose to a bug in this design.

## API

| Method | Path | Access |
|---|---|---|
| POST | `/auth/signup` | public |
| POST | `/auth/login` (form-encoded `username`, `password`; `?portal=admin` for the admin sign-in) | public |
| GET | `/auth/me` | Bearer token |
| POST | `/auth/change-password` (`current_password`, `new_password`) | Bearer token |
| GET | `/me/dashboard`, `/me/progress` | Bearer token |
| GET | `/topics`, `/topics/{slug}` | public |
| POST | `/topics` | `X-Admin-Key` |
| PATCH, DELETE | `/topics/{slug}` | `X-Admin-Key` |
| GET | `/problems` (`?topic=&difficulty=&limit=&offset=`), `/problems/{slug}`, `/problems/{slug}/solutions` | public |
| POST | `/problems` | `X-Admin-Key` |
| PATCH, DELETE | `/problems/{slug}` | `X-Admin-Key` |
| POST | `/submissions` (`problem_slug`, `language`, `code`, `mode`: `run` or `submit`) | Bearer token |
| GET | `/submissions` (`?problem=&limit=&offset=`), `/submissions/{id}` | Bearer token (own only) |
| GET | `/admin/users` (`?search=&role=&limit=&offset=`), `/admin/users/{id}/evaluation` | admin |
| PATCH | `/admin/users/{id}/role` (`role`: `student` or `admin`) | admin |
| GET | `/admin/problems`, `/admin/problems/{slug}` (includes hidden cases and the entry) | admin |
| POST | `/admin/problems/{slug}/test-cases` (`input`, `expected_output`, `is_hidden`) | admin |
| PATCH, DELETE | `/admin/test-cases/{id}` | admin |
| PUT, DELETE | `/admin/problems/{slug}/solutions/{brute_force or optimized}` | admin |

"admin" means a Bearer token for an admin account, or `X-Admin-Key: <ADMIN_API_KEY>` from `.env`; the `X-Admin-Key` rows above accept either one too. `PATCH /problems/{slug}` also takes `thinking` (the "How to think" markdown). Hidden test cases are only ever returned by the `/admin` endpoints.

## Content

- `backend/content/topics.json`: the topics
- `backend/content/problems/<topic-slug>.json`: statements, examples, test cases
- `backend/content/notes/<topic-slug>.md`: topic notes (optional; picked up by the seed), shown at `/topics/<topic-slug>`

Notes follow one format, checked by `tests/test_notes.py`: sections `## The idea`, `## Built-in functions` (a table with Python, C++ and Java columns), `## Pitfalls` and `## Worked example: …`, using `##` headings only, since the page supplies the title. Every ```` ```python ```` block runs during the tests, so put `assert`s in examples to keep them honest.

- `backend/content/solutions/<problem-slug>.md`: the problem's guide: `## How to think`, then one `## Approach …` section each for brute force and optimized (`<!-- approach: … | time: … | space: … -->`), each with `### Code`, `### Line by line` and `### Flowchart`. `app/solution_content.py` parses and validates it, and `tests/test_solutions.py` submits each approach's code through the driver. Keep the time and space strings under 50 characters.
- `backend/content/entries.json`: how each problem's method is called and its arguments are built (lists, trees, graphs, design classes, codecs).
- Diagrams are Mermaid in ```` ```mermaid ```` blocks. The page colours them by shape: rounded `([ ])` for start/end, `{ }` for decisions, and `[ ]` for steps.

To add problems, write a `backend/scripts/batch_<name>.py` that calls `scripts/problem_tool.py`, and add a reference solution to `tests/reference_solutions.py`. Expected outputs are computed from the reference, never typed by hand. Then run:

```bash
docker compose exec -w /app worker python -m scripts.batch_<name>
docker compose exec worker python -m app.seed
```

Test case `input` holds one JSON value per line and `expected_output` holds compact JSON, so every language reads and prints the same format. `backend/tests/reference_solutions.py` checks all examples and test cases against independent solutions.
