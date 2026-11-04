# CLAUDE.md — LeetCode-Style Learning Platform

Handoff from a planning session in Claude chat. Everything below is a decision already made with the owner (Karim). Build from this; don't re-open settled choices unless something is technically blocked.

## 1. Goal

A coding practice platform organized by **topic**. Each topic has a **notes/roadmap page** (theory, built-in functions, worked example) followed by its problems. Each problem has a **LeetCode-replica editor** with sandboxed code execution, and a **solution page** (brute force + optimized, line-by-line explanation, flowcharts).

- Scope: **real project over days/weeks**. Proper auth, database, and sandboxed execution. Not a demo.
- Owner's purpose: resume/portfolio piece for software developer / AI-ML engineer roles at top tech companies. Quality and depth beat raw problem count.
- Owner's context: final-year B.Tech CSE, strong DSA background (1,300+ LeetCode solved), already built URLForge (FastAPI, PostgreSQL, Redis, Docker, JWT). Reuse those patterns.

## 2. Tech stack (decided)

- Backend: FastAPI (Python)
- DB: PostgreSQL
- Queue: Redis + Celery or RQ (async submission execution)
- Execution: Docker, one fresh container per submission
- Frontend: React + Monaco Editor
- Diagrams: Mermaid.js (client-side, from stored Mermaid text)
- Markdown: react-markdown or markdown-it
- Auth: JWT + bcrypt

## 3. Database schema

```
users(id, username, email, password_hash, created_at)

topics(id, name, slug, order, notes_content /*markdown*/)

problems(id, topic_id FK, title, slug, difficulty, description /*md*/,
         constraints, examples /*json*/, order_within_topic, is_flagship bool)

test_cases(id, problem_id FK, input, expected_output, is_hidden bool)

submissions(id, user_id FK, problem_id FK, language, code, status, created_at)

submission_results(id, submission_id FK, test_case_id FK, passed bool,
                   actual_output, runtime_ms, memory_kb)

solutions(id, problem_id FK, approach_type /*brute_force|optimized*/,
          code /*per language*/, explanation /*md, line-by-line*/,
          time_complexity, space_complexity, flowchart_mermaid, order)
```

Keep hidden test cases separate from problem statements so Run (visible only) and Submit (all) share one pipeline.

## 4. Modules

**Auth** — `/auth/signup`, `/auth/login`.

**Topics & notes** — `/topics`, `/topics/{slug}` returns notes markdown + ordered problem list. Notes contain: concept explainer, built-in functions per language, one worked example, then the problem list.

**Problems & editor** (LeetCode replica):
- Split pane: description left, Monaco right, resizable divider
- Language dropdown, per-language boilerplate preserved on switch
- Bottom panel tabs: **Testcase** (editable custom input) and **Result** (output, expected, runtime, memory)
- **Run** = visible/sample cases only. **Submit** = all cases incl. hidden. Same pipeline, different case set.
- Console area: stdout, stderr, runtime + memory line

**Execution engine** — user code never runs on the host:
- Fresh Docker container per submission, destroyed after
- `--network none`, `--memory`, `--cpus`, hard timeout with SIGKILL, guard against fork bombs and filesystem escapes
- One image per language. Start with Python; add C++ and Java later
- API enqueues, worker executes, result written back; frontend polls or uses websocket

**Judging** — compare actual vs expected per case (exact or whitespace/float-normalized). Verdicts: Accepted / Wrong Answer / TLE / Runtime Error. Store per-case results.

**Solution pages** — toggle Brute Force / Optimized. Each shows syntax-highlighted code, synced line-by-line explanation panel, time/space complexity, Mermaid flowchart. Flowcharts are **hand-authored Mermaid text** stored in DB. Do not attempt auto-generating flowcharts from code.

**Dashboard** — solved count, submission history, basic stats.

## 5. Design goals (from analysis of real LeetCode's complaints)

- Strong, language-normalized hidden test cases (LeetCode users report weak tests and cross-language inconsistencies)
- Predictable, fast execution via the queue (users report slow execution)
- Fresh, owner-controlled problem set
- Possible differentiator later: optional "write your own test cases" mode

## 6. Problem set

Full list goes in as problems (statement + editor + judge). Owner may add more later.

**Flagship (2 per topic = 20) get full notes + dual solutions + flowcharts.** All others are basic entries.

| Topic | Flagship pair |
|---|---|
| Array | Two Sum, Maximum Subarray |
| Binary | Number of 1 Bits, Counting Bits |
| Dynamic Programming | Climbing Stairs, Coin Change |
| Graph | Number of Islands, Course Schedule |
| Interval | Insert Interval, Merge Intervals |
| Linked List | Reverse a Linked List, Merge Two Sorted Lists |
| Matrix | Set Matrix Zeroes, Rotate Image |
| String | Valid Parentheses, Longest Substring Without Repeating Characters |
| Tree | Maximum Depth of Binary Tree, Validate Binary Search Tree |
| Heap | Top K Frequent Elements, Find Median from Data Stream |

**Complete problem list by topic (LeetCode slugs):**

- **Array:** two-sum, best-time-to-buy-and-sell-stock, contains-duplicate, product-of-array-except-self, maximum-subarray, maximum-product-subarray, find-minimum-in-rotated-sorted-array, search-in-rotated-sorted-array, 3sum, container-with-most-water
- **Binary:** sum-of-two-integers, number-of-1-bits, counting-bits, missing-number, reverse-bits
- **Dynamic Programming:** climbing-stairs, coin-change, longest-increasing-subsequence, longest-common-subsequence, word-break, combination-sum-iv, house-robber, house-robber-ii, decode-ways, unique-paths, jump-game
- **Graph:** clone-graph, course-schedule, pacific-atlantic-water-flow, number-of-islands, longest-consecutive-sequence, alien-dictionary (premium), graph-valid-tree (premium), number-of-connected-components-in-an-undirected-graph (premium)
- **Interval:** insert-interval, merge-intervals, non-overlapping-intervals, meeting-rooms (premium), meeting-rooms-ii (premium)
- **Linked List:** reverse-linked-list, linked-list-cycle, merge-two-sorted-lists, merge-k-sorted-lists, remove-nth-node-from-end-of-list, reorder-list
- **Matrix:** set-matrix-zeroes, spiral-matrix, rotate-image, word-search
- **String:** longest-substring-without-repeating-characters, longest-repeating-character-replacement, minimum-window-substring, valid-anagram, group-anagrams, valid-parentheses, valid-palindrome, longest-palindromic-substring, palindromic-substrings, encode-and-decode-strings (premium)
- **Tree:** maximum-depth-of-binary-tree, same-tree, invert-binary-tree, binary-tree-maximum-path-sum, binary-tree-level-order-traversal, serialize-and-deserialize-binary-tree, subtree-of-another-tree, construct-binary-tree-from-preorder-and-inorder-traversal, validate-binary-search-tree, kth-smallest-element-in-a-bst, lowest-common-ancestor-of-a-binary-search-tree, implement-trie-prefix-tree, design-add-and-search-words-data-structure, word-search-ii
- **Heap:** merge-k-sorted-lists, top-k-frequent-elements, find-median-from-data-stream

Notes: merge-k-sorted-lists appears under both Linked List and Heap (store once, link from both or assign a primary topic). Premium problems have no public statement, so write original statements for them.

Problem statements and test cases should be written originally by us, not copied from LeetCode.

## 7. Implementation plan

**Phase 1 — Foundation**
1. PostgreSQL schema (all tables above)
2. FastAPI auth (signup/login, JWT)
3. CRUD for topics and problems
4. Seed 10 topics + the 20 flagship problems (description, examples, test cases)

**Phase 2 — Execution engine** (riskiest, do early)
5. Python Docker sandbox: run, capture stdout/stderr, enforce time/memory limits, kill container
6. Redis + Celery/RQ async queue
7. Judging logic, verdicts, store per-case results

**Phase 3 — Editor & frontend core**
8. Monaco split-pane layout
9. Language selector with per-language boilerplate
10. Bottom panel, Run vs Submit wired to the pipeline
11. Result/console panel

**Phase 4 — Topics & notes**
12. Topic overview page rendering markdown notes + problem list
13. Write notes for 2–3 topics first (Array, Binary, DP) to validate the format
14. Notes for all 10 topics

**Phase 5 — Solution pages**
15. Solution page layout (code + synced explanation + complexity)
16. Mermaid.js rendering
17. Author brute force + optimized for 3–5 flagship problems first to lock the template
18. All 20 flagship solutions

**Phase 6 — Expand & harden**
19. Remaining problems as basic entries
20. C++ and Java images
21. Sandbox security pass (verify network none, limits, timeout + SIGKILL, fork-bomb handling)
22. User dashboard

Validate end-to-end on **one topic (Array)** before replicating the pattern to the rest.

## 8. Working conventions

- The biggest time sink is **content authoring** (notes for 10 topics, dual solutions + flowcharts for 20 problems), not code. Treat content as data files (markdown/JSON seed files) so it's easy to edit and re-seed.
- When modifying an existing file the owner provided, write the result to a **new filename** rather than overwriting.
- Prefer small, runnable increments. Get each phase working with curl/Postman before building UI on top.
- Use docker-compose for Postgres + Redis + API + worker so the whole stack starts with one command.

## 9. First prompt to give Claude Code

> Read CLAUDE.md. Start Phase 1: scaffold the FastAPI project with docker-compose (Postgres + Redis), create the SQLAlchemy models and Alembic migration for the schema in section 3, implement JWT auth, and add CRUD endpoints for topics and problems. Then seed the 10 topics and the 20 flagship problems with at least 3 visible and 5 hidden test cases each for the first 4 (Two Sum, Maximum Subarray, Number of 1 Bits, Counting Bits). Show me the project tree and how to run it.
