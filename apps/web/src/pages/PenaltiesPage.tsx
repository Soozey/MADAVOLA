import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'
import './LotsPage.css'

export default function PenaltiesPage() {
  const [violationIdFilter, setViolationIdFilter] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [violationCaseId, setViolationCaseId] = useState('')
  const [penaltyType, setPenaltyType] = useState('')
  const [amount, setAmount] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  const violationIdNum = violationIdFilter ? parseInt(violationIdFilter, 10) : undefined

  const { data: penalties = [], isLoading } = useQuery({
    queryKey: ['penalties', violationIdNum],
    queryFn: () => api.getPenalties(violationIdNum != null ? { violation_case_id: violationIdNum } : undefined),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.createPenalty({
        violation_case_id: parseInt(violationCaseId, 10),
        penalty_type: penaltyType,
        amount: amount ? parseFloat(amount) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['penalties'] })
      setShowForm(false)
      setViolationCaseId('')
      setPenaltyType('')
      setAmount('')
      toast.success('Pénalité enregistrée.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la création.')),
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!violationCaseId || !penaltyType) return
    createMutation.mutate()
  }

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Pénalités</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouvelle pénalité'}
        </button>
      </div>
      <p className="dashboard-subtitle">
        Pénalités associées aux violations. Créez une pénalité à partir d&apos;une violation (case).
      </p>

      {showForm && (
        <div className="card form-card">
          <h2>Enregistrer une pénalité</h2>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>ID violation (case) *</label>
                <input
                  type="number"
                  className="form-control"
                  value={violationCaseId}
                  onChange={(e) => setViolationCaseId(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Type de pénalité *</label>
                <input
                  type="text"
                  className="form-control"
                  value={penaltyType}
                  onChange={(e) => setPenaltyType(e.target.value)}
                  placeholder="ex: amende"
                  required
                />
              </div>
              <div className="form-group">
                <label>Montant (MGA)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="optionnel"
                />
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </form>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <label style={{ marginRight: '0.5rem' }}>Filtrer par violation (case) ID :</label>
        <input
          type="number"
          className="form-control"
          style={{ width: 120, display: 'inline-block' }}
          value={violationIdFilter}
          onChange={(e) => setViolationIdFilter(e.target.value)}
          placeholder="optionnel"
        />
      </div>

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste des pénalités</h2>
          {penalties.length === 0 ? (
            <p className="empty-state">Aucune pénalité.</p>
          ) : (
            <ul className="list">
              {penalties.map((p: { id: number; violation_case_id: number; penalty_type: string; amount: number | null; status: string }) => (
                <li key={p.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">
                      Pénalité #{p.id} — {p.penalty_type}
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>{p.status}</span>
                    </div>
                    <div className="list-item-subtitle">
                      Violation case #{p.violation_case_id}
                      {p.amount != null && ` • ${p.amount} MGA`}
                    </div>
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
