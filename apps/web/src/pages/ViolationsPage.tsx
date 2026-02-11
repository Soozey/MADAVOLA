import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'
import './LotsPage.css'

export default function ViolationsPage() {
  const [inspectionIdFilter, setInspectionIdFilter] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [inspectionId, setInspectionId] = useState('')
  const [violationType, setViolationType] = useState('')
  const [legalBasisRef, setLegalBasisRef] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  const inspectionIdNum = inspectionIdFilter ? parseInt(inspectionIdFilter, 10) : undefined

  const { data: violations = [], isLoading } = useQuery({
    queryKey: ['violations', inspectionIdNum],
    queryFn: () => api.getViolations(inspectionIdNum != null ? { inspection_id: inspectionIdNum } : undefined),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.createViolation({
        inspection_id: parseInt(inspectionId, 10),
        violation_type: violationType,
        legal_basis_ref: legalBasisRef || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['violations'] })
      setShowForm(false)
      setInspectionId('')
      setViolationType('')
      setLegalBasisRef('')
      toast.success('Violation enregistrée.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la création.')),
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inspectionId || !violationType) return
    createMutation.mutate()
  }

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Violations</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouvelle violation'}
        </button>
      </div>
      <p className="dashboard-subtitle">
        Violations constatées lors des inspections. Créez une violation à partir d&apos;une inspection.
      </p>

      {showForm && (
        <div className="card form-card">
          <h2>Enregistrer une violation</h2>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>ID inspection *</label>
                <input
                  type="number"
                  className="form-control"
                  value={inspectionId}
                  onChange={(e) => setInspectionId(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Type de violation *</label>
                <input
                  type="text"
                  className="form-control"
                  value={violationType}
                  onChange={(e) => setViolationType(e.target.value)}
                  placeholder="ex: non_conformite"
                  required
                />
              </div>
              <div className="form-group">
                <label>Référence juridique</label>
                <input
                  type="text"
                  className="form-control"
                  value={legalBasisRef}
                  onChange={(e) => setLegalBasisRef(e.target.value)}
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
        <label style={{ marginRight: '0.5rem' }}>Filtrer par inspection ID :</label>
        <input
          type="number"
          className="form-control"
          style={{ width: 120, display: 'inline-block' }}
          value={inspectionIdFilter}
          onChange={(e) => setInspectionIdFilter(e.target.value)}
          placeholder="optionnel"
        />
      </div>

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste des violations</h2>
          {violations.length === 0 ? (
            <p className="empty-state">Aucune violation.</p>
          ) : (
            <ul className="list">
              {violations.map((v: { id: number; inspection_id: number; violation_type: string; legal_basis_ref: string | null; status: string }) => (
                <li key={v.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">
                      Violation #{v.id} — {v.violation_type}
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>{v.status}</span>
                    </div>
                    <div className="list-item-subtitle">
                      Inspection #{v.inspection_id}
                      {v.legal_basis_ref && ` • ${v.legal_basis_ref}`}
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
