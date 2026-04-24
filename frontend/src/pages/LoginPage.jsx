import { Navigate } from "react-router-dom";

import AuthModal from "../components/auth/AuthModal";
import { useAuth } from "../hooks/useAuth";

function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="auth-wrap">
      <AuthModal forceOpen standalone />
    </div>
  );
}

export default LoginPage;
