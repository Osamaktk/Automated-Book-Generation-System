import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";

function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
