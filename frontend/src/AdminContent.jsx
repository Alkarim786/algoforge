import { EDITOR_FONT, defineEditorThemes, editorTheme } from "./monaco.js";
import Editor from "@monaco-editor/react";
import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useAdminData } from "./AdminPortal.jsx";
import { api } from "./api.js";
import { DifficultyTag } from "./App.jsx";
import MermaidDiagram from "./Mermaid.jsx";
import { Approach, Markdown } from "./SolutionPanel.jsx";
import { usePrefersDark } from "./theme.js";

const APPROACHES = [
  ["brute_force", "Brute force"],
  ["optimized", "Optimized"],
];

const slugify = (text) =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);

const caseCount = (row) => row.visible_cases + row.hidden_cases;

/** What still stops a problem from being complete, in the order an admin would fix it. */
function missingParts(row) {
  const missing = [];
  if (row.visible_cases === 0) missing.push("visible cases");
  if (row.hidden_cases === 0) missing.push("hidden cases");
  if (!row.has_thinking) missing.push("how to think");
  if (row.solutions < 2) missing.push(`${2 - row.solutions} solution${row.solutions === 1 ? "" : "s"}`);
  return missing;
}

export function ProblemTable() {
  const { data, error, loading } = useAdminData("/admin/problems");
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState("");
  const [onlyIncomplete, setOnlyIncomplete] = useState(false);

  const topics = useMemo(() => {
    const seen = new Map();
    data?.forEach((row) => seen.set(row.topic_slug, row.topic_name));
    return [...seen];
  }, [data]);
  const needle = query.trim().toLowerCase();
  const rows = (data ?? []).filter(
    (row) =>
      (!topic || row.topic_slug === topic) &&
      (!needle || row.title.toLowerCase().includes(needle) || row.slug.includes(needle)) &&
      (!onlyIncomplete || missingParts(row).length > 0),
  );

  return (
    <>
      <div className="toolbar">
        <div>
          <h1>Problems</h1>
          {data && (
            <p className="muted">
              {data.length} problems · {data.filter((row) => missingParts(row).length === 0).length} complete with tests and a full guide
            </p>
          )}
        </div>
        <Link className="button-link" to="/admin/problems/new">+ New problem</Link>
      </div>
      <div className="filters admin-filters">
        <input aria-label="Search problems" type="search" placeholder="Search title or slug" value={query} onChange={(e) => setQuery(e.target.value)} />
        <select aria-label="Topic" value={topic} onChange={(event) => setTopic(event.target.value)}>
          <option value="">All topics</option>
          {topics.map(([slug, name]) => <option key={slug} value={slug}>{name}</option>)}
        </select>
        <label className="check">
          <input type="checkbox" checked={onlyIncomplete} onChange={(event) => setOnlyIncomplete(event.target.checked)} />
          Only incomplete
        </label>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {loading && !data && <p className="muted">Loading…</p>}
      {data && rows.length === 0 && <p className="card empty">No problems match.</p>}
      {rows.length > 0 && (
        <div className="card table-scroll">
          <table>
            <thead>
              <tr>
                <th>Problem</th>
                <th>Topic</th>
                <th>Difficulty</th>
                <th className="num">Test cases</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const missing = missingParts(row);
                return (
                  <tr key={row.id}>
                    <td>
                      <Link className="link" to={`/admin/problems/${row.slug}`}>{row.title}</Link>
                      {row.is_flagship && <span className="tag flagship-tag">Flagship</span>}
                      <div className="muted small">{row.slug}</div>
                    </td>
                    <td>{row.topic_name}</td>
                    <td><DifficultyTag difficulty={row.difficulty} /></td>
                    <td className="num" title={`${row.visible_cases} visible, ${row.hidden_cases} hidden`}>
                      {caseCount(row)} <span className="muted small">({row.hidden_cases} hidden)</span>
                    </td>
                    <td>
                      {missing.length === 0 ? (
                        <span className="tag strength">Complete</span>
                      ) : (
                        <span className="tag developing" title={`Missing: ${missing.join(", ")}`}>Needs {missing[0]}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

/** A markdown textarea with a Write / Preview switch. */
function MarkdownField({ id, label, value, onChange, rows = 8, hint }) {
  const [preview, setPreview] = useState(false);
  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor={id}>{label}</label>
        <div className="segmented small-tabs" role="tablist" aria-label={`${label} view`}>
          <button type="button" role="tab" aria-selected={!preview} className={preview ? "" : "active"} onClick={() => setPreview(false)}>Write</button>
          <button type="button" role="tab" aria-selected={preview} className={preview ? "active" : ""} onClick={() => setPreview(true)}>Preview</button>
        </div>
      </div>
      {preview ? (
        <div className="preview-box">{value.trim() ? <Markdown>{value}</Markdown> : <p className="muted small">Nothing to preview yet.</p>}</div>
      ) : (
        <textarea id={id} rows={rows} value={value} onChange={(event) => onChange(event.target.value)} />
      )}
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}

const ENTRY_TEMPLATES = {
  Function: {
    method: "solve",
    params: [
      { name: "nums", type: "List[int]" },
      { name: "target", type: "int" },
    ],
    returns: "int",
  },
  "Design class": {
    class: "Counter",
    operations: {
      add: { method: "add", params: [{ name: "value", type: "int" }], returns: "None" },
      total: { method: "total", returns: "int" },
    },
  },
};

const shownType = (type) => type.replace("TreeNodeRef", "TreeNode");
const signature = (method, returns) => {
  const params = (method.params ?? []).map((param) => `, ${param.name}: ${shownType(param.type)}`).join("");
  return [`    def ${method.method}(self${params})${returns ? ` -> ${shownType(returns)}` : ""}:`, "        pass"];
};

/** The starter code students will see; mirrors drivers.starter_code on the server. */
function starterCode(entry) {
  if (!entry) return "# Read the test case from stdin and print the answer.";
  if (entry.codec) {
    const valueType = entry.params[0].type;
    return [
      `class ${entry.codec}:`,
      ...signature({ method: entry.encode, params: entry.params }, "str"),
      "",
      ...signature({ method: entry.decode, params: [{ name: "data", type: "str" }] }, valueType),
    ].join("\n");
  }
  if (entry.class) {
    const lines = [`class ${entry.class}:`, "    def __init__(self):", "        pass"];
    Object.values(entry.operations ?? {}).forEach((operation) => lines.push("", ...signature(operation, operation.returns)));
    return lines.join("\n");
  }
  return ["class Solution:", ...signature(entry, entry.returns)].join("\n");
}

function parseEntry(text) {
  if (!text.trim()) return { entry: null };
  try {
    const entry = JSON.parse(text);
    starterCode(entry);
    return { entry };
  } catch (failure) {
    return { error: failure.message };
  }
}

function EntryField({ value, onChange }) {
  const parsed = parseEntry(value);
  return (
    <div className="field">
      <div className="field-head">
        <label htmlFor="entry">How the code is called (JSON)</label>
        <div className="template-buttons">
          {Object.entries(ENTRY_TEMPLATES).map(([name, template]) => (
            <button key={name} type="button" className="secondary small-button" onClick={() => onChange(JSON.stringify(template, null, 2))}>
              {name} template
            </button>
          ))}
        </div>
      </div>
      <div className="entry-grid">
        <textarea id="entry" className="code-input" rows={10} spellCheck={false} value={value} onChange={(event) => onChange(event.target.value)} />
        <div>
          <div className="output-label">Starter code students get</div>
          {parsed.error ? <p className="error small">Not valid JSON yet: {parsed.error}</p> : <pre className="starter-preview">{starterCode(parsed.entry)}</pre>}
        </div>
      </div>
      <p className="hint">
        Types are converted for you: <code>List[int]</code>, <code>Optional[ListNode]</code>, <code>Optional[TreeNode]</code> and so on.
        Use <code>"returns": "None"</code> when the method edits its first argument in place. Leave this empty for a plain stdin/stdout program.
      </p>
    </div>
  );
}

function ExamplesEditor({ examples, onChange }) {
  const update = (index, field, value) => onChange(examples.map((example, i) => (i === index ? { ...example, [field]: value } : example)));
  return (
    <fieldset className="field examples-editor">
      <legend>Examples shown in the statement</legend>
      {examples.length === 0 && <p className="muted small">No examples yet.</p>}
      {examples.map((example, index) => (
        <div key={index} className="example-row card">
          <div className="example-row-head">
            <strong className="small">Example {index + 1}</strong>
            <button type="button" className="link danger-link" onClick={() => onChange(examples.filter((_, i) => i !== index))}>Remove</button>
          </div>
          <div className="two-up">
            <label>
              Input
              <textarea className="code-input" rows={3} value={example.input} onChange={(event) => update(index, "input", event.target.value)} />
            </label>
            <label>
              Output
              <textarea className="code-input" rows={3} value={example.output} onChange={(event) => update(index, "output", event.target.value)} />
            </label>
          </div>
          <label>
            Explanation (optional)
            <input value={example.explanation ?? ""} onChange={(event) => update(index, "explanation", event.target.value)} />
          </label>
        </div>
      ))}
      <button type="button" className="secondary" onClick={() => onChange([...examples, { input: "", output: "", explanation: "" }])}>
        + Add example
      </button>
    </fieldset>
  );
}

function formFrom(problem, topics) {
  return {
    title: problem?.title ?? "",
    slug: problem?.slug ?? "",
    topic_slug: problem?.topic_slug ?? topics?.[0]?.slug ?? "",
    difficulty: problem?.difficulty ?? "Easy",
    order_within_topic: problem?.order_within_topic ?? 0,
    is_flagship: problem?.is_flagship ?? false,
    description: problem?.description ?? "",
    constraints: problem?.constraints ?? "",
    examples: problem?.examples ?? [],
    entryText: problem ? (problem.entry ? JSON.stringify(problem.entry, null, 2) : "") : JSON.stringify(ENTRY_TEMPLATES.Function, null, 2),
  };
}

function DetailsForm({ problem, topics, onSaved }) {
  const navigate = useNavigate();
  const [form, setForm] = useState(() => formFrom(problem, topics));
  const [slugEdited, setSlugEdited] = useState(Boolean(problem));
  const [status, setStatus] = useState({ busy: false, error: null, saved: false });
  const set = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }));
  const setFromEvent = (field) => (event) => set(field)(event.target.value);

  useEffect(() => setForm(formFrom(problem, topics)), [problem, topics]);

  const save = async (event) => {
    event.preventDefault();
    const parsed = parseEntry(form.entryText);
    if (parsed.error) {
      setStatus({ busy: false, error: `"How the code is called" isn't valid JSON: ${parsed.error}`, saved: false });
      return;
    }
    const { entryText, ...fields } = form;
    const payload = {
      ...fields,
      order_within_topic: Number(form.order_within_topic) || 0,
      examples: form.examples.map(({ explanation, ...example }) => (explanation?.trim() ? { ...example, explanation } : example)),
      entry: parsed.entry,
    };
    setStatus({ busy: true, error: null, saved: false });
    try {
      const saved = problem
        ? await api(`/problems/${problem.slug}`, { method: "PATCH", json: payload })
        : await api("/problems", { method: "POST", json: payload });
      setStatus({ busy: false, error: null, saved: true });
      if (!problem || saved.slug !== problem.slug) navigate(`/admin/problems/${saved.slug}`, { replace: true, state: { tab: problem ? "details" : "cases" } });
      else onSaved();
    } catch (failure) {
      setStatus({ busy: false, error: failure.message, saved: false });
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete "${problem.title}" with its test cases and solutions? This can't be undone.`)) return;
    try {
      await api(`/problems/${problem.slug}`, { method: "DELETE" });
      navigate("/admin/problems", { replace: true });
    } catch (failure) {
      setStatus({
        busy: false,
        error: failure.status === 409 ? "Students have submitted code for this problem, so it can't be deleted." : failure.message,
        saved: false,
      });
    }
  };

  return (
    <form className="admin-form" onSubmit={save}>
      <section className="card form-grid">
        <label>
          Title
          <input
            required
            maxLength={200}
            value={form.title}
            onChange={(event) => {
              const title = event.target.value;
              setForm((previous) => ({ ...previous, title, slug: slugEdited ? previous.slug : slugify(title) }));
            }}
          />
        </label>
        <label>
          Slug (the URL)
          <input
            required
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            title="Lowercase letters, digits and single hyphens"
            value={form.slug}
            onChange={(event) => {
              setSlugEdited(true);
              set("slug")(event.target.value);
            }}
          />
        </label>
        <label>
          Topic
          <select value={form.topic_slug} onChange={setFromEvent("topic_slug")}>
            {topics.map((topic) => <option key={topic.slug} value={topic.slug}>{topic.name}</option>)}
          </select>
        </label>
        <label>
          Difficulty
          <select value={form.difficulty} onChange={setFromEvent("difficulty")}>
            {["Easy", "Medium", "Hard"].map((level) => <option key={level}>{level}</option>)}
          </select>
        </label>
        <label>
          Position in topic
          <input type="number" min="0" value={form.order_within_topic} onChange={setFromEvent("order_within_topic")} />
        </label>
        <label className="check">
          <input type="checkbox" checked={form.is_flagship} onChange={(event) => set("is_flagship")(event.target.checked)} />
          Flagship problem
        </label>
      </section>

      <section className="card">
        <MarkdownField id="description" label="Statement (markdown)" value={form.description} onChange={set("description")} rows={10} />
        <MarkdownField id="constraints" label="Constraints (markdown)" value={form.constraints} onChange={set("constraints")} rows={4} />
      </section>

      <section className="card">
        <ExamplesEditor examples={form.examples} onChange={set("examples")} />
      </section>

      <section className="card">
        <EntryField value={form.entryText} onChange={set("entryText")} />
      </section>

      <div className="form-actions">
        <button type="submit" disabled={status.busy}>{status.busy ? "Saving…" : problem ? "Save changes" : "Create problem"}</button>
        {status.saved && <span className="ok small" role="status">Saved.</span>}
        {problem && (
          <button type="button" className="danger" onClick={remove}>Delete problem</button>
        )}
      </div>
      {status.error && <p className="error" role="alert">{status.error}</p>}
    </form>
  );
}

function inputHint(entry) {
  if (!entry) return "Plain text, read from stdin by the student's program.";
  if (entry.class) return `One line: a JSON list of calls, e.g. [["${Object.keys(entry.operations)[0]}", …], …]. Expected output: a list of the values the calls return (calls that return nothing are skipped).`;
  if (entry.codec) return `One line: the ${entry.params[0].name} as JSON. Expected output: the same value, rebuilt by decode(encode(…)).`;
  if (entry.cycle) return "Two lines: the list's values, then the index the tail links back to (-1 for no cycle).";
  return `One JSON value per line, in order: ${entry.params.map((param) => `${param.name} (${shownType(param.type)})`).join(", ")}.`;
}

const preview = (text, limit = 160) => (text.length > limit ? `${text.slice(0, limit)}… (${text.length.toLocaleString()} characters)` : text);

function CaseForm({ problem, initial, onDone, onCancel }) {
  const [fields, setFields] = useState(initial ?? { input: "", expected_output: "", is_hidden: true });
  const [status, setStatus] = useState({ busy: false, error: null });

  const submit = async (event) => {
    event.preventDefault();
    setStatus({ busy: true, error: null });
    try {
      if (initial?.id) await api(`/admin/test-cases/${initial.id}`, { method: "PATCH", json: fields });
      else await api(`/admin/problems/${problem.slug}/test-cases`, { method: "POST", json: fields });
      setStatus({ busy: false, error: null });
      if (!initial) setFields({ input: "", expected_output: "", is_hidden: fields.is_hidden });
      onDone();
    } catch (failure) {
      setStatus({ busy: false, error: failure.message });
    }
  };

  return (
    <form className="card case-form" onSubmit={submit}>
      <h2>{initial?.id ? "Edit test case" : "Add a test case"}</h2>
      <p className="hint">{inputHint(problem.entry)}</p>
      <div className="two-up">
        <label>
          Input
          <textarea className="code-input" required rows={5} spellCheck={false} value={fields.input} onChange={(e) => setFields({ ...fields, input: e.target.value })} />
        </label>
        <label>
          Expected output
          <textarea
            className="code-input"
            required
            rows={5}
            spellCheck={false}
            value={fields.expected_output}
            onChange={(e) => setFields({ ...fields, expected_output: e.target.value })}
          />
        </label>
      </div>
      <label className="check">
        <input type="checkbox" checked={fields.is_hidden} onChange={(e) => setFields({ ...fields, is_hidden: e.target.checked })} />
        Hidden (used on Submit only; students never see it)
      </label>
      <div className="form-actions">
        <button type="submit" disabled={status.busy}>{status.busy ? "Saving…" : initial?.id ? "Save case" : "Add case"}</button>
        {onCancel && <button type="button" className="secondary" onClick={onCancel}>Cancel</button>}
      </div>
      {status.error && <p className="error" role="alert">{status.error}</p>}
    </form>
  );
}

function TestCasesPanel({ problem, onChanged }) {
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState(null);
  const visible = problem.test_cases.filter((item) => !item.is_hidden).length;

  const remove = async (item, index) => {
    if (!window.confirm(`Delete test case ${index + 1}?`)) return;
    try {
      await api(`/admin/test-cases/${item.id}`, { method: "DELETE" });
      onChanged();
    } catch (failure) {
      setError(failure.message);
    }
  };

  return (
    <>
      <p className="muted">
        {visible} visible (used by Run and shown to students) · {problem.test_cases.length - visible} hidden (used by Submit only).
        Inputs and outputs are checked as JSON and saved in compact form.
      </p>
      {error && <p className="error" role="alert">{error}</p>}
      {problem.test_cases.length > 0 && (
        <div className="card table-scroll">
          <table className="cases-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Input</th>
                <th>Expected</th>
                <th>Visibility</th>
                <th><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {problem.test_cases.map((item, index) =>
                editing === item.id ? (
                  <tr key={item.id}>
                    <td colSpan={5}>
                      <CaseForm
                        problem={problem}
                        initial={item}
                        onCancel={() => setEditing(null)}
                        onDone={() => {
                          setEditing(null);
                          onChanged();
                        }}
                      />
                    </td>
                  </tr>
                ) : (
                  <tr key={item.id}>
                    <td className="num">{index + 1}</td>
                    <td><pre className="case-text">{preview(item.input)}</pre></td>
                    <td><pre className="case-text">{preview(item.expected_output)}</pre></td>
                    <td><span className={`tag ${item.is_hidden ? "not_attempted" : "strength"}`}>{item.is_hidden ? "Hidden" : "Visible"}</span></td>
                    <td className="row-actions">
                      <button type="button" className="link" onClick={() => setEditing(item.id)}>Edit</button>
                      <button type="button" className="link danger-link" onClick={() => remove(item, index)}>Delete</button>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
      <CaseForm problem={problem} onDone={onChanged} />
    </>
  );
}

const noteText = (notes) => notes.map((note) => `${note.start === note.end ? note.start : `${note.start}-${note.end}`}: ${note.note}`).join("\n");

function parseNotes(text) {
  const notes = [];
  for (const [index, line] of text.split("\n").entries()) {
    if (!line.trim()) continue;
    const match = line.match(/^\s*(\d+)(?:\s*-\s*(\d+))?\s*[:.)]\s*(.+)$/);
    if (!match) return { error: `Line ${index + 1} should look like "3: note" or "3-5: note".` };
    notes.push({ start: Number(match[1]), end: Number(match[2] ?? match[1]), note: match[3].trim() });
  }
  return { notes };
}

const IN_PROGRESS = new Set(["pending", "running"]);

/** Submits the code like a student would (all cases, hidden ones included) and waits for the verdict. */
async function judgeCode(slug, code) {
  const { id } = await api("/submissions", { method: "POST", json: { problem_slug: slug, language: "python", code, mode: "submit" } });
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    const submission = await api(`/submissions/${id}`);
    if (!IN_PROGRESS.has(submission.status)) return submission;
  }
  throw new Error("The judge is taking too long. Is the worker running?");
}

function JudgeResult({ result }) {
  if (result.error) return <p className="error" role="alert">{result.error}</p>;
  const { submission } = result;
  const passed = submission.results.filter((item) => item.passed).length;
  const failure = submission.results.find((item) => !item.passed);
  return (
    <div className={`judge-result ${submission.status === "Accepted" ? "ok" : "bad"}`} role="status">
      <strong>{submission.status}</strong> · {passed} / {submission.results.length} cases passed
      {failure && (
        <span className="muted small">
          {" "}· first failure: case {submission.results.indexOf(failure) + 1} ({failure.is_hidden ? "hidden" : "visible"}, {failure.verdict ?? "failed"})
        </span>
      )}
    </div>
  );
}

function emptyApproach() {
  return { title: "", time_complexity: "", space_complexity: "", explanation: "", code: "", notesText: "", flowchart_mermaid: "" };
}

function approachForm(existing) {
  if (!existing) return emptyApproach();
  return {
    title: existing.title,
    time_complexity: existing.time_complexity,
    space_complexity: existing.space_complexity,
    explanation: existing.explanation,
    code: existing.code.python ?? "",
    notesText: noteText(existing.line_notes),
    flowchart_mermaid: existing.flowchart_mermaid ?? "",
  };
}

function ApproachEditor({ problem, type, label, existing, onChanged }) {
  const dark = usePrefersDark();
  const [form, setForm] = useState(() => approachForm(existing));
  const [status, setStatus] = useState({ busy: false, error: null, saved: false });
  const [showPreview, setShowPreview] = useState(false);
  const [judging, setJudging] = useState(null);
  const [chart, setChart] = useState(form.flowchart_mermaid);
  const set = (field) => (value) => setForm((previous) => ({ ...previous, [field]: value }));

  useEffect(() => setForm(approachForm(existing)), [existing]);
  useEffect(() => {
    const timer = setTimeout(() => setChart(form.flowchart_mermaid), 400);
    return () => clearTimeout(timer);
  }, [form.flowchart_mermaid]);

  const notes = parseNotes(form.notesText);
  const payload = () => ({
    title: form.title,
    time_complexity: form.time_complexity,
    space_complexity: form.space_complexity,
    explanation: form.explanation,
    code: form.code,
    line_notes: notes.notes ?? [],
    flowchart_mermaid: form.flowchart_mermaid.trim() || null,
  });

  const save = async (event) => {
    event.preventDefault();
    if (notes.error) {
      setStatus({ busy: false, error: notes.error, saved: false });
      return;
    }
    setStatus({ busy: true, error: null, saved: false });
    try {
      await api(`/admin/problems/${problem.slug}/solutions/${type}`, { method: "PUT", json: payload() });
      setStatus({ busy: false, error: null, saved: true });
      onChanged();
    } catch (failure) {
      setStatus({ busy: false, error: failure.message, saved: false });
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete the ${label.toLowerCase()} solution?`)) return;
    try {
      await api(`/admin/problems/${problem.slug}/solutions/${type}`, { method: "DELETE" });
      onChanged();
    } catch (failure) {
      setStatus({ busy: false, error: failure.message, saved: false });
    }
  };

  const judge = async () => {
    setJudging({ running: true });
    try {
      setJudging({ submission: await judgeCode(problem.slug, form.code) });
    } catch (failure) {
      setJudging({ error: failure.message });
    }
  };

  const lineCount = Math.max(form.code.split("\n").length, 8);

  return (
    <form className="card approach-editor" onSubmit={save}>
      <div className="field-head">
        <h2>{label}</h2>
        <span className={`tag ${existing ? "strength" : "not_attempted"}`}>{existing ? "Published" : "Not written yet"}</span>
      </div>
      <div className="form-grid">
        <label className="wide">
          Title
          <input required maxLength={200} placeholder={`${label} — the idea in a few words`} value={form.title} onChange={(e) => set("title")(e.target.value)} />
        </label>
        <label>
          Time complexity
          <input required maxLength={50} placeholder="O(n log n)" value={form.time_complexity} onChange={(e) => set("time_complexity")(e.target.value)} />
        </label>
        <label>
          Space complexity
          <input required maxLength={50} placeholder="O(1)" value={form.space_complexity} onChange={(e) => set("space_complexity")(e.target.value)} />
        </label>
      </div>
      <MarkdownField
        id={`${type}-explanation`}
        label="Idea and dry run (markdown)"
        value={form.explanation}
        onChange={set("explanation")}
        hint="Explain the idea, then trace a small example; a table works well for the dry run."
      />
      <div className="field">
        <label>Python code</label>
        <div className="code-editor-box" style={{ height: Math.min(lineCount * 19 + 16, 480) }}>
          <Editor
            language="python"
            value={form.code}
            theme={editorTheme(dark)}
            beforeMount={defineEditorThemes}
            onChange={(value) => set("code")(value ?? "")}
            options={{ minimap: { enabled: false }, fontSize: 13, fontFamily: EDITOR_FONT, scrollBeyondLastLine: false, automaticLayout: true, tabSize: 4 }}
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor={`${type}-notes`}>Line by line notes</label>
        <textarea
          id={`${type}-notes`}
          className="code-input"
          rows={6}
          spellCheck={false}
          placeholder={"3: What line 3 does.\n5-7: What lines 5 to 7 do."}
          value={form.notesText}
          onChange={(e) => set("notesText")(e.target.value)}
        />
        {notes.error ? <p className="error small">{notes.error}</p> : <p className="hint">One note per line: a line number or range, a colon, then the note (markdown allowed).</p>}
      </div>
      <div className="field">
        <label htmlFor={`${type}-flowchart`}>Flowchart (Mermaid)</label>
        <div className="entry-grid">
          <textarea
            id={`${type}-flowchart`}
            className="code-input"
            rows={10}
            spellCheck={false}
            placeholder={'flowchart TD\n    S(["start"]) --> C{"done?"}\n    C -->|yes| E(["return"])'}
            value={form.flowchart_mermaid}
            onChange={(e) => set("flowchart_mermaid")(e.target.value)}
          />
          <div className="flowchart-preview">{chart.trim() ? <MermaidDiagram chart={chart} /> : <p className="muted small">The diagram preview appears here.</p>}</div>
        </div>
        <p className="hint">Rounded <code>([ ])</code> for start and end, <code>{"{ }"}</code> for decisions and <code>[ ]</code> for steps; the colours follow the shapes.</p>
      </div>
      <div className="form-actions">
        <button type="submit" disabled={status.busy}>{status.busy ? "Saving…" : "Save solution"}</button>
        <button type="button" className="secondary" disabled={!form.code.trim() || judging?.running || problem.test_cases.length === 0} onClick={judge}>
          {judging?.running ? "Judging…" : "Test against all cases"}
        </button>
        <button type="button" className="secondary" onClick={() => setShowPreview((shown) => !shown)}>{showPreview ? "Hide preview" : "Preview as students see it"}</button>
        {status.saved && <span className="ok small" role="status">Saved.</span>}
        {existing && <button type="button" className="danger" onClick={remove}>Delete</button>}
      </div>
      {judging && !judging.running && <JudgeResult result={judging} />}
      {status.error && <p className="error" role="alert">{status.error}</p>}
      {showPreview && (
        <div className="preview-box solution-panel">
          {form.code.trim() ? (
            <Approach approach={{ ...payload(), approach_type: type, code: { python: form.code }, line_notes: notes.notes ?? [] }} />
          ) : (
            <p className="muted small">Add code to preview the solution.</p>
          )}
        </div>
      )}
    </form>
  );
}

function SolutionGuidePanel({ problem, onChanged }) {
  const [thinking, setThinking] = useState(problem.thinking ?? "");
  const [status, setStatus] = useState({ busy: false, error: null, saved: false });
  useEffect(() => setThinking(problem.thinking ?? ""), [problem]);

  const saveThinking = async () => {
    setStatus({ busy: true, error: null, saved: false });
    try {
      await api(`/problems/${problem.slug}`, { method: "PATCH", json: { thinking: thinking.trim() || null } });
      setStatus({ busy: false, error: null, saved: true });
      onChanged();
    } catch (failure) {
      setStatus({ busy: false, error: failure.message, saved: false });
    }
  };

  return (
    <>
      <section className="card">
        <MarkdownField
          id="thinking"
          label="How to think (markdown)"
          value={thinking}
          onChange={setThinking}
          rows={12}
          hint="Restate the problem, the key insight, and the edge cases. ```mermaid blocks render as diagrams."
        />
        <div className="form-actions">
          <button type="button" className="primary" disabled={status.busy} onClick={saveThinking}>{status.busy ? "Saving…" : "Save how to think"}</button>
          {status.saved && <span className="ok small" role="status">Saved.</span>}
        </div>
        {status.error && <p className="error" role="alert">{status.error}</p>}
      </section>
      {APPROACHES.map(([type, label]) => (
        <ApproachEditor
          key={type}
          problem={problem}
          type={type}
          label={label}
          existing={problem.solutions.find((item) => item.approach_type === type)}
          onChanged={onChanged}
        />
      ))}
    </>
  );
}

const TABS = [
  ["details", "Details"],
  ["cases", "Test cases"],
  ["guide", "Solution guide"],
];

export function ProblemEditor() {
  const { slug } = useParams();
  const [refresh, setRefresh] = useState(0);
  const location = useLocation();
  const [tab, setTab] = useState(location.state?.tab ?? "details");
  const topics = useAdminData("/topics");
  const { data: problem, error, loading } = useAdminData(slug ? `/admin/problems/${slug}` : null, refresh);
  const reload = () => setRefresh((count) => count + 1);

  // The same editor instance is reused when /new turns into /:slug, so follow the tab each navigation asks for.
  useEffect(() => setTab(location.state?.tab ?? "details"), [location.key]); // eslint-disable-line react-hooks/exhaustive-deps

  if (error || topics.error) return <p className="error" role="alert">{error || topics.error}</p>;
  // Only the first load shows a placeholder; reloads after a save keep the forms (and their tab) on screen.
  if (!topics.data || (slug && !problem) || (slug && loading && problem.slug !== slug)) return <p className="muted">Loading…</p>;

  const hidden = problem ? problem.test_cases.filter((item) => item.is_hidden).length : 0;
  const counts = { cases: problem ? `${problem.test_cases.length}` : null, guide: problem ? `${problem.solutions.length}/2` : null };

  return (
    <>
      <Link className="link back" to="/admin/problems">← All problems</Link>
      <div className="toolbar">
        <div>
          <h1>{problem ? problem.title : "New problem"}</h1>
          {problem && (
            <p className="muted">
              {problem.topic_slug} · <DifficultyTag difficulty={problem.difficulty} /> · {problem.test_cases.length} test cases ({hidden} hidden) ·{" "}
              <Link to={`/problems/${problem.slug}`} target="_blank" rel="noreferrer">Open as a student ↗</Link>
            </p>
          )}
        </div>
      </div>
      {problem && (
        <div className="segmented editor-tabs" role="tablist" aria-label="Problem sections">
          {TABS.map(([id, label]) => (
            <button key={id} type="button" role="tab" aria-selected={tab === id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>
              {label}
              {counts[id] && <span className="tab-count">{counts[id]}</span>}
            </button>
          ))}
        </div>
      )}
      {(!problem || tab === "details") && <DetailsForm problem={problem} topics={topics.data} onSaved={reload} />}
      {problem && tab === "cases" && <TestCasesPanel problem={problem} onChanged={reload} />}
      {problem && tab === "guide" && <SolutionGuidePanel problem={problem} onChanged={reload} />}
    </>
  );
}
