import { useEffect, useState } from "react";
import apiClient from "../lib/api";

export default function LotsPage() {
  const [lots, setLots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get("/lots?page=1&page_size=50")
      .then((response) => setLots(response.data.items || response.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Lots</h1>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>ID</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Filière</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Type</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Quantité</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Statut</th>
          </tr>
        </thead>
        <tbody>
          {lots.map((lot) => (
            <tr key={lot.id}>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{lot.id}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{lot.filiere}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{lot.product_type}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>
                {lot.quantity} {lot.unit}
              </td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{lot.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
