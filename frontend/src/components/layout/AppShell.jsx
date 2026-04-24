import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import Sidebar from "./Sidebar";

function AppShell() {
  const navigate = useNavigate();
  const { user, signOut, isAuthenticated, openAuthModal } = useAuth();

  async function handleLogout() {
    await signOut();
    navigate("/dashboard", { replace: true });
  }

  function handleAuthClick() {
    openAuthModal(null, "Sign in to save, sync, share, or export your work.");
  }

  return (
    <div className="app-shell">
      <Sidebar
        isAuthenticated={isAuthenticated}
        onAuthClick={handleAuthClick}
        onLogout={handleLogout}
        userEmail={user?.email || ""}
      />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
