import { useState } from "react";
import { Link, navigate } from "../router";
import { authApi } from "../api";

export default function Auth({ mode }) {
  const isSignup = mode === "signup";
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      if (isSignup) {
        await authApi.register(form.email.trim(), form.password, form.name.trim());
      } else {
        await authApi.login(form.email.trim(), form.password);
      }
      // Redirect to Research page upon successful authentication
      navigate("/research");
    } catch (err) {
      setError(err.message || "Authentication failed. Please verify your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth">
      <Link to="/" className="auth-back">
        <span aria-hidden="true">←</span> Back to home
      </Link>

      <div className="auth-brand">
        <img src="/QMIcon.png" alt="QueryMind" />
        <span>QueryMind</span>
      </div>

      <div className="auth-card">
        <h1>{isSignup ? "Create your account" : "Welcome back"}</h1>
        <p className="auth-sub">
          {isSignup
            ? "Start turning questions into cited research reports."
            : "Sign in to access your saved research history."}
        </p>

        <form onSubmit={submit}>
          {error && <div className="auth-error">{error}</div>}

          {isSignup && (
            <div className="field">
              <label htmlFor="name">Full name</label>
              <input
                id="name"
                type="text"
                placeholder="Ada Lovelace"
                value={form.name}
                onChange={set("name")}
                autoComplete="name"
                required
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              type="email"
              placeholder="name@example.com"
              value={form.email}
              onChange={set("email")}
              autoComplete="email"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <div className="input-wrap">
              <input
                id="password"
                type={showPw ? "text" : "password"}
                placeholder={isSignup ? "At least 8 characters" : "Enter password"}
                value={form.password}
                onChange={set("password")}
                autoComplete={isSignup ? "new-password" : "current-password"}
                required
              />
              <button
                type="button"
                className="toggle-pw"
                onClick={() => setShowPw(!showPw)}
                aria-label={showPw ? "Hide password" : "Show password"}
              >
                {showPw ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <button className="btn btn-block" type="submit" disabled={loading}>
            {loading ? "Please wait…" : isSignup ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          {isSignup ? (
            <>Already have an account? <Link to="/signin">Sign in</Link></>
          ) : (
            <>New to QueryMind? <Link to="/signup">Create account</Link></>
          )}
        </p>
      </div>

      <p className="auth-foot">Ask. Research. Understand.</p>
    </div>
  );
}