import { NavLink, useNavigate } from "react-router-dom";
import { getCurrentUser, logout } from "../services/authApi";

function AppLayout({ title, links, children }) {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();

  const handleLogout = () => {
    logout();
    navigate("/connexion");
  };

  return (
    <main className="workspace-layout">
      <section className="workspace-card">
        <p className="workspace-title">{title}</p>
        <nav className="workspace-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {link.label}
            </NavLink>
          ))}
          <button type="button" onClick={handleLogout} className="nav-link nav-button">
            Deconnexion
          </button>
        </nav>
        <p className="workspace-user">
          Connecte : {currentUser && currentUser.role}
        </p>
        {children}
      </section>
    </main>
  );
}

export default AppLayout;
