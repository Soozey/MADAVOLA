import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'

export default function TransactionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const transactionId = id ? parseInt(id, 10) : NaN
  const queryClient = useQueryClient()
  const toast = useToast()
  const [providerCode, setProviderCode] = useState('orange_money')

  const { data, isLoading, error } = useQuery({
    queryKey: ['transaction', transactionId],
    queryFn: () => api.getTransaction(transactionId),
    enabled: Number.isInteger(transactionId),
  })

  const { data: payments = [] } = useQuery({
    queryKey: ['transaction-payments', transactionId],
    queryFn: () => api.getTransactionPayments(transactionId),
    enabled: Number.isInteger(transactionId),
  })

  const { data: invoices = [] } = useQuery({
    queryKey: ['invoices', transactionId],
    queryFn: () => api.getInvoices({ transaction_id: transactionId }),
    enabled: Number.isInteger(transactionId),
  })

  const initiatePayment = useMutation({
    mutationFn: () =>
      api.initiateTransactionPayment(transactionId, {
        provider_code: providerCode,
        external_ref: `txn-${transactionId}-${Date.now()}`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transaction-payments', transactionId] })
      queryClient.invalidateQueries({ queryKey: ['transaction', transactionId] })
      toast.success('Paiement initié. Suivez les instructions du prestataire.')
    },
    onError: (err) => {
      toast.error(getErrorMessage(err, 'Impossible d\'initier le paiement.'))
    },
  })

  if (!Number.isInteger(transactionId)) {
    return (
      <div className="dashboard">
        <p className="error">ID invalide.</p>
        <Link to="/transactions">← Retour</Link>
      </div>
    )
  }
  if (error) {
    return (
      <div className="dashboard">
        <h1>Transaction #{transactionId}</h1>
        <p className="error">Erreur lors du chargement.</p>
        <Link to="/transactions">← Retour aux transactions</Link>
      </div>
    )
  }
  if (isLoading) return <div className="loading">Chargement...</div>
  if (!data) return null

  const canInitiatePayment = data.status === 'pending_payment'
  const invoice = Array.isArray(invoices) && invoices.length > 0 ? invoices[0] : null

  return (
    <div className="dashboard">
      <h1>Transaction #{data.id}</h1>
      <p className="dashboard-subtitle">
        <Link to="/transactions">← Retour aux transactions</Link>
      </p>

      <div className="card">
        <h2>Informations générales</h2>
        <div className="profile-info">
          <div className="info-item">
            <span className="info-label">Vendeur (acteur ID)</span>
            <span className="info-value">
              <Link to={`/actors/${data.seller_actor_id}`}>{data.seller_actor_id}</Link>
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Acheteur (acteur ID)</span>
            <span className="info-value">
              <Link to={`/actors/${data.buyer_actor_id}`}>{data.buyer_actor_id}</Link>
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Montant total</span>
            <span className="info-value">
              {data.total_amount} {data.currency}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Statut</span>
            <span className="info-value">
              <span className={`badge badge-${data.status === 'paid' ? 'success' : data.status === 'pending_payment' ? 'warning' : 'default'}`}>
                {data.status}
              </span>
            </span>
          </div>
          {invoice && (
            <div className="info-item">
              <span className="info-label">Facture</span>
              <span className="info-value">
                <Link to={`/invoices?transaction=${transactionId}`} title="Voir la facture">
                  Facture #{invoice.invoice_number ?? invoice.id}
                </Link>
              </span>
            </div>
          )}
        </div>
      </div>

      {data.items && data.items.length > 0 && (
        <div className="card">
          <h2>Lignes de la transaction</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Lot ID</th>
                <th>Quantité</th>
                <th>Prix unitaire</th>
                <th>Montant ligne</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item: { id: number; lot_id: number | null; quantity: number; unit_price: number; line_amount: number }) => (
                <tr key={item.id}>
                  <td>{item.lot_id != null ? <Link to={`/lots/${item.lot_id}`}>{item.lot_id}</Link> : '—'}</td>
                  <td>{item.quantity}</td>
                  <td>{item.unit_price} {data.currency}</td>
                  <td>{item.line_amount} {data.currency}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {canInitiatePayment && (
        <div className="card">
          <h2>Initier un paiement</h2>
          <p className="form-hint">Choisissez le moyen de paiement et lancez la demande.</p>
          <div className="form-group" style={{ maxWidth: 320, marginBottom: '1rem' }}>
            <label>Prestataire</label>
            <select
              value={providerCode}
              onChange={(e) => setProviderCode(e.target.value)}
              className="form-control"
            >
              <option value="orange_money">Orange Money</option>
              <option value="mvola">Mvola</option>
              <option value="airtel_money">Airtel Money</option>
            </select>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            disabled={initiatePayment.isPending}
            onClick={() => initiatePayment.mutate()}
          >
            {initiatePayment.isPending ? 'En cours...' : 'Initier le paiement'}
          </button>
        </div>
      )}

      {payments.length > 0 && (
        <div className="card">
          <h2>Historique des paiements</h2>
          <ul className="list">
            {payments.map((p: { payment_request_id: number; payment_id: number; status: string; external_ref: string }) => (
              <li key={p.payment_request_id} className="list-item">
                <div className="list-item-content">
                  <div className="list-item-title">Demande #{p.payment_request_id}</div>
                  <div className="list-item-subtitle">
                    Réf. {p.external_ref} — Statut: <strong>{p.status}</strong>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
