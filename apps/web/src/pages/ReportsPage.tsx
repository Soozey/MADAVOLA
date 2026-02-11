import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import './DashboardPage.css'

function toCSVRow(values: (string | number)[]): string {
  return values
    .map((v) =>
      typeof v === 'string' && (v.includes(',') || v.includes('"') || v.includes('\n'))
        ? `"${v.replace(/"/g, '""')}"`
        : v
    )
    .join(',')
}

export default function ReportsPage() {
  const { user } = useAuth()
  const communeId = (user?.commune as { id?: number })?.id
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [actorIdForReport, setActorIdForReport] = useState('')

  const params = { date_from: dateFrom || undefined, date_to: dateTo || undefined }

  const { data: national, isLoading: loadingNational } = useQuery({
    queryKey: ['report-national', params.date_from, params.date_to],
    queryFn: () => api.getReportNational(params),
  })

  const { data: commune, isLoading: loadingCommune } = useQuery({
    queryKey: ['report-commune', communeId, params.date_from, params.date_to],
    queryFn: () => api.getReportCommune(communeId!, params),
    enabled: !!communeId,
  })

  const actorIdNum = actorIdForReport ? parseInt(actorIdForReport, 10) : undefined
  const { data: actorReport, isLoading: loadingActor } = useQuery({
    queryKey: ['report-actor', actorIdNum, params.date_from, params.date_to],
    queryFn: () => api.getReportActor(actorIdNum!, params),
    enabled: !!actorIdNum,
  })

  const handleExportCSV = () => {
    const rows: (string | number)[][] = [['Rapport', 'Volume créé', 'Montant transactions']]
    if (national) rows.push(['National', national.volume_created, national.transactions_total])
    if (commune) rows.push(['Commune ' + communeId, commune.volume_created, commune.transactions_total])
    if (actorReport) rows.push(['Acteur ' + actorIdNum, actorReport.volume_created, actorReport.transactions_total])
    const csv = rows.map(toCSVRow).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `rapports_madavola_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(link.href)
  }

  return (
    <div className="dashboard">
      <h1>Rapports</h1>
      <p className="dashboard-subtitle">Rapports nationaux, communaux et par acteur. Filtrez par période.</p>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>Filtres</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Du</label>
            <input type="date" className="form-control" style={{ width: 160 }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Au</label>
            <input type="date" className="form-control" style={{ width: 160 }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <button type="button" className="btn-secondary" onClick={handleExportCSV}>Exporter en CSV</button>
        </div>
      </div>

      <div className="card">
        <h2>Rapport national</h2>
        {loadingNational ? <div className="loading">Chargement...</div> : national ? (
          <div className="stats-grid">
            <div className="stat-item"><div className="stat-value">{national.volume_created}</div><div className="stat-label">Volume créé</div></div>
            <div className="stat-item"><div className="stat-value">{national.transactions_total}</div><div className="stat-label">Montant transactions</div></div>
          </div>
        ) : <p className="empty-state">Données non disponibles ou accès refusé.</p>}
      </div>
      {communeId && (
        <div className="card">
          <h2>Rapport communal</h2>
          {loadingCommune ? <div className="loading">Chargement...</div> : commune ? (
            <div className="stats-grid">
              <div className="stat-item"><div className="stat-value">{commune.volume_created}</div><div className="stat-label">Volume créé</div></div>
              <div className="stat-item"><div className="stat-value">{commune.transactions_total}</div><div className="stat-label">Montant transactions</div></div>
            </div>
          ) : <p className="empty-state">Données non disponibles.</p>}
        </div>
      )}

      <div className="card">
        <h2>Rapport par acteur</h2>
        <p className="form-hint">Saisissez l&apos;ID d&apos;un acteur pour afficher son rapport.</p>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1rem' }}>
          <input type="number" className="form-control" style={{ width: 120 }} value={actorIdForReport} onChange={(e) => setActorIdForReport(e.target.value)} placeholder="ID acteur" />
        </div>
        {actorIdNum && (loadingActor ? <div className="loading">Chargement...</div> : actorReport ? (
          <div className="stats-grid">
            <div className="stat-item"><div className="stat-value">{actorReport.volume_created}</div><div className="stat-label">Volume créé (acteur {actorIdNum})</div></div>
            <div className="stat-item"><div className="stat-value">{actorReport.transactions_total}</div><div className="stat-label">Montant transactions</div></div>
          </div>
        ) : <p className="empty-state">Aucune donnée pour cet acteur.</p>)}
      </div>
    </div>
  )
}
