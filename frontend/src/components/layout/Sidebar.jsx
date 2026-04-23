import { Link, useLocation } from "react-router-dom";

function Sidebar({ onLogout, userEmail }) {
  const location = useLocation();

  const items = [
    { to: "/dashboard", icon: "Library", label: "Library", key: "library" },
    { to: "/dashboard?tab=create", icon: "Create", label: "New Book", key: "create" }
  ];

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">AB</div>
        <h1>AutoBook</h1>
        <p>AI Publishing System</p>
      </div>

      <div className="sidebar-nav">
        <div className="nav-section-label">Workspace</div>
        {items.map((item) => {
          const active =
            location.pathname === "/dashboard" &&
            ((item.key === "library" && !location.search.includes("tab=create")) ||
              (item.key === "create" && location.search.includes("tab=create")));

          return (
            <Link key={item.to} className={`nav-item ${active ? "active" : ""}`} to={item.to}>
              <span className="nav-icon">{item.icon.slice(0, 1)}</span>
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="sidebar-footer">
        {userEmail ? (
          <div className="user-chip">
            <div className="user-avatar">{userEmail[0].toUpperCase()}</div>
            <div className="user-email" title={userEmail}>
              {userEmail}
            </div>
          </div>
        ) : null}
        <button className="btn-logout" onClick={onLogout} type="button">
          <span>Out</span> Sign Out
        </button>
      </div>
    </nav>
  );
}

export default Sidebar;
