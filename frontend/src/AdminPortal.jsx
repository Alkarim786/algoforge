import { Suspense, lazy, useEffect, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { api, fetchMe, getToken, signOut } from "./api.js";
import { Avatar, Logo, ThemeToggle } from "./App.jsx";

const ProblemTable = lazy(() => import("./AdminContent.jsx").then((module) => ({ default: module.ProblemTable })));
const ProblemEditor = lazy(() => import("./AdminContent.jsx").then((module) => ({ default: module.ProblemEditor })));

const percent = (rate) => (rate === null ? "–" : `${Math.round(rate * 100)}%`);
const formatDate = (value) => (value ? new Date(value).toLocaleDateString(undefined, { dateStyle: "medium" }) : "–");

const CLASSIFICATION_LABELS = {
  strength: "Strength",
  developing: "Developing",
  weakness: "Weakness",
  not_attempted: "Not attempted",
};

/** GETs an admin endpoint (nothing when `path` is null). A rejected or expired session sends the admin back to
 * the admin sign-in. */
export function useAdminData(path, refresh = 0) {
  const navigate = useNavigate();
  const [state, setState] = useState({ data: null, error: null, loading: Boolean(path) });
  useEffect(() => {
    if (!path) {
      setState({ data: null, error: null, loading: false });
      return undefined;
    }
    let current = true;
    setState((previous) => ({ ...previous, loading: true }));
    api(path)
      .then((data) => current && setState({ data, error: null, loading: false }))
      .catch((failure) => {
        if (!current) return;
        if (failure.status === 401 || failure.status === 403) {
          signOut();
          navigate("/admin/login", { replace: true });
        } else setState({ data: null, error: failure.message, loading: false });
      });
    return () => {
      current = false;
    };
  }, [path, refresh, navigate]);
  return state;
}

const ROLE_FILTERS = [
  ["student", "Students"],
  ["admin", "Admins"],
  ["", "Everyone"],
];

function UserList() {
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("student");
  useEffect(() => {
    const timer = setTimeout(() => setSearch(input.trim()), 250);
    return () => clearTimeout(timer);
  }, [input]);

  const { data, error, loading } = useAdminData(
    `/admin/users?limit=200&role=${role}&search=${encodeURIComponent(search)}`.replace("role=&", ""),
  );
  const noun = role === "admin" ? "admin" : role === "student" ? "student" : "account";

  return (
    <>
      <div className="toolbar">
        <div>
          <h1>Student progress</h1>
          {data && (
            <p className="muted">
              {data.total_users} {data.total_users === 1 ? noun : `${noun}s`} · {data.total_problems} problems on the platform
            </p>
          )}
        </div>
        <div className="filters">
          <select aria-label="Account type" value={role} onChange={(event) => setRole(event.target.value)}>
            {ROLE_FILTERS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <input aria-label="Search users" type="search" placeholder="Search username or email" value={input} onChange={(e) => setInput(e.target.value)} />
        </div>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {loading && !data && <p className="muted">Loading…</p>}
      {data && data.users.length === 0 && <p className="card empty">No accounts match.</p>}
      {data && data.users.length > 0 && (
        <div className="card table-scroll">
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th className="num">Solved</th>
                <th className="num">Attempted</th>
                <th className="num">Submissions</th>
                <th className="num">Acceptance</th>
                <th>Last active</th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <Link className="link" to={`/admin/users/${user.id}`}>{user.username}</Link>
                    {user.role === "admin" && <span className="tag admin-tag">Admin</span>}
                    <div className="muted small">{user.email}</div>
                  </td>
                  <td className="num">{user.solved} / {data.total_problems}</td>
                  <td className="num">{user.attempted}</td>
                  <td className="num">{user.submissions}</td>
                  <td className="num">{percent(user.acceptance_rate)}</td>
                  <td>{formatDate(user.last_active)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Stat({ label, value }) {
  return (
    <div className="card stat">
      <div className="stat-value">{value}</div>
      <div className="muted small">{label}</div>
    </div>
  );
}

function TagGroup({ title, kind, names, emptyText }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      {names.length === 0 ? (
        <p className="muted small">{emptyText}</p>
      ) : (
        <ul className="tags">
          {names.map((name) => <li key={name} className={`tag ${kind}`}>{name}</li>)}
        </ul>
      )}
    </section>
  );
}

function Bar({ value, kind }) {
  return (
    <div className="bar" aria-hidden="true">
      <div className={`bar-fill ${kind}`} style={{ width: `${value}%` }} />
    </div>
  );
}

function RoleControl({ user, me, onChanged }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const isAdmin = user.role === "admin";
  if (user.id === me.id) return <p className="muted small">This is your account.</p>;

  const change = async () => {
    const question = isAdmin
      ? `Remove admin access from ${user.username}? They will become a student.`
      : `Give ${user.username} admin access? They will be able to edit content and see every student's progress.`;
    if (!window.confirm(question)) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/admin/users/${user.id}/role`, { method: "PATCH", json: { role: isAdmin ? "student" : "admin" } });
      onChanged();
    } catch (failure) {
      setError(failure.message);
    }
    setBusy(false);
  };

  return (
    <div className="role-control">
      <button type="button" className="secondary" disabled={busy} onClick={change}>
        {isAdmin ? "Remove admin access" : "Make admin"}
      </button>
      {error && <p className="error" role="alert">{error}</p>}
    </div>
  );
}

function UserEvaluation({ me }) {
  const { userId } = useParams();
  const [refresh, setRefresh] = useState(0);
  const { data, error, loading } = useAdminData(`/admin/users/${userId}/evaluation`, refresh);

  return (
    <>
      <Link className="link back" to="/admin">← All students</Link>
      {error && <p className="error" role="alert">{error}</p>}
      {loading && !data && <p className="muted">Loading…</p>}
      {data && (
        <>
          <div className="toolbar">
            <div>
              <h1>
                {data.user.username}
                {data.user.role === "admin" && <span className="tag admin-tag">Admin</span>}
              </h1>
              <p className="muted">{data.user.email} · joined {formatDate(data.user.created_at)}</p>
            </div>
            <RoleControl user={data.user} me={me} onChanged={() => setRefresh((count) => count + 1)} />
          </div>

          <div className="stats">
            <Stat label="Problems solved" value={`${data.solved} / ${data.total_problems}`} />
            <Stat label="Problems attempted" value={data.attempted} />
            <Stat label="Submissions" value={data.submissions} />
            <Stat label="Acceptance rate" value={percent(data.acceptance_rate)} />
          </div>

          <div className="columns">
            <TagGroup title="Strengths" kind="strength" names={data.strengths} emptyText="No topic has reached a score of 70 yet." />
            <TagGroup title="Weaknesses" kind="weakness" names={data.weaknesses} emptyText="No attempted topic is below a score of 40." />
            <TagGroup title="Not attempted" kind="not_attempted" names={data.not_attempted} emptyText="Every topic has been attempted." />
          </div>

          <section className="card">
            <h2>Topics</h2>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Topic</th>
                    <th>Score</th>
                    <th>Assessment</th>
                    <th className="num">Solved</th>
                    <th className="num">Submissions</th>
                    <th>Most common failure</th>
                  </tr>
                </thead>
                <tbody>
                  {data.topics.map((topic) => (
                    <tr key={topic.slug}>
                      <td>{topic.name}</td>
                      <td className="score-cell">
                        <span className="score">{topic.classification === "not_attempted" ? "–" : topic.score}</span>
                        <Bar value={topic.score} kind={topic.classification} />
                      </td>
                      <td><span className={`tag ${topic.classification}`}>{CLASSIFICATION_LABELS[topic.classification]}</span></td>
                      <td className="num">{topic.solved} / {topic.total}</td>
                      <td className="num">{topic.submissions}</td>
                      <td>{topic.top_failure ?? "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="muted small">
              Score = 70% difficulty-weighted problems solved + 30% solves per submission. 70 or above is a strength; below 40 is a weakness.
            </p>
          </section>

          <div className="columns two">
            <section className="card">
              <h2>By difficulty</h2>
              {data.difficulty.map((row) => (
                <div key={row.difficulty} className="difficulty-row">
                  <div className="difficulty-label">
                    <span>{row.difficulty}</span>
                    <span className="muted">{row.solved} / {row.total}</span>
                  </div>
                  <Bar value={row.total ? (100 * row.solved) / row.total : 0} kind="neutral" />
                </div>
              ))}
            </section>
            <section className="card">
              <h2>Recent submissions</h2>
              {data.recent_submissions.length === 0 ? (
                <p className="muted small">No submissions yet.</p>
              ) : (
                <ul className="recent">
                  {data.recent_submissions.map((submission) => (
                    <li key={submission.id}>
                      <Link to={`/admin/problems/${submission.slug}`}>{submission.title}</Link>
                      <span className={submission.status === "Accepted" ? "ok small" : "bad small"}>{submission.status}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}

function NotAdmin({ me }) {
  const navigate = useNavigate();
  return (
    <main className="center">
      <section className="card key-form">
        <h1>Admins only</h1>
        <p className="muted">
          You're signed in as <strong>{me.username}</strong>, which is a student account. Sign in with an admin account to use the admin console.
        </p>
        <button
          type="button"
          className="primary"
          onClick={() => {
            signOut();
            navigate("/admin/login", { replace: true });
          }}
        >
          Switch to an admin account
        </button>
        <Link to="/">Back to your dashboard</Link>
      </section>
    </main>
  );
}

export default function AdminPortal() {
  const navigate = useNavigate();
  const [me, setMe] = useState(undefined);
  useEffect(() => {
    let current = true;
    fetchMe()
      .then((user) => current && setMe(user))
      .catch(() => current && setMe(null));
    return () => {
      current = false;
    };
  }, []);

  if (!getToken() || me === null) return <Navigate to="/admin/login" replace />;
  if (me === undefined) return <p className="muted page">Loading…</p>;
  if (me.role !== "admin") return <NotAdmin me={me} />;

  return (
    <>
      <header className="topbar admin-bar">
        <Logo to="/admin"><span className="admin-badge">Admin</span></Logo>
        <nav className="nav-links" aria-label="Admin">
          <NavLink to="/admin" end>Students</NavLink>
          <NavLink to="/admin/problems">Problems</NavLink>
        </nav>
        <div className="nav-right">
          <Link to="/" className="link small">View site</Link>
          <ThemeToggle />
          <span className="profile-link">
            <Avatar name={me.username} />
            <span className="profile-name">{me.username}</span>
          </span>
          <button
            type="button"
            className="link"
            onClick={() => {
              signOut();
              navigate("/admin/login", { replace: true });
            }}
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="page admin-page">
        <Suspense fallback={<p className="muted">Loading…</p>}>
          <Routes>
            <Route index element={<UserList />} />
            <Route path="users/:userId" element={<UserEvaluation me={me} />} />
            <Route path="problems" element={<ProblemTable />} />
            <Route path="problems/new" element={<ProblemEditor />} />
            <Route path="problems/:slug" element={<ProblemEditor />} />
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </Routes>
        </Suspense>
      </main>
    </>
  );
}
