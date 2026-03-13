import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

type InvoiceRow = {
  id: number
  invoice_number: string | null
  transaction_id: number
  seller_actor_id: number
  buyer_actor_id: number
  filiere?: string
  origin_reference?: string
  total_amount: number
  subtotal_ht?: number
  taxes_total?: number
  total_ttc?: number
  receipt_number?: string
  receipt_document_id?: number
  invoice_hash?: string
  status: string
}

export default function InvoicesPage() {
  const [downloadError, setDownloadError] = useState('')
  const [searchParams] = useSearchParams()
  const transactionIdParam = searchParams.get('transaction')
  const transactionId = transactionIdParam ? parseInt(transactionIdParam, 10) : undefined

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices', transactionId],
    queryFn: () => api.getInvoices(transactionId ? { transaction_id: transactionId } : undefined),
  })

  const handleDownloadReceipt = async (documentId?: number) => {
    if (!documentId) return
    setDownloadError('')
    try {
      const file = await api.downloadDocumentFile(documentId)
      const url = URL.createObjectURL(file.blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      setDownloadError('Telechargement du recu impossible.')
    }
  }

  return (
    <div className="dashboard">
      <h1>Factures</h1>
      <p className="dashboard-subtitle">
        Liste des factures generees automatiquement a la validation des paiements.
      </p>
      {downloadError && <p className="error">{downloadError}</p>}

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste des factures</h2>
          {invoices.length === 0 ? (
            <p className="empty-state">Aucune facture.</p>
          ) : (
            <ul className="list">
              {(invoices as InvoiceRow[]).map((inv) => (
                <li key={inv.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">
                      <Link to={`/transactions/${inv.transaction_id}`}>
                        Facture {inv.invoice_number || `#${inv.id}`}
                      </Link>
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>
                        {inv.status}
                      </span>
                    </div>
                    <div className="list-item-subtitle">
                      Transaction #{inv.transaction_id} - Vendeur {inv.seller_actor_id} {'->'} Acheteur {inv.buyer_actor_id}
                    </div>
                    <div className="list-item-subtitle">
                      Filiere {inv.filiere || '-'} - Origine {inv.origin_reference || '-'}
                    </div>
                    <div className="list-item-subtitle">
                      HT {inv.subtotal_ht ?? inv.total_amount} MGA - Taxes {inv.taxes_total ?? 0} MGA - TTC {inv.total_ttc ?? inv.total_amount} MGA
                    </div>
                    <div className="list-item-subtitle">
                      Hash: {inv.invoice_hash ? `${inv.invoice_hash.slice(0, 12)}...` : '-'}
                    </div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <Link className="btn-secondary" to={`/verify/invoice/${encodeURIComponent(inv.invoice_number || String(inv.id))}`}>
                        Verifier
                      </Link>
                      <button
                        type="button"
                        className="btn-secondary"
                        disabled={!inv.receipt_document_id}
                        onClick={() => handleDownloadReceipt(inv.receipt_document_id)}
                      >
                        {inv.receipt_number ? `Recu ${inv.receipt_number}` : 'Recu'}
                      </button>
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
