import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { canSeeDashboardNational } from '../config/rolesMenu'
import { useAuth } from '../contexts/AuthContext'
import './DashboardPage.css'

export default function DashboardNationalPage() {
  const { user } = useAuth()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const effectiveRoles = userRoles
  const canSee = canSeeDashboardNational(effectiveRoles)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-national'],
    queryFn: () => api.getDashboardNational(),
    enabled: canSee,
  })

  if (!canSee) {
    return (
      <div className="dashboard">
        <h1>Vue nationale</h1>
        <p className="empty-state">Vous n'avez pas les habilitations pour accÃ©der au dashboard national.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <h1>Vue nationale</h1>
        <p className="error">Erreur lors du chargement des indicateurs.</p>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <h1>Vue nationale</h1>
      <p className="dashboard-subtitle">
        Indicateurs agrÃ©gÃ©s (volumes, recettes, anomalies, export, zones Ã  risque) â€” Lecture seule, accÃ¨s aux alertes stratÃ©giques.
      </p>
      {isLoading ? (
        <div className="loading">Chargement...</div>
      ) : data ? (
        <>
          <div className="dashboard-grid">
            <div className="stat-item">
              <div className="stat-value">{data.volume_created}</div>
              <div className="stat-label">Volume crÃ©Ã© (pÃ©riode)</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{data.transactions_total}</div>
              <div className="stat-label">Montant transactions (recettes)</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{data.nb_acteurs}</div>
              <div className="stat-label">Acteurs actifs</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{data.nb_lots}</div>
              <div className="stat-label">Lots</div>
            </div>
            {(data as { nb_exports_en_attente?: number }).nb_exports_en_attente != null && (
              <div className="stat-item">
                <div className="stat-value">{(data as { nb_exports_en_attente: number }).nb_exports_en_attente}</div>
                <div className="stat-label">Exports en attente</div>
              </div>
            )}
          </div>

          {data.alertes_strategiques?.length > 0 && (
            <div className="card">
              <h2>Alertes stratÃ©giques</h2>
              <ul className="list">
                {data.alertes_strategiques.map((a: { id: string; libelle: string; severite: string }) => (
                  <li key={a.id} className="list-item">
                    {(data as { nb_exports_en_attente?: number }).nb_exports_en_attente != null &&
                     (data as { nb_exports_en_attente: number }).nb_exports_en_attente > 0 &&
                     a.libelle.includes('export') ? (
                      <Link to="/exports" style={{ color: 'var(--color-primary)' }}>
                        <span className="badge">{a.severite}</span> {a.libelle}
                      </Link>
                    ) : (
                      <>
                        <span className="badge">{a.severite}</span> {a.libelle}
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}
