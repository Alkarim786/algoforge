import { Laptop, LogOut, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api, getToken, signOut } from "./api.js";
import { Avatar, NavBar } from "./App.jsx";
import { setThemeChoice, useTheme } from "./theme.js";
import { FieldError, useFieldErrors } from "./validation.jsx";

const formatDate = (value) => new Date(value).toLocaleDateString(undefined, { dateStyle: "long" });

function AppearanceCard() {
  const { choice } = useTheme();
  const options = [
    ["light", "Light", Sun],
    ["dark", "Dark", Moon],
    ["system", "System", Laptop],
  ];
  return (
    <section className="card stack-form">
      <h2>Appearance</h2>
      <p className="muted small">System follows your device's light or dark setting.</p>
      <div className="theme-options" role="group" aria-label="Theme">
        {options.map(([value, label, Icon]) => (
          <button key={value} type="button" className="theme-option" aria-pressed={choice === value} onClick={() => setThemeChoice(value)}>
            <Icon size={20} aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}

function PasswordForm() {
  const [fields, setFields] = useState({ current_password: "", new_password: "", confirm: "" });
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const { errors, validate, clear, fieldProps } = useFieldErrors();
  const ids = { current_password: "current-password", new_password: "new-password", confirm: "confirm-password" };
  const update = (name) => (event) => {
    setFields({ ...fields, [name]: event.target.value });
    clear(ids[name]);
  };

  const submit = async (event) => {
    event.preventDefault();
    setMessage(null);
    if (!validate(event.currentTarget)) return;
    if (fields.new_password !== fields.confirm) {
      setMessage({ ok: false, text: "The two new passwords don't match. Type the same password in both boxes." });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      await api("/auth/change-password", {
        method: "POST",
        json: { current_password: fields.current_password, new_password: fields.new_password },
      });
      setFields({ current_password: "", new_password: "", confirm: "" });
      setMessage({ ok: true, text: "Password updated." });
    } catch (failure) {
      setMessage({ ok: false, text: failure.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card stack-form" onSubmit={submit} noValidate>
      <h2>Change password</h2>
      <label htmlFor="current-password">Current password</label>
      <input id="current-password" type="password" required autoComplete="current-password" data-required-message="Enter your current password." value={fields.current_password} onChange={update("current_password")} {...fieldProps("current-password")} />
      <FieldError id="current-password" message={errors["current-password"]} />
      <label htmlFor="new-password">New password</label>
      <input id="new-password" type="password" required minLength={8} autoComplete="new-password" data-required-message="Choose a new password." value={fields.new_password} onChange={update("new_password")} {...fieldProps("new-password")} />
      <FieldError id="new-password" message={errors["new-password"]} />
      <label htmlFor="confirm-password">Confirm new password</label>
      <input id="confirm-password" type="password" required autoComplete="new-password" data-required-message="Type the new password again." value={fields.confirm} onChange={update("confirm")} {...fieldProps("confirm-password")} />
      <FieldError id="confirm-password" message={errors["confirm-password"]} />
      {message && (
        <p className={message.ok ? "ok" : "error"} role={message.ok ? "status" : "alert"}>{message.text}</p>
      )}
      <button type="submit" disabled={busy}>{busy ? "Saving…" : "Update password"}</button>
    </form>
  );
}

export default function Profile() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!getToken()) return undefined;
    let current = true;
    api("/me/dashboard")
      .then((body) => current && setData(body))
      .catch((failure) => {
        if (!current) return;
        if (failure.status === 401) {
          signOut();
          navigate("/login", { replace: true, state: { from: "/profile" } });
        } else setError(failure.message);
      });
    return () => {
      current = false;
    };
  }, [navigate]);

  if (!getToken()) return <Navigate to="/login" replace state={{ from: "/profile" }} />;

  return (
    <>
      <NavBar />
      <main className="page profile-page">
        {error && <p className="error" role="alert">{error}</p>}
        {!data && !error && <p className="muted">Loading…</p>}
        {data && (
          <>
            <section className="card profile-card">
              <Avatar name={data.user.username} size="large" />
              <div>
                <h1>{data.user.username}</h1>
                <p className="muted">{data.user.email}</p>
                <p className="muted small">Member since {formatDate(data.user.created_at)}</p>
              </div>
            </section>

            <div className="stats">
              <div className="card stat">
                <div className="stat-value">{data.solved}</div>
                <div className="muted small">Problems solved</div>
              </div>
              <div className="card stat">
                <div className="stat-value">{data.current_streak}</div>
                <div className="muted small">Day streak (longest {data.longest_streak})</div>
              </div>
              <div className="card stat">
                <div className="stat-value">{data.submissions}</div>
                <div className="muted small">Submissions</div>
              </div>
              <div className="card stat">
                <div className="stat-value">{data.strengths.length}</div>
                <div className="muted small">Strong topics</div>
              </div>
            </div>

            <div className="profile-grid">
              <PasswordForm />
              <AppearanceCard />
              <section className="card stack-form">
                <h2>Account</h2>
                <p className="muted small">Your progress is saved to your account and shown on your <Link to="/">dashboard</Link>.</p>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    signOut();
                    navigate("/", { replace: true });
                  }}
                >
                  <LogOut size={16} aria-hidden="true" />
                  Sign out
                </button>
              </section>
            </div>
          </>
        )}
      </main>
    </>
  );
}
