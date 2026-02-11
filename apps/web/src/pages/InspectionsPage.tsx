import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'
import './LotsPage.css'

export default function InspectionsPage() {
  const [showForm, setShowForm] = useState(false)
  const [inspectedActorId, setInspectedActorId] = useState('')
  const [inspectedLotId, setInspectedLotId] = useState('')
  const [result, setResult] = useState('conforme')
  const [reasonCode, setReasonCode] = useState('')
  const [notes, setNotes] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data: inspections = [], isLoading, error } = useQuery({
    queryKey: ['inspections'],
    queryFn: () => api.getInspections(),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.createInspection({
        inspected_actor_id: inspectedActorId ? parseInt(inspectedActorId, 10) : undefined,
        inspected_lot_id: inspectedLotId ? parseInt(inspectedLotId, 10) : undefined,
        result,
        reason_code: reasonCode || undefined,
        notes: notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inspections'] })
      setShowForm(false)
      setInspectedActorId('')
      setInspectedLotId('')
      setReasonCode('')
      setNotes('')
      toast.success('Inspection enregistrée.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la création.')),
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate()
  }

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Contrôles / Inspections</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouvelle inspection'}
        </button>
      </div>
      <p className="dashboard-subtitle">
        Profil Contrôleur (Police, Gendarmerie, DGD) – scan QR, PV, observations. Enregistrez une inspection (acteur et/ou lot contrôlé).
      </p>

      {showForm && (
        <div className="card form-card">
          <h2>Créer une inspection</h2>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>ID acteur contrôlé</label>
                <input
                  type="number"
                  className="form-control"
                  value={inspectedActorId}
                  onChange={(e) => setInspectedActorId(e.target.value)}
                  placeholder="optionnel"
                />
              </div>
              <div className="form-group">
                <label>ID lot contrôlé</label>
                <input
                  type="number"
                  className="form-control"
                  value={inspectedLotId}
                  onChange={(e) => setInspectedLotId(e.target.value)}
                  placeholder="optionnel"
                />
              </div>
              <div className="form-group">
                <label>Résultat *</label>
                <select
                  className="form-control"
                  value={result}
                  onChange={(e) => setResult(e.target.value)}
                  required
                >
                  <option value="conforme">Conforme</option>
                  <option value="non_conforme">Non conforme</option>
                  <option value="observation">Observation</option>
                </select>
              </div>
              <div className="form-group">
                <label>Code motif</label>
                <input
                  type="text"
                  className="form-control"
                  value={reasonCode}
                  onChange={(e) => setReasonCode(e.target.value)}
                  placeholder="optionnel"
                />
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Notes</label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Observations, PV..."
                />
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Enregistrement...' : 'Enregistrer l\'inspection'}
            </button>
          </form>
        </div>
      )}

      {error && <p className="error">Erreur lors du chargement.</p>}
      {isLoading && <div className="loading">Chargement...</div>}

      {!isLoading && (
        <div className="card">
          <h2>Liste des inspections</h2>
          {inspections.length === 0 ? (
            <p className="empty-state">Aucune inspection.</p>
          ) : (
            <ul className="list">
              {inspections.map((i: { id: number; result: string; inspected_actor_id: number | null; inspected_lot_id: number | null; reason_code: string | null; notes: string | null }) => (
                <li key={i.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">
                      Inspection #{i.id} – Résultat : {i.result}
                    </div>
                    <div className="list-item-subtitle">
                      {i.inspected_actor_id != null && (
                        <>Acteur <Link to={`/actors/${i.inspected_actor_id}`}>{i.inspected_actor_id}</Link></>
                      )}
                      {i.inspected_actor_id != null && i.inspected_lot_id != null && ' • '}
                      {i.inspected_lot_id != null && (
                        <>Lot <Link to={`/lots/${i.inspected_lot_id}`}>{i.inspected_lot_id}</Link></>
                      )}
                      {!i.inspected_actor_id && !i.inspected_lot_id && '—'}
                      {i.reason_code && ` • ${i.reason_code}`}
                      {i.notes && ` • ${i.notes}`}
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
