import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function InvoicesPage() {
  const [searchParams] = useSearchParams()
  const transactionIdParam = searchParams.get('transaction')
  const transactionId = transactionIdParam ? parseInt(transactionIdParam, 10) : undefined

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices', transactionId],
    queryFn: () => api.getInvoices(transactionId ? { transaction_id: transactionId } : undefined),
  })

  return (
    <div className="dashboard">
      <h1>Factures</h1>
      <p className="dashboard-subtitle">
        Liste des factures générées après paiement des transactions.
      </p>

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste des factures</h2>
          {invoices.length === 0 ? (
            <p className="empty-state">Aucune facture.</p>
          ) : (
            <ul className="list">
              {invoices.map((inv: { id: number; invoice_number: string | null; transaction_id: number; seller_actor_id: number; buyer_actor_id: number; total_amount: number; status: string }) => (
                <li key={inv.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">
                      <Link to={`/transactions/${inv.transaction_id}`}>
                        Facture {inv.invoice_number ?? `#${inv.id}`}
                      </Link>
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>
                        {inv.status}
                      </span>
                    </div>
                    <div className="list-item-subtitle">
                      Transaction #{inv.transaction_id} • Vendeur {inv.seller_actor_id} → Acheteur {inv.buyer_actor_id}
                      {' • '}
                      {inv.total_amount} MGA
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
