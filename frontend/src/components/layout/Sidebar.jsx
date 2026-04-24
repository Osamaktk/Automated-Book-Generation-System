import { Link, useLocation } from "react-router-dom";

function Sidebar({ isAuthenticated, onAuthClick, onLogout, userEmail }) {
  const location = useLocation();

  const items = [
    { to: "/dashboard", icon: "L", label: "Library", key: "library" },
    { to: "/dashboard?tab=create", icon: "N", label: "New Book", key: "create" }
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
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="sidebar-footer">
        {isAuthenticated && userEmail ? (
          <div className="user-chip">
            <div className="user-avatar">{userEmail[0].toUpperCase()}</div>
            <div className="user-email" title={userEmail}>
              {userEmail}
            </div>
          </div>
        ) : (
          <div className="guest-chip">
            <div className="user-avatar">G</div>
            <div className="user-email">Guest Mode Active</div>
          </div>
        )}
        {isAuthenticated ? (
          <button className="btn-logout" onClick={onLogout} type="button">
            Sign Out
          </button>
        ) : (
          <button className="btn-logout" onClick={onAuthClick} type="button">
            Sign In
          </button>
        )}
      </div>
    </nav>
  );
}

export default Sidebar;
