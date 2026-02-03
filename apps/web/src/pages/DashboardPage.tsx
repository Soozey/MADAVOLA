import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'

export default function DashboardPage() {
  const { user } = useAuth()

  const { data: lots } = useQuery({
    queryKey: ['lots'],
    queryFn: () => api.getLots({ page: 1, page_size: 5 }),
  })

  const { data: transactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => api.getTransactions({ page: 1, page_size: 5 }),
  })

  return (
    <div>
      <h1 style={{ marginBottom: '30px' }}>Dashboard</h1>
      <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
        <h2>Profil</h2>
        <p>
          <strong>Nom:</strong> {user?.nom} {user?.prenoms}
        </p>
        <p>
          <strong>Email:</strong> {user?.email}
        </p>
        <p>
          <strong>Téléphone:</strong> {user?.telephone}
        </p>
        <p>
          <strong>Commune:</strong> {user?.commune?.name}
        </p>
        <p>
          <strong>Rôles:</strong> {user?.roles.map((r) => r.role).join(', ')}
        </p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
          <h3>Derniers lots</h3>
          {lots?.items?.length ? (
            <ul>
              {lots.items.map((lot: any) => (
                <li key={lot.id}>
                  {lot.product_type} - {lot.quantity} {lot.unit}
                </li>
              ))}
            </ul>
          ) : (
            <p>Aucun lot</p>
          )}
        </div>
        <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '8px' }}>
          <h3>Dernières transactions</h3>
          {transactions?.items?.length ? (
            <ul>
              {transactions.items.map((txn: any) => (
                <li key={txn.id}>
                  Transaction #{txn.id} - {txn.total_amount} {txn.currency}
                </li>
              ))}
            </ul>
          ) : (
            <p>Aucune transaction</p>
          )}
        </div>
      </div>
    </div>
  )
}
