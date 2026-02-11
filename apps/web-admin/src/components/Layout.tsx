import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

export default function Layout() {
  const { actor, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={{ width: "250px", background: "#1a1a1a", padding: "1rem" }}>
        <h2>MADAVOLA</h2>
        <nav style={{ marginTop: "2rem" }}>
          <Link to="/" style={{ display: "block", padding: "0.5rem", color: "white", textDecoration: "none" }}>
            Dashboard
          </Link>
          <Link to="/actors" style={{ display: "block", padding: "0.5rem", color: "white", textDecoration: "none" }}>
            Acteurs
          </Link>
          <Link to="/lots" style={{ display: "block", padding: "0.5rem", color: "white", textDecoration: "none" }}>
            Lots
          </Link>
          <Link
            to="/transactions"
            style={{ display: "block", padding: "0.5rem", color: "white", textDecoration: "none" }}
          >
            Transactions
          </Link>
          <Link to="/roles" style={{ display: "block", padding: "0.5rem", color: "white", textDecoration: "none" }}>
            Attribution des rôles
          </Link>
          <Link to="/config" style={{ display: "block", padding: "0.5rem", color: "white", textDecoration: "none" }}>
            Config système
          </Link>
        </nav>
        <div style={{ marginTop: "2rem", padding: "1rem", background: "#2a2a2a", borderRadius: "4px" }}>
          <div style={{ fontSize: "0.875rem" }}>{actor?.nom} {actor?.prenoms}</div>
          <div style={{ fontSize: "0.75rem", color: "#aaa", marginTop: "0.25rem" }}>{actor?.email}</div>
          <button onClick={handleLogout} style={{ marginTop: "1rem", padding: "0.5rem", width: "100%" }}>
            Déconnexion
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: "2rem" }}>
        <Outlet />
      </main>
    </div>
  );
}
