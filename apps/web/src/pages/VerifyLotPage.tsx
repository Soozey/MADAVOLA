import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function VerifyLotPage() {
  const { id } = useParams<{ id: string }>()
  const lotId = id ? parseInt(id, 10) : NaN

  const { data, isLoading, error } = useQuery({
    queryKey: ['verify-lot', lotId],
    queryFn: () => api.getVerifyLot(lotId),
    enabled: Number.isInteger(lotId),
  })

  if (!Number.isInteger(lotId)) return <div className="dashboard"><p className="error">ID lot invalide.</p></div>
  if (isLoading) return <div className="loading">Chargement...</div>
  if (error || !data) return <div className="dashboard"><p className="error">Lot introuvable.</p></div>

  return (
    <div className="dashboard verify-page">
      <h1>Verification lot</h1>
      <div className="card verify-result-card">
        <div className="profile-info">
          <div className="info-item"><span className="info-label">Lot ID</span><span className="info-value">{data.id}</span></div>
          <div className="info-item"><span className="info-label">Statut</span><span className={`info-value status-badge status-${data.status}`}>{data.status}</span></div>
          <div className="info-item"><span className="info-label">Proprietaire</span><span className="info-value">{data.current_owner_actor_id}</span></div>
          <div className="info-item"><span className="info-label">Produit</span><span className="info-value">{data.product_type}</span></div>
          <div className="info-item"><span className="info-label">Quantite</span><span className="info-value">{data.quantity} {data.unit}</span></div>
          <div className="info-item"><span className="info-label">Recu</span><span className="info-value">{data.declaration_receipt_number ?? '—'}</span></div>
        </div>
      </div>
    </div>
  )
}
