import { useEffect, useState } from "react";
import apiClient from "../lib/api";

export default function ActorsPage() {
  const [actors, setActors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get("/actors")
      .then((response) => setActors(response.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Acteurs</h1>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>ID</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Nom</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Email</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Téléphone</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Statut</th>
          </tr>
        </thead>
        <tbody>
          {actors.map((actor) => (
            <tr key={actor.id}>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{actor.id}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>
                {actor.nom} {actor.prenoms}
              </td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{actor.email}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{actor.telephone}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{actor.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
