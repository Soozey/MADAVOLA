import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function VerifyInvoicePage() {
  const { ref } = useParams<{ ref: string }>()
  const invoiceRef = decodeURIComponent(ref || '').trim()

  const { data, isLoading, error } = useQuery({
    queryKey: ['verify-invoice', invoiceRef],
    queryFn: () => api.getVerifyInvoice(invoiceRef),
    enabled: !!invoiceRef,
  })

  if (!invoiceRef) return <div className="dashboard"><p className="error">Reference facture invalide.</p></div>
  if (isLoading) return <div className="loading">Chargement...</div>
  if (error || !data) return <div className="dashboard"><p className="error">Facture introuvable.</p></div>

  return (
    <div className="dashboard verify-page">
      <h1>Verification facture</h1>
      <div className="card verify-result-card">
        <div className="profile-info">
          <div className="info-item"><span className="info-label">Numero</span><span className="info-value">{data.invoice_number}</span></div>
          <div className="info-item"><span className="info-label">Statut</span><span className={`info-value status-badge status-${data.status}`}>{data.status}</span></div>
          <div className="info-item"><span className="info-label">Transaction</span><span className="info-value">{data.transaction_id}</span></div>
          <div className="info-item"><span className="info-label">Filiere</span><span className="info-value">{data.filiere || '-'}</span></div>
          <div className="info-item"><span className="info-label">Origine</span><span className="info-value">{data.origin_reference || '-'}</span></div>
          <div className="info-item"><span className="info-label">Montant HT</span><span className="info-value">{data.subtotal_ht ?? data.total_amount}</span></div>
          <div className="info-item"><span className="info-label">Taxes</span><span className="info-value">{data.taxes_total ?? 0}</span></div>
          <div className="info-item"><span className="info-label">Total TTC</span><span className="info-value">{data.total_ttc ?? data.total_amount}</span></div>
          <div className="info-item"><span className="info-label">Hash</span><span className="info-value">{data.invoice_hash || '-'}</span></div>
          <div className="info-item"><span className="info-label">Hash precedent</span><span className="info-value">{data.previous_invoice_hash || '-'}</span></div>
          <div className="info-item"><span className="info-label">Signature</span><span className="info-value">{data.internal_signature || '-'}</span></div>
          <div className="info-item"><span className="info-label">Recu</span><span className="info-value">{data.receipt_number || '-'}</span></div>
        </div>
      </div>
    </div>
  )
}
