import { Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import Sidebar from "./Sidebar";

function AppShell() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  async function handleLogout() {
    await signOut();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <Sidebar onLogout={handleLogout} userEmail={user?.email || ""} />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
