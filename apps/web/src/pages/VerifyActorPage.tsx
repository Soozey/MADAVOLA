import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function VerifyActorPage() {
  const { id } = useParams<{ id: string }>()
  const actorId = id ? parseInt(id, 10) : NaN

  const { data, isLoading, error } = useQuery({
    queryKey: ['verify-actor', actorId],
    queryFn: () => api.getVerifyActor(actorId),
    enabled: Number.isInteger(actorId),
  })

  if (!Number.isInteger(actorId)) {
    return (
      <div className="dashboard verify-page">
        <h1>Vérification acteur</h1>
        <p className="error">ID acteur invalide.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard verify-page">
        <h1>Vérification acteur</h1>
        <p className="error">Acteur introuvable ou erreur de chargement.</p>
      </div>
    )
  }

  if (isLoading) return <div className="loading">Chargement...</div>
  if (!data) return null

  return (
    <div className="dashboard verify-page">
      <h1>Vérification acteur (scan QR)</h1>
      <p className="dashboard-subtitle">Contrôleur : identité vérifiée via carte orpailleur/collecteur.</p>
      <div className="card verify-result-card">
        <div className="verify-badge">MADAVOLA</div>
        <div className="profile-info">
          <div className="info-item">
            <span className="info-label">ID acteur</span>
            <span className="info-value">{data.id}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Nom</span>
            <span className="info-value">{data.nom} {data.prenoms}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Statut</span>
            <span className={`info-value status-badge status-${data.statut}`}>{data.statut}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Commune (code)</span>
            <span className="info-value">{data.commune_code || '—'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Type</span>
            <span className="info-value">{data.type_personne}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
