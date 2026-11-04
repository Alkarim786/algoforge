import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ActivityChart from "./ActivityChart.jsx";
import { api, getToken, signOut } from "./api.js";
import { Avatar, DifficultyTag, NavBar } from "./App.jsx";

const ASSESSMENT = {
  strength: "Strength",
  developing: "Developing",
  weakness: "Needs work",
  not_attempted: "Not started",
};

const formatDate = (value) => new Date(value).toLocaleDateString(undefined, { dateStyle: "medium" });
const percent = (rate) => (rate === null || rate === undefined ? "–" : `${Math.round(rate * 100)}%`);

function useTopics() {
  const [topics, setTopics] = useState(null);
  useEffect(() => {
    let current = true;
    (async () => {
      const summaries = await api("/topics");
      return Promise.all(summaries.map((topic) => api(`/topics/${topic.slug}`)));
    })()
      .then((details) => current && setTopics(details))
      .catch(() => current && setTopics([]));
    return () => {
      current = false;
    };
  }, []);
  return topics;
}

function Landing() {
  const topics = useTopics();
  const problemCount = topics?.reduce((total, topic) => total + topic.problems.length, 0);

  return (
    <>
      <NavBar />
      <main className="landing">
        <section className="hero">
          <h1>Master data structures and algorithms, one topic at a time.</h1>
          <p className="hero-sub">
            A study guide and judge in one place: read the notes, learn how to think about each problem, then prove it
            against hidden test cases.
          </p>
          <div className="hero-actions">
            <Link className="button-link large" to="/signup">Start learning, it's free</Link>
            <Link className="button-link secondary large" to="/login">Sign in</Link>
          </div>
          {topics && (
            <p className="muted small">
              {topics.length} topics · {problemCount} problems · Python
            </p>
          )}
        </section>

        <section className="features" aria-label="What you get">
          {[
            ["Topic notes", "Concepts, complexity tables, built-in functions and pitfalls, with a worked example in every topic."],
            ["Guided solutions", "How to think about each problem, then brute force and optimized approaches with dry runs and flowcharts."],
            ["A real judge", "Run against sample cases, submit against hidden and stress tests, and see runtime and memory."],
            ["Your dashboard", "Solved count, daily streak, topic progress, strengths and weaknesses, and what to do next."],
          ].map(([title, body]) => (
            <article key={title} className="card feature">
              <h2>{title}</h2>
              <p className="muted">{body}</p>
            </article>
          ))}
        </section>

        {topics && topics.length > 0 && (
          <section className="study-path-preview">
            <h2>The study path</h2>
            <p className="muted">Work through the topics in order. Each one builds on the ones before it.</p>
            <ol className="path-list">
              {topics.map((topic, index) => (
                <li key={topic.slug} className="card">
                  <span className="path-number">{index + 1}</span>
                  <div>
                    <Link to={`/topics/${topic.slug}`} className="topic-link"><strong>{topic.name}</strong></Link>
                    <div className="muted small">{topic.problems.length} problems</div>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        )}
      </main>
    </>
  );
}

function StatTile({ label, value, detail }) {
  return (
    <div className="card stat">
      <div className="stat-value">{value}</div>
      <div className="muted small">{label}</div>
      {detail && <div className="muted small">{detail}</div>}
    </div>
  );
}

function ProgressBar({ value, total, label }) {
  const share = total ? (100 * value) / total : 0;
  return (
    <div className="progress" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={total} aria-valuenow={value}>
      <div className="progress-fill" style={{ width: `${share}%` }} />
    </div>
  );
}

function ProblemCard({ title, problem, action }) {
  return (
    <Link to={`/problems/${problem.slug}`} className="card next-card">
      <span className="muted small">{title}</span>
      <strong>{problem.title}</strong>
      <span className="small next-meta">
        {problem.topic_name} · <DifficultyTag difficulty={problem.difficulty} />
      </span>
      <span className="next-action">{action} →</span>
    </Link>
  );
}

function Dashboard({ onSignedOut }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let current = true;
    api("/me/dashboard")
      .then((body) => current && setData(body))
      .catch((failure) => {
        if (!current) return;
        if (failure.status === 401) {
          signOut();
          onSignedOut();
        } else setError(failure.message);
      });
    return () => {
      current = false;
    };
  }, [onSignedOut]);

  if (error || !data) {
    return (
      <>
        <NavBar />
        <main className="page">{error ? <p className="error" role="alert">{error}</p> : <p className="muted">Loading your dashboard…</p>}</main>
      </>
    );
  }

  const solvedShare = data.total_problems ? Math.round((100 * data.solved) / data.total_problems) : 0;
  const firstName = data.user.username;

  return (
    <>
      <NavBar />
      <main className="page dashboard">
        <section className="dash-header">
          <div className="dash-profile">
            <Avatar name={data.user.username} size="large" />
            <div>
              <h1>Welcome back, {firstName}</h1>
              <p className="muted small">
                Member since {formatDate(data.user.created_at)} · <Link to="/profile">Profile</Link>
              </p>
            </div>
          </div>
          <div className="dash-next">
            {data.continue_problem && <ProblemCard title="Continue where you left off" problem={data.continue_problem} action="Resume" />}
            {data.next_problem && <ProblemCard title="Next in your study path" problem={data.next_problem} action="Start" />}
            {!data.continue_problem && !data.next_problem && (
              <div className="card next-card">
                <strong>Every problem attempted</strong>
                <span className="muted small">Revisit a weak topic below, or try a problem again from memory.</span>
              </div>
            )}
          </div>
        </section>

        <div className="stats">
          <StatTile label="Problems solved" value={`${data.solved} / ${data.total_problems}`} detail={`${solvedShare}% of the study path`} />
          <StatTile label="Day streak" value={data.current_streak} detail={`Longest: ${data.longest_streak}`} />
          <StatTile label="Acceptance rate" value={percent(data.acceptance_rate)} detail={`${data.submissions} submissions`} />
          <StatTile label="Attempted, not solved" value={data.attempted - data.solved} />
        </div>

        <div className="dash-grid">
          <section className="card" aria-labelledby="path-title">
            <h2 id="path-title">Study path</h2>
            <ol className="path-progress">
              {data.topics.map((topic, index) => (
                <li key={topic.slug}>
                  <div className="path-row">
                    <span className="path-number small">{index + 1}</span>
                    <Link to={`/topics/${topic.slug}`} className="path-name">{topic.name}</Link>
                    <span className={`tag ${topic.classification}`}>{ASSESSMENT[topic.classification]}</span>
                    <span className="muted small path-count">{topic.solved} / {topic.total}</span>
                  </div>
                  <ProgressBar value={topic.solved} total={topic.total} label={`${topic.name}: ${topic.solved} of ${topic.total} solved`} />
                </li>
              ))}
            </ol>
            <p className="muted small">
              Topic assessment combines how much you've solved (weighted by difficulty) with how many submissions it took.
            </p>
          </section>

          <div className="dash-side">
            <section className="card">
              <h2>Activity</h2>
              <ActivityChart days={data.activity} />
            </section>

            <section className="card">
              <h2>Strengths and weaknesses</h2>
              <h3 className="small muted">Strong topics</h3>
              {data.strengths.length ? (
                <ul className="tags">{data.strengths.map((name) => <li key={name} className="tag strength">{name}</li>)}</ul>
              ) : (
                <p className="muted small">Solve a few problems in a topic to build a strength.</p>
              )}
              <h3 className="small muted">Needs work</h3>
              {data.weaknesses.length ? (
                <ul className="tags">{data.weaknesses.map((name) => <li key={name} className="tag weakness">{name}</li>)}</ul>
              ) : (
                <p className="muted small">Nothing flagged yet.</p>
              )}
            </section>

            <section className="card">
              <h2>By difficulty</h2>
              {data.difficulty.map((row) => (
                <div key={row.difficulty} className="difficulty-row">
                  <div className="difficulty-label">
                    <DifficultyTag difficulty={row.difficulty} />
                    <span className="muted small">{row.solved} / {row.total}</span>
                  </div>
                  <ProgressBar value={row.solved} total={row.total} label={`${row.difficulty}: ${row.solved} of ${row.total} solved`} />
                </div>
              ))}
            </section>

            <section className="card">
              <h2>Recent submissions</h2>
              {data.recent_submissions.length === 0 ? (
                <p className="muted small">No submissions yet. Your first one will show up here.</p>
              ) : (
                <ul className="recent">
                  {data.recent_submissions.map((submission) => (
                    <li key={submission.id}>
                      <Link to={`/problems/${submission.slug}`}>{submission.title}</Link>
                      <span className={submission.status === "Accepted" ? "ok small" : "bad small"}>{submission.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      </main>
    </>
  );
}

export default function Home() {
  const [signedIn, setSignedIn] = useState(() => Boolean(getToken()));
  return signedIn ? <Dashboard onSignedOut={() => setSignedIn(false)} /> : <Landing />;
}
