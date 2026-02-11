import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { canSeeDashboardCommune } from '../config/rolesMenu'
import { useAuth } from '../contexts/AuthContext'
import './DashboardPage.css'

export default function DashboardCommunePage() {
  const { user } = useAuth()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const effectiveRoles = userRoles
  const canSee = canSeeDashboardCommune(effectiveRoles)

  const communeId = (user?.commune as { id?: number })?.id ?? null

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-commune', communeId],
    queryFn: () => api.getDashboardCommune(communeId!),
    enabled: canSee && communeId != null,
  })

  if (!canSee) {
    return (
      <div className="dashboard">
        <h1>Vue communale</h1>
        <p className="empty-state">Vous n'avez pas les habilitations pour accÃ©der au dashboard communal.</p>
      </div>
    )
  }

  if (!communeId) {
    return (
      <div className="dashboard">
        <h1>Vue communale</h1>
        <p className="empty-state">Aucune commune associÃ©e Ã  votre profil.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <h1>Vue communale</h1>
        <p className="error">Erreur lors du chargement.</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <h1>ðŸ˜ï¸ Vue communale</h1>
      <p className="dashboard-subtitle">Recensement, validation, recettes (Maire / Agent commune)</p>

      {isLoading ? (
        <div className="loading">Chargement...</div>
      ) : data ? (
        <div className="dashboard-grid">
          <div className="stat-item">
            <div className="stat-value">{data.commune_name}</div>
            <div className="stat-label">Commune</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.volume_created}</div>
            <div className="stat-label">Volume crÃ©Ã©</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.transactions_total}</div>
            <div className="stat-label">Montant transactions</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.nb_acteurs}</div>
            <div className="stat-label">Acteurs</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.nb_lots}</div>
            <div className="stat-label">Lots</div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
