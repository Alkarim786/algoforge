import { ArrowRight, BookOpen, CheckCircle2, Flame, LineChart, Lightbulb, ShieldCheck, Sparkles, Target, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ActivityChart from "./ActivityChart.jsx";
import { api, getToken, signOut } from "./api.js";
import { Avatar, DifficultyTag, Logo, NavBar } from "./App.jsx";

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

// The landing page's sample solution, as [text, token class] pairs per line.
const SAMPLE = [
  [["class", "kw"], [" "], ["Solution", "ty"], [":"]],
  [["    "], ["def", "kw"], [" "], ["twoSum", "fn"], ["(self, nums: "], ["List", "ty"], ["[int], target: "], ["int", "ty"], [") -> "], ["List", "ty"], ["[int]:"]],
  [["        "], ["# value -> index of the numbers seen so far", "cm"]],
  [["        seen = {}"]],
  [["        "], ["for", "kw"], [" i, x "], ["in", "kw"], [" "], ["enumerate", "fn"], ["(nums):"]],
  [["            "], ["if", "kw"], [" target - x "], ["in", "kw"], [" seen:"]],
  [["                "], ["return", "kw"], [" [seen[target - x], i]"]],
  [["            seen[x] = i"]],
];

const FEATURES = [
  [BookOpen, "Topic notes", "Concepts, built-in functions, pitfalls and a worked example for every topic, with diagrams."],
  [Lightbulb, "Learn how to think", "Every problem walks from brute force to optimized, with dry runs, line notes and flowcharts."],
  [ShieldCheck, "A real judge", "Each test case runs in its own locked-down container, hidden and stress cases included."],
  [LineChart, "Your progress", "Streaks, topic strengths and weaknesses, and a clear next problem every time you sign in."],
];

function CodeCard() {
  return (
    <div className="code-card">
      <div className="code-card-head">
        <span className="dot" style={{ background: "var(--red-bar)" }} />
        <span className="dot" style={{ background: "var(--amber-bar)" }} />
        <span className="dot" style={{ background: "var(--green-bar)" }} />
        <span className="file">two_sum.py</span>
        <span style={{ marginLeft: "auto" }}><DifficultyTag difficulty="Easy" /></span>
      </div>
      <pre aria-label="A sample Two Sum solution">
        {SAMPLE.map((parts, index) => (
          <span className="code-line" key={index}>
            <span className="ln">{index + 1}</span>
            {parts.map(([text, kind], part) => (
              <span key={part} className={kind ? `tk-${kind}` : undefined}>{text}</span>
            ))}
          </span>
        ))}
      </pre>
      <div className="code-card-foot">
        <span className="verdict"><CheckCircle2 size={20} strokeWidth={2.6} aria-hidden="true" />Accepted</span>
        <span className="muted">8 / 8 test cases passed · 41 ms · 12.4 MB</span>
      </div>
    </div>
  );
}

function Landing() {
  const topics = useTopics();
  const problemCount = topics?.reduce((total, topic) => total + topic.problems.length, 0);

  return (
    <>
      <NavBar />
      <main className="landing">
        <section className="hero">
          <span className="eyebrow"><span className="eyebrow-badge">Free</span>Notes, guided solutions and a real judge</span>
          <h1>
            Master data structures &amp; algorithms, <span className="accent">one topic at a time.</span>
          </h1>
          <p className="hero-sub">
            Read the notes, learn how to think about each problem, then prove your solution against hidden test cases in a
            sandboxed judge.
          </p>
          <div className="hero-actions">
            <Link className="button-link large" to="/signup">Start learning <ArrowRight size={18} aria-hidden="true" /></Link>
            <Link className="button-link secondary large" to="/problems">Browse problems</Link>
          </div>
          <ul className="hero-stats">
            <li><strong>{problemCount ?? 75}</strong><span>Problems</span></li>
            <li><strong>{topics?.length || 10}</strong><span>Topics</span></li>
            <li><strong>{(problemCount ?? 75) * 2}</strong><span>Guided solutions</span></li>
            <li><strong>Python</strong><span>Language</span></li>
          </ul>
          <div className="hero-visual">
            <CodeCard />
          </div>
        </section>

        <section className="section" aria-labelledby="features-title">
          <div className="section-head">
            <h2 id="features-title">Everything a study guide needs</h2>
            <p>One place to learn the idea, see it worked through, and practice until it sticks.</p>
          </div>
          <div className="features">
            {FEATURES.map(([Icon, title, body]) => (
              <article key={title} className="card feature">
                <span className="feature-icon"><Icon size={22} aria-hidden="true" /></span>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        {topics && topics.length > 0 && (
          <section className="section" aria-labelledby="path-title">
            <div className="section-head">
              <h2 id="path-title">The study path</h2>
              <p>Ten topics in order. Each one builds on the ones before it.</p>
            </div>
            <ol className="path-list">
              {topics.map((topic, index) => (
                <li key={topic.slug} className="card">
                  <Link to={`/topics/${topic.slug}`}>
                    <span className="path-number">{index + 1}</span>
                    <span>
                      <strong>{topic.name}</strong>
                      <span className="muted small" style={{ display: "block" }}>{topic.problems.length} problems</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ol>
          </section>
        )}

        <section className="section" aria-labelledby="how-title">
          <div className="section-head">
            <h2 id="how-title">How it works</h2>
          </div>
          <div className="steps">
            {[
              ["Read", "Start a topic with its notes: the idea, the built-in functions you'll use, and a worked example."],
              ["Think", "Open a problem's guide to see how to approach it, from the brute force to the optimized solution."],
              ["Prove", "Write your solution, run it on the samples, then submit it against the hidden test cases."],
            ].map(([title, body], index) => (
              <div key={title} className="card step">
                <span className="step-number">STEP 0{index + 1}</span>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            ))}
          </div>
          <div className="cta-band">
            <div>
              <h2>Ready for your first problem?</h2>
              <p>It's free. Your progress, streak and strengths are saved to your account.</p>
            </div>
            <Link className="button-link large" to="/signup">Create your account <ArrowRight size={18} aria-hidden="true" /></Link>
          </div>
        </section>

        <footer className="site-footer">
          <Logo />
          <span>Built with FastAPI, PostgreSQL, Redis, Docker and React.</span>
        </footer>
      </main>
    </>
  );
}

function StatTile({ icon: Icon, tone, label, value, detail }) {
  return (
    <div className="card stat">
      <span className={`stat-icon ${tone ?? ""}`}><Icon size={20} aria-hidden="true" /></span>
      <div className="stat-value">{value}</div>
      <div className="muted small" style={{ fontWeight: 700 }}>{label}</div>
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
      <span className="muted">{title}</span>
      <strong>{problem.title}</strong>
      <span className="small next-meta">
        {problem.topic_name} <DifficultyTag difficulty={problem.difficulty} />
      </span>
      <span className="next-action">{action} <ArrowRight size={16} aria-hidden="true" /></span>
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

  return (
    <>
      <NavBar />
      <main className="page dashboard">
        <section className="dash-header">
          <div className="dash-profile">
            <Avatar name={data.user.username} size="large" />
            <div>
              <h1>Welcome back, {data.user.username}</h1>
              <p className="streak">
                <Flame size={16} strokeWidth={2.4} aria-hidden="true" />
                {data.current_streak > 0 ? `${data.current_streak}-day streak` : "Start a streak today"}
                <span className="muted">· member since {formatDate(data.user.created_at)}</span>
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
          <StatTile icon={Trophy} label="Problems solved" value={`${data.solved} / ${data.total_problems}`} detail={`${solvedShare}% of the study path`} />
          <StatTile icon={Flame} tone="amber" label="Day streak" value={data.current_streak} detail={`Longest: ${data.longest_streak}`} />
          <StatTile icon={Target} tone="teal" label="Acceptance rate" value={percent(data.acceptance_rate)} detail={`${data.submissions} submissions`} />
          <StatTile icon={Sparkles} tone="green" label="Strong topics" value={data.strengths.length} detail={data.strengths.slice(0, 3).join(", ") || "Solve a few to build one"} />
        </div>

        <div className="dash-grid">
          <section className="card" aria-labelledby="path-title">
            <h2 id="path-title">Study path</h2>
            <ol className="path-progress">
              {data.topics.map((topic, index) => (
                <li key={topic.slug}>
                  <div className="path-row">
                    <span className="path-number">{index + 1}</span>
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
              <h2>Strengths and weaknesses</h2>
              <h3 className="muted">Strong topics</h3>
              {data.strengths.length ? (
                <ul className="tags">{data.strengths.map((name) => <li key={name} className="tag strength">{name}</li>)}</ul>
              ) : (
                <p className="muted small">Solve a few problems in a topic to build a strength.</p>
              )}
              <h3 className="muted">Needs work</h3>
              {data.weaknesses.length ? (
                <ul className="tags">{data.weaknesses.map((name) => <li key={name} className="tag weakness">{name}</li>)}</ul>
              ) : (
                <p className="muted small">Nothing flagged yet.</p>
              )}
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
                      <span className={`tag ${submission.status === "Accepted" ? "strength" : "weakness"}`}>{submission.status}</span>
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
