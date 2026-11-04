import { Children, isValidElement, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";
import remarkGfm from "remark-gfm";
import { api } from "./api.js";
import { DifficultyTag, NavBar, StatusMark, useProgress } from "./App.jsx";
import MermaidDiagram from "./Mermaid.jsx";

function textOf(children) {
  return Children.toArray(children)
    .map((child) => (isValidElement(child) ? textOf(child.props.children) : String(child)))
    .join("");
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

const markdownComponents = {
  h2: ({ children }) => <h2 id={slugify(textOf(children))}>{children}</h2>,
  pre: ({ node, children }) => {
    const code = node?.children?.[0];
    if (code?.tagName === "code" && (code.properties?.className ?? []).includes("language-mermaid")) {
      return <MermaidDiagram chart={code.children.map((child) => child.value ?? "").join("")} />;
    }
    return <pre>{children}</pre>;
  },
  // Wide tables scroll inside their own box instead of widening the page on phones.
  table: ({ children }) => (
    <div className="table-scroll">
      <table>{children}</table>
    </div>
  ),
};

function headingsOf(markdown) {
  return [...markdown.matchAll(/^## (.+)$/gm)].map((match) => {
    const title = match[1].replace(/[`*]/g, "");
    return { title, id: slugify(title) };
  });
}

export default function TopicPage() {
  const { slug } = useParams();
  const [topic, setTopic] = useState(null);
  const [topics, setTopics] = useState([]);
  const [error, setError] = useState(null);
  const progress = useProgress();

  useEffect(() => {
    let current = true;
    setTopic(null);
    setError(null);
    Promise.all([api(`/topics/${slug}`), api("/topics")])
      .then(([detail, all]) => {
        if (!current) return;
        setTopic(detail);
        setTopics(all);
        window.scrollTo(0, 0);
      })
      .catch((failure) => current && setError(failure.message));
    return () => {
      current = false;
    };
  }, [slug]);

  if (error || !topic) {
    return (
      <>
        <NavBar />
        <main className="page">
          {error ? <p className="error" role="alert">{error}</p> : <p className="muted">Loading…</p>}
        </main>
      </>
    );
  }

  const position = topics.findIndex((item) => item.slug === slug);
  const previous = topics[position - 1];
  const next = topics[position + 1];
  const headings = topic.notes_content ? [...headingsOf(topic.notes_content), { title: "Practice problems", id: "practice-problems" }] : [];

  return (
    <>
      <NavBar />
      <main className="page topic-page">
        <div className="topic-layout">
          <article className="notes">
            <p className="muted small">
              <Link to="/">Topics</Link> / Topic {position + 1} of {topics.length}
            </p>
            <h1>{topic.name}</h1>
            {topic.notes_content ? (
              <div className="markdown notes-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                  {topic.notes_content}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="muted">Notes for this topic are on the way. The problems are ready below.</p>
            )}

            <section className="practice" aria-labelledby="practice-problems">
              <h2 id="practice-problems">Practice problems</h2>
              <ol className="problem-list numbered">
                {topic.problems.map((problem) => (
                  <li key={problem.slug}>
                    <StatusMark slug={problem.slug} progress={progress} />
                    <Link to={`/problems/${problem.slug}`}>{problem.title}</Link>
                    <DifficultyTag difficulty={problem.difficulty} />
                  </li>
                ))}
              </ol>
            </section>

            <nav className="topic-nav" aria-label="Other topics">
              {previous ? <Link to={`/topics/${previous.slug}`}>← {previous.name}</Link> : <span />}
              {next && <Link to={`/topics/${next.slug}`}>{next.name} →</Link>}
            </nav>
          </article>

          {headings.length > 0 && (
            <aside className="toc" aria-label="On this page">
              <div className="toc-title">On this page</div>
              <ul>
                {headings.map((heading) => (
                  <li key={heading.id}>
                    <a href={`#${heading.id}`}>{heading.title}</a>
                  </li>
                ))}
              </ul>
            </aside>
          )}
        </div>
      </main>
    </>
  );
}
