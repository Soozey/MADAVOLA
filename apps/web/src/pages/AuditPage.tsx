import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function AuditPage() {
  const { data: logs, isLoading, error } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => api.getAuditLogs(),
  })

  return (
    <div className="dashboard">
      <h1>Audit / Traces</h1>
      <p className="dashboard-subtitle">Consultation des logs d'audit (admin, dirigeant, BIANCO).</p>
      {error && <p className="error">Erreur lors du chargement des logs.</p>}
      {isLoading && <div className="loading">Chargement...</div>}
      {logs && (
        <div className="card">
          <h2>Dernières actions</h2>
          {logs.length === 0 ? <p className="empty-state">Aucun log.</p> : (
            <ul className="list">
              {logs.slice(0, 50).map((log: { id: number; action: string; entity_type: string; entity_id: string; created_at: string }) => (
                <li key={log.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">{log.action} – {log.entity_type} #{log.entity_id}</div>
                    <div className="list-item-subtitle">{log.created_at}</div>
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
