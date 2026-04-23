import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import Alert from "../components/ui/Alert";
import { useAuth } from "../hooks/useAuth";

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading, signIn, signUp } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  if (!isLoading && isAuthenticated) {
    const destination = location.state?.from || "/dashboard";
    return <Navigate to={destination} replace />;
  }

  async function handleSubmit() {
    if (!email.trim() || !password.trim()) {
      setMessage({ type: "error", text: "Please enter your email and password." });
      return;
    }

    try {
      setSubmitting(true);
      setMessage(null);
      if (mode === "login") {
        await signIn(email.trim(), password);
        navigate("/dashboard", { replace: true });
        return;
      }

      const result = await signUp(email.trim(), password);
      if (!result.session) {
        setMessage({
          type: "success",
          text: "Account created. Check your email to confirm, then sign in."
        });
        setMode("login");
      } else {
        navigate("/dashboard", { replace: true });
      }
    } catch (error) {
      setMessage({ type: "error", text: error.message || "Authentication failed." });
    } finally {
      setSubmitting(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter") {
      handleSubmit();
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card fade-up">
        <div className="auth-logo">
          <div className="auth-logo-icon">AB</div>
          <h1>AutoBook</h1>
          <p>AI Publishing System</p>
        </div>

        <div className="auth-title">{mode === "login" ? "Welcome back" : "Create account"}</div>

        {message ? <Alert type={message.type}>{message.text}</Alert> : null}

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            className="form-input"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="you@example.com"
            disabled={submitting}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Password</label>
          <input
            className="form-input"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={mode === "login" ? "Your password" : "At least 6 characters"}
            disabled={submitting}
          />
        </div>

        <button className="btn btn-gold auth-submit" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>

        <div className="auth-toggle">
          {mode === "login" ? "Do not have an account?" : "Already have an account?"}
          <button
            type="button"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setMessage(null);
            }}
          >
            {mode === "login" ? "Register" : "Sign In"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
