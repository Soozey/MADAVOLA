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
  ready_for_control: 'Pret controle',
  controlled: 'Controle',
  sealed: 'Scelle',
  exported: 'Exporte',
  approved: 'Approuve',
  rejected: 'Rejete',
}

export default function ExportsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [destination, setDestination] = useState('')
  const [destinationCountry, setDestinationCountry] = useState('')
  const [transportMode, setTransportMode] = useState('road')
  const [totalWeight, setTotalWeight] = useState('')
  const [declaredValue, setDeclaredValue] = useState('')
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
        destination_country: destinationCountry || undefined,
        transport_mode: transportMode || undefined,
        total_weight: totalWeight ? parseFloat(totalWeight) : undefined,
        declared_value: declaredValue ? parseFloat(declaredValue) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      setShowForm(false)
      setDestination('')
      setDestinationCountry('')
      setTransportMode('road')
      setTotalWeight('')
      setDeclaredValue('')
      toast.success('Dossier export cree.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la creation.')),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.updateExportStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      toast.success('Statut mis a jour.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Erreur lors de la mise a jour.')),
  })

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Dossiers export</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouveau dossier'}
        </button>
      </div>
      <p className="dashboard-subtitle">
        Comptoir: creation dossier, lien lots, preparation, controle, scellement, export.
      </p>

      {showForm && (
        <div className="card form-card">
          <h2>Creer un dossier export</h2>
          <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate() }}>
            <div className="form-grid">
              <div className="form-group">
                <label>Destination</label>
                <input type="text" className="form-control" value={destination} onChange={(e) => setDestination(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Pays destination</label>
                <input type="text" className="form-control" value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Mode transport</label>
                <select className="form-control" value={transportMode} onChange={(e) => setTransportMode(e.target.value)}>
                  <option value="road">Routier</option>
                  <option value="air">Aerien</option>
                  <option value="sea">Maritime</option>
                </select>
              </div>
              <div className="form-group">
                <label>Poids total (kg)</label>
                <input type="number" step="0.01" className="form-control" value={totalWeight} onChange={(e) => setTotalWeight(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Valeur declaree</label>
                <input type="number" step="0.01" className="form-control" value={declaredValue} onChange={(e) => setDeclaredValue(e.target.value)} />
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creation...' : 'Creer dossier'}
            </button>
          </form>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <label style={{ marginRight: '0.5rem' }}>Filtre statut:</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="form-control" style={{ width: 'auto', display: 'inline-block', minWidth: 180 }}>
          <option value="">Tous</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="loading">Chargement...</div>}
      {!isLoading && (
        <div className="card">
          <h2>Liste dossiers</h2>
          {exportsList.length === 0 ? (
            <p className="empty-state">Aucun dossier export.</p>
          ) : (
            <ul className="list">
              {exportsList.map((exp: any) => (
                <li key={exp.id} className="list-item">
                  <div className="list-item-content" style={{ flex: 1 }}>
                    <div className="list-item-title">
                      {exp.dossier_number ?? `Dossier #${exp.id}`} - {exp.destination || 'Sans destination'}
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>
                        {STATUS_LABELS[exp.status] ?? exp.status}
                      </span>
                    </div>
                    <div className="list-item-subtitle">
                      Acteur #{exp.created_by_actor_id}
                      {exp.destination_country ? ` - ${exp.destination_country}` : ''}
                      {exp.transport_mode ? ` - ${exp.transport_mode}` : ''}
                      {exp.total_weight != null ? ` - ${exp.total_weight} kg` : ''}
                      {exp.declared_value != null ? ` - ${exp.declared_value}` : ''}
                      {exp.sealed_qr ? ` - QR ${exp.sealed_qr}` : ''}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    {exp.status === 'draft' && <button type="button" className="btn-secondary" onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'submitted' })}>Soumettre</button>}
                    {exp.status === 'submitted' && <button type="button" className="btn-secondary" onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'ready_for_control' })}>Pret controle</button>}
                    {exp.status === 'ready_for_control' && <button type="button" className="btn-secondary" onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'controlled' })}>Marquer controle</button>}
                    {exp.status === 'controlled' && <button type="button" className="btn-secondary" onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'sealed' })}>Sceller</button>}
                    {exp.status === 'sealed' && <button type="button" className="btn-primary" onClick={() => updateStatusMutation.mutate({ id: exp.id, status: 'exported' })}>Exporter</button>}
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
