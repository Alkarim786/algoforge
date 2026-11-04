import "./monaco.js";
import Editor from "@monaco-editor/react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { ApiError, api, getToken, signOut } from "./api.js";
import { DifficultyTag, NavBar } from "./App.jsx";
import SolutionPanel from "./SolutionPanel.jsx";
import { usePrefersDark } from "./theme.js";

const LANGUAGES = [
  { id: "python", label: "Python 3", available: true },
  { id: "cpp", label: "C++ (coming soon)", available: false },
  { id: "java", label: "Java (coming soon)", available: false },
];
const POLL_INTERVAL_MS = 600;
const POLL_TIMEOUT_MS = 180_000;
const FAILING = new Set(["Wrong Answer", "TLE", "Runtime Error", "System Error"]);

const codeKey = (slug, language) => `algoforge-code:${slug}:${language}`;

function readStored(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Without storage, code is only kept until the page reloads.
  }
}

/** A draggable divider. `onResize` receives the pointer position as a 0–100 share of the container. */
function Divider({ orientation, containerRef, value, onResize }) {
  const horizontal = orientation === "vertical";
  const handlePointerDown = (event) => {
    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const handlePointerMove = (event) => {
    if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
    const rect = containerRef.current.getBoundingClientRect();
    const share = horizontal ? (event.clientX - rect.left) / rect.width : (event.clientY - rect.top) / rect.height;
    onResize(share * 100);
  };
  const handleKeyDown = (event) => {
    const step = { ArrowLeft: -2, ArrowUp: -2, ArrowRight: 2, ArrowDown: 2 }[event.key];
    if (step) {
      event.preventDefault();
      onResize(value + step);
    }
  };
  return (
    <div
      className={`divider ${orientation}`}
      role="separator"
      aria-orientation={orientation}
      aria-valuenow={Math.round(value)}
      tabIndex={0}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onKeyDown={handleKeyDown}
    />
  );
}

function Description({ problem }) {
  return (
    <div className="description">
      <h1>{problem.title}</h1>
      <div className="problem-meta">
        <DifficultyTag difficulty={problem.difficulty} />
        <Link className="small" to={`/topics/${problem.topic_slug}`}>Topic notes</Link>
      </div>
      <div className="markdown">
        <ReactMarkdown>{problem.description}</ReactMarkdown>
      </div>
      {problem.examples.map((example, index) => (
        <div key={index} className="example">
          <h3>Example {index + 1}</h3>
          <pre>
            <strong>Input:</strong> {example.input}
            {"\n"}
            <strong>Output:</strong> {example.output}
            {example.explanation && (
              <>
                {"\n"}
                <strong>Explanation:</strong> {example.explanation}
              </>
            )}
          </pre>
        </div>
      ))}
      {problem.constraints && (
        <>
          <h3>Constraints</h3>
          <div className="markdown">
            <ReactMarkdown>{problem.constraints}</ReactMarkdown>
          </div>
        </>
      )}
    </div>
  );
}

function CaseTabs({ count, active, onSelect, labelFor, statusFor }) {
  return (
    <div className="case-tabs" role="tablist">
      {Array.from({ length: count }, (_, index) => (
        <button
          key={index}
          role="tab"
          aria-selected={index === active}
          className={`case-tab ${index === active ? "active" : ""} ${statusFor?.(index) ?? ""}`}
          onClick={() => onSelect(index)}
        >
          {labelFor(index)}
        </button>
      ))}
    </div>
  );
}

function OutputBlock({ label, text, tone }) {
  if (text === null || text === undefined || text === "") return null;
  return (
    <div className="output-block">
      <div className="output-label">{label}</div>
      <pre className={tone}>{text}</pre>
    </div>
  );
}

function CaseDetail({ result }) {
  return (
    <>
      <OutputBlock label="Input" text={result.input} />
      <OutputBlock label="Output" text={result.actual_output || (result.verdict === "Runtime Error" ? null : "(no answer returned)")} />
      <OutputBlock label="Expected" text={result.expected_output} />
      <OutputBlock label="Stdout" text={result.stdout} />
      <OutputBlock label="Error" text={result.stderr} tone="bad" />
    </>
  );
}

function ResultPanel({ submission, running, error }) {
  const [active, setActive] = useState(0);
  useEffect(() => setActive(0), [submission?.id]);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (running) return <p className="muted">{running === "submit" ? "Judging against all test cases…" : "Running…"}</p>;
  if (!submission) return <p className="muted">Run your code to see results here.</p>;

  const { results, status, mode } = submission;
  const passed = results.filter((result) => result.passed).length;
  const statusClass = FAILING.has(status) ? "bad" : "ok";
  const maxRuntime = Math.max(0, ...results.map((result) => result.runtime_ms ?? 0));
  const maxMemory = Math.max(0, ...results.map((result) => result.memory_kb ?? 0));

  const header = (
    <div className="result-header">
      <span className={`result-status ${statusClass}`}>{status}</span>
      {results.length > 0 && (
        <span className="muted small">
          {passed} / {results.length} {mode === "submit" ? "test cases passed" : "cases"} · {maxRuntime} ms · {(maxMemory / 1024).toFixed(1)} MB
        </span>
      )}
    </div>
  );

  if (status === "System Error") {
    return (
      <>
        {header}
        <p className="muted">Something went wrong on our side. This doesn't count against you; please try again.</p>
      </>
    );
  }

  if (mode === "submit") {
    const failure = results.find((result) => !result.passed);
    return (
      <>
        {header}
        {!failure && status === "Accepted" && <p className="ok">All test cases passed.</p>}
        {failure && failure.is_hidden && (
          <p className="muted">Failed on a hidden test case ({failure.verdict}). Hidden inputs aren't shown.</p>
        )}
        {failure && !failure.is_hidden && <CaseDetail result={failure} />}
        {!failure && status !== "Accepted" && (
          <p className="muted">The program was stopped before producing results.</p>
        )}
      </>
    );
  }

  const current = results[Math.min(active, results.length - 1)];
  return (
    <>
      {header}
      {results.length > 0 && (
        <CaseTabs
          count={results.length}
          active={active}
          onSelect={setActive}
          labelFor={(index) => `Case ${index + 1}`}
          statusFor={(index) => (FAILING.has(results[index].verdict) ? "failed" : "passed")}
        />
      )}
      {current && <CaseDetail result={current} />}
      {current?.verdict === "Finished" && (
        <p className="muted small">This input isn't one of the sample cases, so there's no expected output to compare against.</p>
      )}
    </>
  );
}

export default function Workspace() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const prefersDark = usePrefersDark();

  const [problem, setProblem] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [cases, setCases] = useState([]);
  const [defaultCases, setDefaultCases] = useState([]);
  const [activeCase, setActiveCase] = useState(0);
  const [bottomTab, setBottomTab] = useState("testcase");
  const [leftTab, setLeftTab] = useState("description");
  const [running, setRunning] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [runError, setRunError] = useState(null);
  const [leftWidth, setLeftWidth] = useState(42);
  const [bottomHeight, setBottomHeight] = useState(38);

  const splitRef = useRef(null);
  const rightRef = useRef(null);
  const mounted = useRef(true);
  const runRef = useRef(null);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  useEffect(() => {
    let current = true;
    setProblem(null);
    setSubmission(null);
    setLeftTab("description");
    api(`/problems/${slug}`)
      .then((data) => {
        if (!current) return;
        // Sample cases when the problem has them; otherwise the examples are the best starting point.
        const inputs = data.sample_test_cases.length
          ? data.sample_test_cases.map((sample) => sample.input)
          : data.examples.map((example) => example.input);
        setProblem(data);
        setCases(inputs);
        setDefaultCases(inputs);
        setActiveCase(0);
        setCode(readStored(codeKey(slug, "python")) ?? data.starter_code.python);
      })
      .catch((failure) => current && setLoadError(failure.message));
    return () => {
      current = false;
    };
  }, [slug]);

  const changeCode = (value) => {
    setCode(value ?? "");
    writeStored(codeKey(slug, language), value ?? "");
  };

  const changeLanguage = (next) => {
    // Each language keeps its own code, so switching back restores it.
    setLanguage(next);
    setCode(readStored(codeKey(slug, next)) ?? problem.starter_code[next] ?? "");
  };

  const resetCode = () => {
    if (!window.confirm("Replace your code with the starter code?")) return;
    changeCode(problem.starter_code[language] ?? "");
  };

  const execute = useCallback(
    async (mode) => {
      if (running) return;
      if (!getToken()) {
        navigate("/login", { state: { from: location.pathname } });
        return;
      }
      setRunning(mode);
      setRunError(null);
      setBottomTab("result");
      const edited = cases.length !== defaultCases.length || cases.some((text, index) => text !== defaultCases[index]);
      const payload = { problem_slug: slug, language, code, mode };
      // The examples stand in when a problem has no stored cases, so they go up as custom inputs too.
      if (mode === "run" && (edited || problem.sample_test_cases.length === 0)) {
        payload.custom_inputs = cases.filter((text) => text.trim());
      }
      try {
        const { id } = await api("/submissions", { method: "POST", json: payload });
        const started = Date.now();
        let latest;
        do {
          await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
          if (!mounted.current) return;
          latest = await api(`/submissions/${id}`);
        } while (["pending", "running"].includes(latest.status) && Date.now() - started < POLL_TIMEOUT_MS);
        if (["pending", "running"].includes(latest.status)) throw new Error("The judge is taking too long. Try again in a moment.");
        if (mounted.current) setSubmission(latest);
      } catch (failure) {
        if (!mounted.current) return;
        if (failure instanceof ApiError && failure.status === 401) {
          signOut();
          navigate("/login", { state: { from: location.pathname } });
          return;
        }
        setRunError(failure.message);
      } finally {
        if (mounted.current) setRunning(null);
      }
    },
    [running, cases, defaultCases, slug, language, code, problem, navigate, location.pathname],
  );
  runRef.current = execute;

  const handleEditorMount = (editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => runRef.current("run"));
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, () => runRef.current("submit"));
  };

  if (loadError) {
    return (
      <>
        <NavBar />
        <main className="page"><p className="error" role="alert">{loadError}</p></main>
      </>
    );
  }
  if (!problem) {
    return (
      <>
        <NavBar />
        <main className="page"><p className="muted">Loading…</p></main>
      </>
    );
  }

  const clamp = (value) => Math.min(75, Math.max(20, value));
  const editCase = (value) => setCases(cases.map((text, index) => (index === activeCase ? value : text)));

  return (
    <div className="workspace-page">
      <NavBar>
        <div className="actions">
          <button className="secondary" onClick={() => execute("run")} disabled={Boolean(running)} title="Run (Ctrl+Enter)">
            {running === "run" ? "Running…" : "Run"}
          </button>
          <button
            className="primary"
            onClick={() => execute("submit")}
            disabled={Boolean(running) || !problem.can_submit}
            title={problem.can_submit ? "Submit (Ctrl+Shift+Enter)" : "Hidden test cases for this problem aren't written yet"}
          >
            {running === "submit" ? "Judging…" : "Submit"}
          </button>
        </div>
      </NavBar>
      <div className="workspace" ref={splitRef} style={{ "--left": `${leftWidth}%` }}>
        <section className="pane left-pane" aria-label="Problem">
          <div className="panel-tabs left-tabs" role="tablist">
            {[["description", "Description"], ["solution", "Solution"]].map(([id, label]) => (
              <button key={id} role="tab" aria-selected={leftTab === id} className={leftTab === id ? "active" : ""} onClick={() => setLeftTab(id)}>
                {label}
              </button>
            ))}
          </div>
          {leftTab === "description" ? <Description problem={problem} /> : <SolutionPanel slug={slug} />}
        </section>
        <Divider orientation="vertical" containerRef={splitRef} value={leftWidth} onResize={(v) => setLeftWidth(clamp(v))} />
        <section className="pane right-pane" ref={rightRef} style={{ "--bottom": `${bottomHeight}%` }}>
          <div className="editor-toolbar">
            <select aria-label="Language" value={language} onChange={(event) => changeLanguage(event.target.value)}>
              {LANGUAGES.map((option) => (
                <option key={option.id} value={option.id} disabled={!option.available}>{option.label}</option>
              ))}
            </select>
            <button className="link small" onClick={resetCode}>Reset code</button>
          </div>
          <div className="editor">
            <Editor
              language={language}
              value={code}
              onChange={changeCode}
              onMount={handleEditorMount}
              theme={prefersDark ? "vs-dark" : "light"}
              options={{ fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false, tabSize: 4, automaticLayout: true }}
            />
          </div>
          <Divider
            orientation="horizontal"
            containerRef={rightRef}
            value={100 - bottomHeight}
            onResize={(v) => setBottomHeight(clamp(100 - v))}
          />
          <div className="bottom-panel">
            <div className="panel-tabs" role="tablist">
              <button role="tab" aria-selected={bottomTab === "testcase"} className={bottomTab === "testcase" ? "active" : ""} onClick={() => setBottomTab("testcase")}>
                Testcase
              </button>
              <button role="tab" aria-selected={bottomTab === "result"} className={bottomTab === "result" ? "active" : ""} onClick={() => setBottomTab("result")}>
                Result
              </button>
            </div>
            <div className="panel-body">
              {bottomTab === "testcase" ? (
                <>
                  <div className="case-row">
                    <CaseTabs count={cases.length} active={activeCase} onSelect={setActiveCase} labelFor={(index) => `Case ${index + 1}`} />
                    {cases.length < 10 && (
                      <button
                        className="link small"
                        onClick={() => {
                          setCases([...cases, cases[activeCase] ?? ""]);
                          setActiveCase(cases.length);
                        }}
                      >
                        + Add case
                      </button>
                    )}
                    {cases.length > 1 && (
                      <button
                        className="link small"
                        onClick={() => {
                          setCases(cases.filter((_, index) => index !== activeCase));
                          setActiveCase(Math.max(0, activeCase - 1));
                        }}
                      >
                        Remove
                      </button>
                    )}
                    <button
                      className="link small"
                      onClick={() => {
                        setCases(defaultCases);
                        setActiveCase(0);
                      }}
                    >
                      Reset cases
                    </button>
                  </div>
                  <label className="muted small" htmlFor="case-input">One argument per line, written as JSON</label>
                  <textarea
                    id="case-input"
                    spellCheck={false}
                    value={cases[activeCase] ?? ""}
                    onChange={(event) => editCase(event.target.value)}
                  />
                </>
              ) : (
                <ResultPanel submission={submission} running={running} error={runError} />
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
