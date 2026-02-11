import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function ActorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const actorId = id ? parseInt(id, 10) : NaN

  const { data, isLoading, error } = useQuery({
    queryKey: ['actor', actorId],
    queryFn: () => api.getActor(actorId),
    enabled: Number.isInteger(actorId),
  })

  if (!Number.isInteger(actorId)) {
    return (
      <div className="dashboard">
        <p className="error">ID d'acteur invalide.</p>
        <Link to="/actors">Retour aux acteurs</Link>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <h1>Acteur #{actorId}</h1>
        <p className="error">Erreur lors du chargement.</p>
        <Link to="/actors">Retour aux acteurs</Link>
      </div>
    )
  }

  if (isLoading) return <div className="loading">Chargement...</div>
  if (!data) return null

  return (
    <div className="dashboard">
      <h1>Acteur #{data.id}</h1>
      <p className="dashboard-subtitle">
        <Link to="/actors">← Retour aux acteurs</Link>
      </p>
      <div className="card">
        <div className="profile-info">
          <div className="info-item">
            <span className="info-label">Nom</span>
            <span className="info-value">{data.nom} {data.prenoms}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Email</span>
            <span className="info-value">{data.email || '—'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Téléphone</span>
            <span className="info-value">{data.telephone}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Région / District / Commune</span>
            <span className="info-value">{data.region_code} / {data.district_code} / {data.commune_code}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Statut</span>
            <span className="info-value">{data.status}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
