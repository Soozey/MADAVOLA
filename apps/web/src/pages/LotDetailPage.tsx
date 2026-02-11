import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function LotDetailPage() {
  const { id } = useParams<{ id: string }>()
  const lotId = id ? parseInt(id, 10) : NaN

  const { data, isLoading, error } = useQuery({
    queryKey: ['lot', lotId],
    queryFn: () => api.getLot(lotId),
    enabled: Number.isInteger(lotId),
  })

  if (!Number.isInteger(lotId)) {
    return <div className="dashboard"><p className="error">ID invalide.</p><Link to="/lots">Retour</Link></div>
  }
  if (error) {
    return <div className="dashboard"><h1>Lot #{lotId}</h1><p className="error">Erreur.</p><Link to="/lots">Retour</Link></div>
  }
  if (isLoading) return <div className="loading">Chargement...</div>
  if (!data) return null

  return (
    <div className="dashboard">
      <h1>Lot #{data.id}</h1>
      <p className="dashboard-subtitle"><Link to="/lots">← Retour aux lots</Link></p>
      <div className="card">
        <div className="profile-info">
          <div className="info-item"><span className="info-label">Filière</span><span className="info-value">{data.filiere}</span></div>
          <div className="info-item"><span className="info-label">Type</span><span className="info-value">{data.product_type}</span></div>
          <div className="info-item"><span className="info-label">Quantité</span><span className="info-value">{data.quantity} {data.unit}</span></div>
          <div className="info-item"><span className="info-label">Propriétaire (ID)</span><span className="info-value">{data.current_owner_actor_id}</span></div>
          <div className="info-item"><span className="info-label">Statut</span><span className="info-value">{data.status}</span></div>
        </div>
      </div>
    </div>
  )
}
