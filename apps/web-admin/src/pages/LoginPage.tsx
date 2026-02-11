import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import apiClient from "../lib/api";

export default function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await apiClient.post("/auth/login", {
        identifier,
        password,
      });

      const { access_token, refresh_token } = response.data;

      // Récupérer le profil
      const meResponse = await apiClient.get("/auth/me", {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      login(access_token, refresh_token, meResponse.data);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || "Erreur de connexion");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: "400px", padding: "2rem" }}>
        <h1>MADAVOLA Admin</h1>
        <div style={{ marginBottom: "1rem" }}>
          <label>
            Email ou Téléphone
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
            />
          </label>
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label>
            Mot de passe
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
            />
          </label>
        </div>
        {error && <div style={{ color: "red", marginBottom: "1rem" }}>{error}</div>}
        <button type="submit" disabled={loading} style={{ width: "100%", padding: "0.75rem" }}>
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </div>
  );
}
