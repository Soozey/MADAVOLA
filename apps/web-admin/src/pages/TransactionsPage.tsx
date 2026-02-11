import { useEffect, useState } from "react";
import apiClient from "../lib/api";

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .get("/transactions?page=1&page_size=50")
      .then((response) => setTransactions(response.data.items || response.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Transactions</h1>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>ID</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Vendeur</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Acheteur</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Montant</th>
            <th style={{ border: "1px solid #ddd", padding: "0.5rem" }}>Statut</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr key={txn.id}>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{txn.id}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{txn.seller_actor_id}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{txn.buyer_actor_id}</td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>
                {txn.total_amount} {txn.currency}
              </td>
              <td style={{ border: "1px solid #ddd", padding: "0.5rem" }}>{txn.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
