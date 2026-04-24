import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import Alert from "../ui/Alert";

function AuthModal({ forceOpen = false, standalone = false }) {
  const navigate = useNavigate();
  const {
    authModalOpen,
    authIntent,
    closeAuthModal,
    isAuthenticated,
    signIn,
    signUp,
    resetPassword
  } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [helperLoading, setHelperLoading] = useState("");
  const [message, setMessage] = useState(null);

  const isOpen = forceOpen || authModalOpen;

  useEffect(() => {
    if (isAuthenticated && standalone) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate, standalone]);

  if (!isOpen) {
    return null;
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
        if (standalone) {
          navigate("/dashboard", { replace: true });
        }
        return;
      }

      const result = await signUp(email.trim(), password);
      if (!result.session) {
        setMessage({
          type: "success",
          text: "Account created. Check your email to confirm the account, then sign in."
        });
        setMode("login");
      } else if (standalone) {
        navigate("/dashboard", { replace: true });
      }
    } catch (error) {
      const errorText =
        error.message === "Invalid login credentials"
          ? "Invalid login credentials. If the password still looks correct, use the reset password option below."
          : error.message || "Authentication failed.";
      setMessage({ type: "error", text: errorText });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResetPassword() {
    if (!email.trim()) {
      setMessage({ type: "error", text: "Enter your email first, then request a password reset." });
      return;
    }

    try {
      setHelperLoading("reset");
      setMessage(null);
      await resetPassword(email.trim());
      setMessage({
        type: "success",
        text: "Password reset email sent. Use that link to set a fresh password."
      });
    } catch (error) {
      setMessage({ type: "error", text: error.message || "Unable to send reset email." });
    } finally {
      setHelperLoading("");
    }
  }

  function handleClose() {
    setMessage(null);
    if (standalone) {
      navigate("/dashboard", { replace: true });
      return;
    }
    closeAuthModal();
  }

  return (
    <div className={`auth-modal-overlay ${standalone ? "auth-modal-overlay-standalone" : ""}`}>
      <div className="auth-card fade-up auth-modal-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">AB</div>
          <h1>AutoBook</h1>
          <p>AI Publishing System</p>
        </div>

        <div className="auth-modal-header">
          <div className="auth-title">{mode === "login" ? "Sign in to continue" : "Create account"}</div>
          {!standalone ? (
            <button type="button" className="btn btn-ghost btn-sm" onClick={handleClose}>
              Close
            </button>
          ) : null}
        </div>

        {authIntent ? <div className="helper-text">{authIntent}</div> : null}
        {message ? <Alert type={message.type}>{message.text}</Alert> : null}

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            className="form-input"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
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
            placeholder={mode === "login" ? "Your password" : "At least 6 characters"}
            disabled={submitting}
          />
        </div>

        <button className="btn btn-gold auth-submit" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>

        <div className="inline-actions mt-16">
          <button type="button" className="btn btn-ghost" onClick={handleResetPassword} disabled={submitting}>
            {helperLoading === "reset" ? "Sending..." : "Reset Password"}
          </button>
        </div>

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

export default AuthModal;
