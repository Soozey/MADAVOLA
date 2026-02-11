import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'
import './LotsPage.css'

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  submitted: 'Soumis',
  approved: 'Approuvé',
  rejected: 'Rejeté',
}

export default function ExportsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [destination, setDestination] = useState('')
  const [totalWeight, setTotalWeight] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data: exportsList = [], isLoading } = useQuery({
    queryKey: ['exports', statusFilter],
    queryFn: () => api.getExports(statusFilter ? { status: statusFilter } : undefined),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.createExport({
        destination: destination || undefined,
        total_weight: totalWeight ? parseFloat(totalWeight) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      setShowForm(false)
      setDestination('')
      setTotalWeight('')
      toast.success('Dossier export créé.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la création.')),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.updateExportStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      toast.success('Statut mis à jour.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la mise à jour.')),
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate()
  }

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Dossiers export</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouveau dossier'}
        </button>
      </div>
      <p className="dashboard-subtitle">
        Créez et suivez vos dossiers d&apos;export. Liez des lots en brouillon puis soumettez pour validation.
      </p>

      {showForm && (
        <div className="card form-card">
          <h2>Créer un dossier export</h2>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>Destination</label>
                <input
                  type="text"
                  className="form-control"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="ex: France"
                />
              </div>
              <div className="form-group">
                <label>Poids total (kg)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  value={totalWeight}
                  onChange={(e) => setTotalWeight(e.target.value)}
                  placeholder="optionnel"
                />
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Création...' : 'Créer le dossier'}
            </button>
          </form>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <label style={{ marginRight: '0.5rem' }}>Filtrer par statut :</label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="form-control"
          style={{ width: 'auto', display: 'inline-block', minWidth: 160 }}
        >
          <option value="">Tous</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste des dossiers</h2>
          {exportsList.length === 0 ? (
            <p className="empty-state">Aucun dossier export.</p>
          ) : (
            <ul className="list">
              {exportsList.map((exp: { id: number; status: string; destination: string | null; total_weight: number | null; created_by_actor_id: number; created_at: string }) => (
                <li key={exp.id} className="list-item">
                  <div className="list-item-content" style={{ flex: 1 }}>
                    <div className="list-item-title">
                      Dossier #{exp.id} — {exp.destination || 'Sans destination'}
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>
                        {STATUS_LABELS[exp.status] ?? exp.status}
                      </span>
                    </div>
                    <div className="list-item-subtitle">
                      Créé par acteur #{exp.created_by_actor_id}
                      {exp.total_weight != null && ` • ${exp.total_weight} kg`}
                      {' • '}
                      {new Date(exp.created_at).toLocaleDateString('fr-FR')}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    {exp.status === 'draft' && (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'submitted' })}
                        disabled={updateStatusMutation.isPending}
                      >
                        Soumettre
                      </button>
                    )}
                    {exp.status === 'submitted' && (
                      <>
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'approved' })}
                          disabled={updateStatusMutation.isPending}
                        >
                          Approuver
                        </button>
                        <button
                          type="button"
                          className="btn-danger"
                          onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'rejected' })}
                          disabled={updateStatusMutation.isPending}
                        >
                          Rejeter
                        </button>
                      </>
                    )}
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
