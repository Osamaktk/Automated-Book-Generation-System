import { Link, useLocation } from "react-router-dom";
import logoMark from "../../assets/autobook-mark.svg";

function LibraryIcon() {
  return (
    <svg className="nav-icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M6 4.5h9.5a2 2 0 0 1 2 2V19a1 1 0 0 1-1.6.8l-1.7-1.26a1 1 0 0 0-1.2 0l-1.7 1.26a1 1 0 0 1-1.2 0l-1.7-1.26a1 1 0 0 0-1.2 0L5.6 19.8A1 1 0 0 1 4 19V6.5a2 2 0 0 1 2-2Z" />
      <path d="M8 8.5h6.5" />
      <path d="M8 12h6.5" />
    </svg>
  );
}

function NewBookIcon() {
  return (
    <svg className="nav-icon-svg" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 4.5h7.8c.7 0 1.37.28 1.87.78l1.55 1.55c.5.5.78 1.17.78 1.87V18a2 2 0 0 1-2 2H7A2 2 0 0 1 5 18V6.5a2 2 0 0 1 2-2Z" />
      <path d="M12 9v6" />
      <path d="M9 12h6" />
    </svg>
  );
}

function Sidebar() {
  const location = useLocation();

  const items = [
    { to: "/dashboard", icon: <LibraryIcon />, label: "Library", key: "library" },
    { to: "/dashboard?tab=create", icon: <NewBookIcon />, label: "New Book", key: "create" }
  ];

  return (
    <nav className="sidebar">
      <Link className="sidebar-logo sidebar-home-link" to="/dashboard">
        <div className="logo-mark-wrap">
          <img className="logo-mark" src={logoMark} alt="AutoBook logo" />
          <span className="logo-orbit logo-orbit-one" />
          <span className="logo-orbit logo-orbit-two" />
        </div>
        <div className="logo-copy">
          <h1>AutoBook</h1>
          <p>AI Publishing System</p>
        </div>
      </Link>

      <div className="sidebar-nav">
        <div className="nav-section-label">Workspace</div>
        <div className="nav-links">
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
      </div>

      <div className="sidebar-footer">
        <div className="guest-chip">
          <div className="user-avatar">E</div>
          <div className="user-email">Editor Workspace</div>
        </div>
      </div>
    </nav>
  );
}

export default Sidebar;
