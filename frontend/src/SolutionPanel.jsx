import Editor from "@monaco-editor/react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "./api.js";
import MermaidDiagram from "./Mermaid.jsx";
import { usePrefersDark } from "./theme.js";

const APPROACH_LABELS = { brute_force: "Brute force", optimized: "Optimized" };
const LINE_HEIGHT = 20;

const markdownComponents = {
  // ```mermaid blocks become diagrams; other code blocks render as usual.
  pre: ({ node, children }) => {
    const code = node?.children?.[0];
    const classes = code?.properties?.className ?? [];
    if (code?.tagName === "code" && classes.includes("language-mermaid")) {
      return <MermaidDiagram chart={code.children.map((child) => child.value ?? "").join("")} />;
    }
    return <pre>{children}</pre>;
  },
  table: ({ children }) => (
    <div className="table-scroll">
      <table>{children}</table>
    </div>
  ),
};

export function Markdown({ children }) {
  return (
    <div className="markdown guide-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {children}
      </ReactMarkdown>
    </div>
  );
}

const lineLabel = ({ start, end }) => (start === end ? `Line ${start}` : `Lines ${start}–${end}`);

/** Read-only code with its line-by-line notes. Hovering or focusing a note highlights its lines, and
 * clicking a code line selects the note that covers it. */
function CodeWithNotes({ code, notes }) {
  const dark = usePrefersDark();
  const [active, setActive] = useState(null);
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const decorationsRef = useRef(null);
  const lineCount = code.replace(/\n$/, "").split("\n").length;

  useEffect(() => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco) return;
    const note = active === null ? null : notes[active];
    decorationsRef.current?.clear();
    decorationsRef.current = editor.createDecorationsCollection(
      note
        ? [{ range: new monaco.Range(note.start, 1, note.end, 1), options: { isWholeLine: true, className: "code-line-highlight" } }]
        : [],
    );
    if (note) editor.revealLinesInCenterIfOutsideViewport(note.start, note.end);
  }, [active, notes]);

  const handleMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    editor.onDidChangeCursorPosition(({ position }) => {
      const index = notes.findIndex((note) => note.start <= position.lineNumber && position.lineNumber <= note.end);
      if (index !== -1) setActive(index);
    });
  };

  return (
    <div className="code-with-notes">
      <div className="solution-code" style={{ height: lineCount * LINE_HEIGHT + 16 }}>
        <Editor
          language="python"
          value={code.replace(/\n$/, "")}
          theme={dark ? "vs-dark" : "light"}
          onMount={handleMount}
          options={{
            readOnly: true,
            domReadOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineHeight: LINE_HEIGHT,
            fontSize: 13,
            renderLineHighlight: "none",
            folding: false,
            contextmenu: false,
            scrollbar: { vertical: "hidden", alwaysConsumeMouseWheel: false },
            padding: { top: 8, bottom: 8 },
            automaticLayout: true,
          }}
        />
      </div>
      <ol className="line-notes" aria-label="Line by line explanation">
        {notes.map((note, index) => (
          <li key={index}>
            <button
              type="button"
              className={`line-note ${index === active ? "active" : ""}`}
              aria-pressed={index === active}
              onMouseEnter={() => setActive(index)}
              onFocus={() => setActive(index)}
              onClick={() => setActive(index)}
            >
              <span className="line-ref">{lineLabel(note)}</span>
              <span className="line-text">
                <ReactMarkdown components={{ p: ({ children }) => <>{children}</> }}>{note.note}</ReactMarkdown>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function Approach({ approach }) {
  return (
    <section className="approach" aria-label={approach.title}>
      <h2>{approach.title}</h2>
      <div className="complexity">
        <span className="chip">Time: {approach.time_complexity}</span>
        <span className="chip">Space: {approach.space_complexity}</span>
      </div>
      <Markdown>{approach.explanation}</Markdown>
      <h3>Code, line by line</h3>
      <p className="muted small">Hover over a note to highlight its lines, or click a line of code to find its note.</p>
      <CodeWithNotes key={approach.approach_type} code={approach.code.python} notes={approach.line_notes} />
      {approach.flowchart_mermaid && (
        <>
          <h3>Flowchart</h3>
          <MermaidDiagram chart={approach.flowchart_mermaid} />
        </>
      )}
    </section>
  );
}

export default function SolutionPanel({ slug }) {
  const [guide, setGuide] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState("thinking");

  useEffect(() => {
    let current = true;
    setGuide(null);
    setSelected("thinking");
    api(`/problems/${slug}/solutions`)
      .then((data) => current && setGuide(data))
      .catch((failure) => current && setError(failure.message));
    return () => {
      current = false;
    };
  }, [slug]);

  if (error) return <p className="error description" role="alert">{error}</p>;
  if (!guide) return <p className="muted description">Loading…</p>;
  if (!guide.thinking && guide.approaches.length === 0) {
    return <p className="muted description">The solution guide for this problem is still being written.</p>;
  }

  const approach = guide.approaches.find((item) => item.approach_type === selected);
  const tabs = [{ id: "thinking", label: "How to think" }, ...guide.approaches.map((item) => ({ id: item.approach_type, label: APPROACH_LABELS[item.approach_type] }))];

  return (
    <div className="description solution-panel">
      <div className="segmented" role="tablist" aria-label="Solution sections">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={selected === tab.id}
            className={selected === tab.id ? "active" : ""}
            onClick={() => setSelected(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {selected === "thinking" ? (
        <>
          <h2>How to think about it</h2>
          <Markdown>{guide.thinking}</Markdown>
          <div className="next-steps">
            {guide.approaches.map((item) => (
              <button key={item.approach_type} className="secondary" onClick={() => setSelected(item.approach_type)}>
                {APPROACH_LABELS[item.approach_type]}: {item.time_complexity} →
              </button>
            ))}
          </div>
        </>
      ) : (
        approach && <Approach approach={approach} />
      )}
    </div>
  );
}
