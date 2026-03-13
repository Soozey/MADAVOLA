import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { canSeeDashboardRegional } from '../config/rolesMenu'
import { useAuth } from '../contexts/AuthContext'
import './DashboardPage.css'

export default function DashboardRegionalPage() {
  const { user } = useAuth()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const effectiveRoles = userRoles
  const canSee = canSeeDashboardRegional(effectiveRoles)

  const { data: regionsData } = useQuery({
    queryKey: ['territories-regions'],
    queryFn: () => api.getRegions(),
    enabled: canSee,
  })

  const userRegion = user?.region as { id?: number } | undefined
  const [selectedRegionId, setSelectedRegionId] = useState<number | null>(userRegion?.id ?? null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-regional', selectedRegionId],
    queryFn: () => api.getDashboardRegional(selectedRegionId!),
    enabled: canSee && selectedRegionId != null,
  })

  if (!canSee) {
    return (
      <div className="dashboard">
        <h1>Vue régionale</h1>
        <p className="empty-state">Vous n'avez pas les habilitations pour accéder au dashboard régional.</p>
      </div>
    )
  }

  const regions = (regionsData ?? []) as { id?: number; code: string; name: string }[]
  const effectiveRegionId = selectedRegionId ?? userRegion?.id ?? regions[0]?.id

  return (
    <div className="dashboard">
      <h1>Vue régionale</h1>
      <p className="dashboard-subtitle">Pilotage régional (Gouverneur, communes, décentralisation)</p>

      {regions.length > 0 && (
        <div className="form-group" style={{ maxWidth: 320, marginBottom: '1.5rem' }}>
          <label htmlFor="region">Région</label>
          <select
            id="region"
            value={effectiveRegionId ?? ''}
            onChange={(e) => setSelectedRegionId(Number(e.target.value) || null)}
          >
            <option value="">Sélectionner une région</option>
            {regions.map((r) => (
              <option key={r.code} value={r.id ?? r.code}>
                {r.name} ({r.code})
              </option>
            ))}
          </select>
        </div>
      )}

      {error && <p className="error">Erreur lors du chargement.</p>}
      {isLoading && effectiveRegionId && <div className="loading">Chargement...</div>}

      {data && (
        <div className="dashboard-grid">
          <div className="stat-item">
            <div className="stat-value">{data.region_name}</div>
            <div className="stat-label">Région</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{data.volume_created}</div>
            <div className="stat-label">Volume créé</div>
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
      )}
    </div>
  )
}
