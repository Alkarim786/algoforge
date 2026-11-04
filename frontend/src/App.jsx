import { Check, CheckCircle2, Circle, CircleDot, Moon, Search, Sun } from "lucide-react";
import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { api, fetchMe, getToken, signIn } from "./api.js";
import Home from "./Home.jsx";
import { setThemeChoice, useTheme } from "./theme.js";

const Workspace = lazy(() => import("./Workspace.jsx"));
const TopicPage = lazy(() => import("./TopicPage.jsx"));
const Profile = lazy(() => import("./Profile.jsx"));
const AdminPortal = lazy(() => import("./AdminPortal.jsx"));

export function DifficultyTag({ difficulty }) {
  return <span className={`difficulty ${difficulty.toLowerCase()}`}>{difficulty}</span>;
}

export function useMe() {
  const [me, setMe] = useState(null);
  useEffect(() => {
    let current = true;
    fetchMe()
      .then((user) => current && setMe(user))
      .catch(() => {});
    return () => {
      current = false;
    };
  }, []);
  return me;
}

/** Solved and attempted slugs for the signed-in user; empty when signed out. */
export function useProgress() {
  const [progress, setProgress] = useState({ solved: [], attempted: [] });
  useEffect(() => {
    if (!getToken()) return undefined;
    let current = true;
    api("/me/progress")
      .then((data) => current && setProgress(data))
      .catch(() => {});
    return () => {
      current = false;
    };
  }, []);
  return useMemo(() => ({ solved: new Set(progress.solved), attempted: new Set(progress.attempted) }), [progress]);
}

export function StatusMark({ slug, progress }) {
  if (progress.solved.has(slug)) {
    return <span className="status-mark solved" title="Solved" role="img" aria-label="Solved"><CheckCircle2 size={18} strokeWidth={2.4} /></span>;
  }
  if (progress.attempted.has(slug)) {
    return <span className="status-mark attempted" title="Attempted" role="img" aria-label="Attempted"><CircleDot size={18} strokeWidth={2.4} /></span>;
  }
  return <span className="status-mark" aria-hidden="true"><Circle size={18} strokeWidth={1.8} /></span>;
}

/** The AlgoForge mark: a pair of code brackets. */
export function LogoMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8.5 6 3 12l5.5 6M15.5 6 21 12l-5.5 6" />
      </svg>
    </span>
  );
}

export function Logo({ large = false, to = "/", children }) {
  return (
    <Link to={to} className={large ? "brand large" : "brand"}>
      <LogoMark size={large ? 21 : 18} />
      AlgoForge
      {children}
    </Link>
  );
}

/** Flips between light and dark. The choice is remembered; until then the page follows the system setting. */
export function ThemeToggle() {
  const { dark } = useTheme();
  const label = dark ? "Switch to light mode" : "Switch to dark mode";
  return (
    <button type="button" className="icon-button" onClick={() => setThemeChoice(dark ? "light" : "dark")} aria-label={label} title={label}>
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export function Avatar({ name, size = "small" }) {
  return (
    <span className={`avatar ${size}`} aria-hidden="true">
      {(name ?? "?").slice(0, 1).toUpperCase()}
    </span>
  );
}

export function NavBar({ children }) {
  const me = useMe();
  const location = useLocation();
  const signedIn = Boolean(getToken());
  return (
    <header className="topbar">
      <Logo />
      <nav className="nav-links" aria-label="Main">
        <NavLink to="/" end>{signedIn ? "Dashboard" : "Home"}</NavLink>
        <NavLink to="/problems">Problems</NavLink>
        {me?.role === "admin" && <NavLink to="/admin">Admin</NavLink>}
      </nav>
      {children}
      <div className="nav-right">
        <ThemeToggle />
        {signedIn ? (
          <Link to="/profile" className="profile-link" title="Your profile">
            <Avatar name={me?.username} />
            <span className="profile-name">{me?.username ?? "Profile"}</span>
          </Link>
        ) : (
          <>
            <Link className="link" to="/login" state={{ from: location.pathname }}>Sign in</Link>
            <Link className="button-link" to="/signup" state={{ from: location.pathname }}>Get started</Link>
          </>
        )}
      </div>
    </header>
  );
}

const STATUS_FILTERS = [
  ["all", "All"],
  ["todo", "To do"],
  ["attempted", "Attempted"],
  ["solved", "Solved"],
];

function ProblemList() {
  const [topics, setTopics] = useState(null);
  const [error, setError] = useState(null);
  const [difficulty, setDifficulty] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [query, setQuery] = useState("");
  const progress = useProgress();
  const signedIn = Boolean(getToken());

  useEffect(() => {
    let current = true;
    (async () => {
      const summaries = await api("/topics");
      const details = await Promise.all(summaries.map((topic) => api(`/topics/${topic.slug}`)));
      if (current) setTopics(details);
    })().catch((failure) => current && setError(failure.message));
    return () => {
      current = false;
    };
  }, []);

  const needle = query.trim().toLowerCase();
  const matches = (problem) => {
    if (needle && !problem.title.toLowerCase().includes(needle)) return false;
    if (difficulty !== "all" && problem.difficulty !== difficulty) return false;
    const solved = progress.solved.has(problem.slug);
    const attempted = progress.attempted.has(problem.slug);
    if (statusFilter === "solved") return solved;
    if (statusFilter === "attempted") return attempted;
    if (statusFilter === "todo") return !solved && !attempted;
    return true;
  };

  return (
    <>
      <NavBar />
      <main className="page">
        <div className="toolbar">
          <div>
            <h1>Problems</h1>
            {topics && (
              <p className="muted">
                {topics.reduce((total, topic) => total + topic.problems.length, 0)} problems across {topics.length} topics
                {signedIn && ` · ${progress.solved.size} solved`}
              </p>
            )}
          </div>
          <div className="filters">
            <label className="search">
              <Search size={16} aria-hidden="true" />
              <input type="search" aria-label="Search problems" placeholder="Search problems" value={query} onChange={(event) => setQuery(event.target.value)} />
            </label>
            <select aria-label="Difficulty" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
              <option value="all">All difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
            {signedIn && (
              <select aria-label="Status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                {STATUS_FILTERS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            )}
          </div>
        </div>
        {error && <p className="error" role="alert">{error}</p>}
        {!topics && !error && <p className="muted">Loading…</p>}
        <div className="topic-grid">
          {topics?.map((topic) => {
            const visible = topic.problems.filter(matches);
            if (visible.length === 0) return null;
            return (
              <section key={topic.slug} className="card">
                <h2>
                  <Link to={`/topics/${topic.slug}`} className="topic-link">{topic.name}</Link>
                  <span className="topic-count">
                    {signedIn
                      ? `${topic.problems.filter((problem) => progress.solved.has(problem.slug)).length} / ${topic.problems.length} solved`
                      : `${topic.problems.length} problems`}
                  </span>
                </h2>
                <p className="muted small topic-blurb">
                  {topic.notes_content ? <Link to={`/topics/${topic.slug}`}>Read the notes</Link> : "Notes coming soon"}
                </p>
                <ul className="problem-list">
                  {visible.map((problem) => (
                    <li key={problem.slug}>
                      <StatusMark slug={problem.slug} progress={progress} />
                      <Link to={`/problems/${problem.slug}`}>{problem.title}</Link>
                      <DifficultyTag difficulty={problem.difficulty} />
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
        {topics && topics.every((topic) => topic.problems.filter(matches).length === 0) && (
          <p className="card empty">No problems match these filters.</p>
        )}
      </main>
    </>
  );
}

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const adminPortal = location.pathname === "/admin/login";
  const signingUp = location.pathname === "/signup";
  const [fields, setFields] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const update = (name) => (event) => setFields({ ...fields, [name]: event.target.value });

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (signingUp) await api("/auth/signup", { method: "POST", json: fields });
      const { access_token: token } = await api(`/auth/login?portal=${adminPortal ? "admin" : "student"}`, {
        method: "POST",
        form: { username: fields.username, password: fields.password },
      });
      signIn(token);
      navigate(adminPortal ? "/admin" : location.state?.from || "/", { replace: true });
    } catch (failure) {
      setError(failure.message);
      setBusy(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-intro">
        <Logo large />
        <h1>{adminPortal ? "Run the platform your students learn on." : "Think it through. Prove it against hidden tests."}</h1>
        <p>
          {adminPortal
            ? "The admin console: content, test cases, solution guides and every student's progress."
            : "Learn data structures and algorithms one topic at a time: notes, guided solutions with diagrams, and a real judge."}
        </p>
        <ul className="check-list">
          {(adminPortal
            ? ["Add and edit problems, examples and test cases", "Write solution guides with code, line notes and flowcharts", "Track every student's strengths and weaknesses", "Give other accounts admin access"]
            : ["10 topics with notes and worked examples", "Step-by-step solutions, from brute force to optimized", "Hidden test cases, just like an interview", "A dashboard that tracks your progress and streak"]
          ).map((item) => (
            <li key={item}><Check size={18} strokeWidth={3} aria-hidden="true" />{item}</li>
          ))}
        </ul>
      </section>
      <div className="auth-main">
        <ThemeToggle />
        <form className="auth-form" onSubmit={submit}>
        {!signingUp && (
          <div className="role-switch" role="tablist" aria-label="Account type">
            <Link role="tab" aria-selected={!adminPortal} className={adminPortal ? "" : "active"} to="/login" state={location.state} replace>
              Student
            </Link>
            <Link role="tab" aria-selected={adminPortal} className={adminPortal ? "active" : ""} to="/admin/login" replace>
              Admin
            </Link>
          </div>
        )}
        <h1>{adminPortal ? "Admin sign in" : signingUp ? "Create your account" : "Welcome back"}</h1>
        <p className="muted small">
          {adminPortal
            ? "For platform admins only. Student accounts can't sign in here."
            : signingUp
              ? "It's free. Your progress is saved to your account."
              : "Sign in to continue where you left off."}
        </p>
        <label htmlFor="username">{signingUp ? "Username" : "Username or email"}</label>
        <input id="username" required autoFocus autoComplete="username" value={fields.username} onChange={update("username")} />
        {signingUp && (
          <>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" required autoComplete="email" value={fields.email} onChange={update("email")} />
          </>
        )}
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          required
          minLength={signingUp ? 8 : undefined}
          autoComplete={signingUp ? "new-password" : "current-password"}
          value={fields.password}
          onChange={update("password")}
        />
        {signingUp && <p className="hint">At least 8 characters.</p>}
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Please wait…" : signingUp ? "Create account" : adminPortal ? "Sign in as admin" : "Sign in"}
        </button>
        {adminPortal ? (
          <p className="small muted switch-auth">Admin accounts are created by another admin, or with the create_admin command.</p>
        ) : (
          <p className="small muted switch-auth">
            {signingUp ? "Already have an account? " : "New here? "}
            <Link to={signingUp ? "/login" : "/signup"} state={location.state} replace>
              {signingUp ? "Sign in" : "Create an account"}
            </Link>
          </p>
        )}
        </form>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<p className="muted page">Loading…</p>}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/problems" element={<ProblemList />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Login />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/topics/:slug" element={<TopicPage />} />
          <Route path="/problems/:slug" element={<Workspace />} />
          <Route path="/admin/login" element={<Login />} />
          <Route path="/admin/*" element={<AdminPortal />} />
          <Route
            path="*"
            element={
              <>
                <NavBar />
                <main className="page">
                  <h1>Page not found</h1>
                  <p className="muted">That page doesn't exist. It may have moved.</p>
                  <p><Link className="button-link" to="/">Back home</Link></p>
                </main>
              </>
            }
          />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
