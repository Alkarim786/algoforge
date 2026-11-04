import { ChevronDown, Search, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { getToken } from "./api.js";
import { DifficultyTag, ProgressRing, StatusMark } from "./App.jsx";

/** The study path as a slide-in panel: every topic with its progress, the current one open, any problem a click away. */
export default function ProblemDrawer({ topics, currentSlug, progress, onClose }) {
  const currentTopic = topics.find((topic) => topic.problems.some((problem) => problem.slug === currentSlug));
  const [open, setOpen] = useState(() => new Set(currentTopic ? [currentTopic.slug] : []));
  const [query, setQuery] = useState("");
  const searchRef = useRef(null);
  const signedIn = Boolean(getToken());

  useEffect(() => {
    searchRef.current?.focus();
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    // Bring the current problem into view inside the panel.
    document.querySelector(".drawer [aria-current='page']")?.scrollIntoView({ block: "center" });
  }, []);

  const needle = query.trim().toLowerCase();
  const total = topics.reduce((sum, topic) => sum + topic.problems.length, 0);
  const toggle = (slug) =>
    setOpen((previous) => {
      const next = new Set(previous);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} aria-hidden="true" />
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
        <div className="drawer-head">
          <div>
            <h2 id="drawer-title">Study path</h2>
            <span className="muted small">
              {signedIn ? `${progress.solved.size} of ${total} solved` : `${total} problems in ${topics.length} topics`}
            </span>
          </div>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close the problem list">
            <X size={18} />
          </button>
        </div>
        <label className="search drawer-search">
          <Search size={16} aria-hidden="true" />
          <input ref={searchRef} type="search" aria-label="Search problems" placeholder="Search problems" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <div className="drawer-body">
          {topics.map((topic, index) => {
            const problems = topic.problems.filter((problem) => !needle || problem.title.toLowerCase().includes(needle));
            if (problems.length === 0) return null;
            const solved = topic.problems.filter((problem) => progress.solved.has(problem.slug)).length;
            const expanded = Boolean(needle) || open.has(topic.slug);
            const listId = `drawer-${topic.slug}`;
            return (
              <section key={topic.slug} className={`drawer-topic ${topic === currentTopic ? "current" : ""}`}>
                <button type="button" className="drawer-topic-head" aria-expanded={expanded} aria-controls={listId} onClick={() => toggle(topic.slug)}>
                  <ProgressRing value={solved} total={topic.problems.length} size={40} label={`${topic.name}: ${solved} of ${topic.problems.length} solved`} />
                  <span className="drawer-topic-name">
                    <strong>{index + 1}. {topic.name}</strong>
                    <span className="muted small">{topic.problems.length} problems</span>
                  </span>
                  <ChevronDown size={18} aria-hidden="true" className="drawer-chevron" />
                </button>
                {expanded && (
                  <ul className="problem-list drawer-problems" id={listId}>
                    {problems.map((problem) => (
                      <li key={problem.slug} className={problem.slug === currentSlug ? "current" : ""}>
                        <StatusMark slug={problem.slug} progress={progress} />
                        <Link to={`/problems/${problem.slug}`} onClick={onClose} aria-current={problem.slug === currentSlug ? "page" : undefined}>
                          {problem.title}
                        </Link>
                        <DifficultyTag difficulty={problem.difficulty} />
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            );
          })}
        </div>
      </aside>
    </>
  );
}
