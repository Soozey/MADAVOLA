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
  const [penaltyType, setPenaltyType] = useState('amende')
  const [amount, setAmount] = useState('')
  const [actionOnLot, setActionOnLot] = useState('none')
  const [seizedToActorId, setSeizedToActorId] = useState('')
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
        action_on_lot: actionOnLot !== 'none' ? actionOnLot : undefined,
        seized_to_actor_id: actionOnLot === 'seize' && seizedToActorId ? parseInt(seizedToActorId, 10) : undefined,
      } as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['penalties'] })
      queryClient.invalidateQueries({ queryKey: ['violations'] })
      setShowForm(false)
      setViolationCaseId('')
      setPenaltyType('amende')
      setAmount('')
      setActionOnLot('none')
      setSeizedToActorId('')
      toast.success('Penalite enregistree.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la creation.')),
  })

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Penalites</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouvelle penalite'}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2>Enregistrer une penalite</h2>
          <form onSubmit={(e) => { e.preventDefault(); if (violationCaseId) createMutation.mutate() }}>
            <div className="form-grid">
              <div className="form-group">
                <label>ID violation case *</label>
                <input type="number" className="form-control" value={violationCaseId} onChange={(e) => setViolationCaseId(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Type penalite *</label>
                <input type="text" className="form-control" value={penaltyType} onChange={(e) => setPenaltyType(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Montant (MGA)</label>
                <input type="number" step="0.01" className="form-control" value={amount} onChange={(e) => setAmount(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Action lot</label>
                <select className="form-control" value={actionOnLot} onChange={(e) => setActionOnLot(e.target.value)}>
                  <option value="none">Aucune</option>
                  <option value="block">Bloquer lot</option>
                  <option value="seize">Saisir lot</option>
                </select>
              </div>
              {actionOnLot === 'seize' && (
                <div className="form-group">
                  <label>Transferer vers acteur ID (optionnel)</label>
                  <input type="number" className="form-control" value={seizedToActorId} onChange={(e) => setSeizedToActorId(e.target.value)} />
                </div>
              )}
            </div>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </form>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <label style={{ marginRight: '0.5rem' }}>Filtrer violation case ID:</label>
        <input type="number" className="form-control" style={{ width: 160, display: 'inline-block' }} value={violationIdFilter} onChange={(e) => setViolationIdFilter(e.target.value)} />
      </div>

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste penalites</h2>
          {penalties.length === 0 ? (
            <p className="empty-state">Aucune penalite.</p>
          ) : (
            <ul className="list">
              {penalties.map((p: any) => (
                <li key={p.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">Penalite #{p.id} - {p.penalty_type}</div>
                    <div className="list-item-subtitle">
                      Violation #{p.violation_case_id} - {p.status}
                      {p.amount != null ? ` - ${p.amount} MGA` : ''}
                      {p.action_on_lot ? ` - action lot: ${p.action_on_lot}` : ''}
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
