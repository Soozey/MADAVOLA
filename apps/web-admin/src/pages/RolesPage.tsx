import { useEffect, useState } from "react";
import apiClient, { getRoleReferential, assignRole, getActorRoles } from "../lib/api";

type RoleRef = { code: string; level: string; institution: string; acronym: string | null; description: string };

export default function RolesPage() {
  const [referential, setReferential] = useState<RoleRef[]>([]);
  const [actors, setActors] = useState<any[]>([]);
  const [selectedActorId, setSelectedActorId] = useState<number | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>("");
  const [actorRoles, setActorRoles] = useState<Record<number, any[]>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getRoleReferential(),
      apiClient.get("/actors").then((r) => r.data),
    ])
      .then(([ref, acts]) => {
        setReferential(Array.isArray(ref) ? ref : []);
        setActors(Array.isArray(acts) ? acts : acts?.items ?? []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const loadActorRoles = (actorId: number) => {
    getActorRoles(actorId)
      .then((roles) => setActorRoles((prev) => ({ ...prev, [actorId]: roles })))
      .catch(console.error);
  };

  const handleAssign = () => {
    if (!selectedActorId || !selectedRole) return;
    setSubmitting(true);
    setMessage(null);
    assignRole(selectedActorId, selectedRole)
      .then(() => {
        setMessage("Rôle attribué.");
        loadActorRoles(selectedActorId);
      })
      .catch((err) => setMessage(err.response?.data?.detail || "Erreur"))
      .finally(() => setSubmitting(false));
  };

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Attribution des rôles</h1>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Référentiel des 19 autorités (niveau stratégique, central, contrôle, territorial, communautaire, judiciaire).
      </p>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "flex-end", marginBottom: "1.5rem" }}>
        <div>
          <label style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.875rem" }}>Acteur</label>
          <select
            value={selectedActorId ?? ""}
            onChange={(e) => {
              const id = Number(e.target.value) || null;
              setSelectedActorId(id);
              if (id) loadActorRoles(id);
            }}
            style={{ padding: "0.5rem", minWidth: "220px" }}
          >
            <option value="">Sélectionner un acteur</option>
            {actors.map((a) => (
              <option key={a.id} value={a.id}>
                {a.nom} {a.prenoms} ({a.email})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.875rem" }}>Rôle (institution)</label>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            style={{ padding: "0.5rem", minWidth: "320px" }}
          >
            <option value="">Sélectionner un rôle</option>
            {referential.map((r) => (
              <option key={r.code} value={r.code}>
                [{r.level}] {r.acronym ? `${r.acronym} – ` : ""}{r.institution}
              </option>
            ))}
          </select>
        </div>
        <button onClick={handleAssign} disabled={submitting || !selectedActorId || !selectedRole}>
          {submitting ? "..." : "Attribuer le rôle"}
        </button>
      </div>

      {message && <p style={{ marginBottom: "1rem", color: message.startsWith("Erreur") ? "#c00" : "#080" }}>{message}</p>}

      {selectedActorId && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Rôles actuels de l'acteur</h2>
          {actorRoles[selectedActorId] ? (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {(actorRoles[selectedActorId] || []).map((r: any) => (
                <li key={r.id} style={{ padding: "0.5rem", borderBottom: "1px solid #eee" }}>
                  {r.role} – {r.status}
                </li>
              ))}
            </ul>
          ) : (
            <button type="button" onClick={() => loadActorRoles(selectedActorId)}>
              Charger les rôles
            </button>
          )}
        </div>
      )}

      <div style={{ marginTop: "2rem" }}>
        <h2>Référentiel des rôles (niveau / institution)</h2>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
          <thead>
            <tr>
              <th style={{ border: "1px solid #ddd", padding: "0.5rem", textAlign: "left" }}>Code</th>
              <th style={{ border: "1px solid #ddd", padding: "0.5rem", textAlign: "left" }}>Niveau</th>
              <th style={{ border: "1px solid #ddd", padding: "0.5rem", textAlign: "left" }}>Acronyme</th>
              <th style={{ border: "1px solid #ddd", padding: "0.5rem", textAlign: "left" }}>Institution</th>
            </tr>
          </thead>
          <tbody>
            {referential.map((r) => (
              <tr key={r.code}>
                <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{r.code}</td>
                <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{r.level}</td>
                <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{r.acronym || "—"}</td>
                <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{r.institution}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
