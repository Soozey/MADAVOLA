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
  const [destinationCommuneId, setDestinationCommuneId] = useState('')
  const [destinationCountry, setDestinationCountry] = useState('')
  const [transportMode, setTransportMode] = useState('road')
  const [totalWeight, setTotalWeight] = useState('')
  const [declaredValue, setDeclaredValue] = useState('')
  const [selectedExportId, setSelectedExportId] = useState<number | null>(null)
  const [linkLotId, setLinkLotId] = useState('')
  const [linkQty, setLinkQty] = useState('')
  const [validateStep, setValidateStep] = useState<'mines' | 'douanes'>('mines')
  const [validateDecision, setValidateDecision] = useState<'approved' | 'rejected'>('approved')
  const [sealNumber, setSealNumber] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data: exportsList = [], isLoading } = useQuery({
    queryKey: ['exports', statusFilter],
    queryFn: () => api.getExports(statusFilter ? { status: statusFilter } : undefined),
  })
  const { data: communes = [] } = useQuery({
    queryKey: ['territories', 'communes-all', 'exports'],
    queryFn: () => api.getAllCommunes(),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      api.createExport({
        destination: destination || undefined,
        destination_commune_id: destinationCommuneId ? Number(destinationCommuneId) : undefined,
        destination_country: destinationCountry || undefined,
        transport_mode: transportMode || undefined,
        total_weight: totalWeight ? parseFloat(totalWeight) : undefined,
        declared_value: declaredValue ? parseFloat(declaredValue) : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      setShowForm(false)
      setDestination('')
      setDestinationCommuneId('')
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
  const { data: lotsData } = useQuery({
    queryKey: ['lots', 'for-export'],
    queryFn: () => api.getLots({ page: 1, page_size: 500 }),
  })
  const { data: checklistData = [] } = useQuery({
    queryKey: ['or-export-checklist', selectedExportId],
    queryFn: () => api.getOrExportChecklist(selectedExportId as number),
    enabled: !!selectedExportId,
  })
  const { data: selectedExportDetail } = useQuery({
    queryKey: ['export-detail', selectedExportId],
    queryFn: () => api.getExport(selectedExportId as number),
    enabled: !!selectedExportId,
  })
  const linkLotMutation = useMutation({
    mutationFn: () =>
      api.linkLotsToExport(selectedExportId as number, [
        { lot_id: Number(linkLotId), quantity_in_export: Number(linkQty) },
      ]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      toast.success('Lot lie au dossier.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Lien lot impossible.')),
  })
  const submitMutation = useMutation({
    mutationFn: () => api.submitExport(selectedExportId as number),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      toast.success('Dossier soumis.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Soumission impossible.')),
  })
  const validateMutation = useMutation({
    mutationFn: () =>
      api.validateExportStep(selectedExportId as number, {
        step_code: validateStep,
        decision: validateDecision,
        seal_number: validateStep === 'douanes' && validateDecision === 'approved' ? sealNumber || undefined : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
      toast.success('Validation enregistree.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Validation impossible.')),
  })
  const verifyChecklistMutation = useMutation({
    mutationFn: (itemId: number) => api.verifyOrExportChecklistItem(selectedExportId as number, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['or-export-checklist', selectedExportId] })
      toast.success('Checklist verifiee.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Verification checklist impossible.')),
  })

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Dossiers export</h1>
      </div>
      <p className="dashboard-subtitle">
        Comptoir: creation dossier, lien lots, preparation, controle, scellement, export.
      </p>
      <div className="card tasks-of-day">
        <h2>Taches du jour</h2>
        <p className="process-label">
          Creez le dossier export en priorite, puis completez les lots et les etapes de validation.
        </p>
        <div className="tasks-actions">
          <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Annuler la creation' : 'Creer un dossier export'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => document.getElementById('exports-list')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Voir la liste des dossiers
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => document.getElementById('exports-advanced')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Operations avancees
          </button>
        </div>
      </div>

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
                <label>Destination locale (commune)</label>
                <select className="form-control" value={destinationCommuneId} onChange={(e) => setDestinationCommuneId(e.target.value)}>
                  <option value="">-- Aucune --</option>
                  {communes.map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.code} - {c.name}
                    </option>
                  ))}
                </select>
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
            <button
              type="submit"
              className="btn-primary"
              disabled={createMutation.isPending || (transportMode === 'road' && !destinationCommuneId)}
            >
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
        <div id="exports-list" className="card">
          <h2>Liste dossiers</h2>
          {exportsList.length === 0 ? (
            <p className="empty-state">Aucun dossier export.</p>
          ) : (
            <ul className="list">
              {exportsList.map((exp: any) => (
                <li key={exp.id} className="list-item">
                  <div className="list-item-content" style={{ flex: 1 }}>
                    <div className="list-item-title">
                      {(exp.dossier_number || `Dossier #${exp.id}`)} - {exp.destination || 'Sans destination'}
                      <span className="badge badge-default" style={{ marginLeft: '0.5rem' }}>
                        {STATUS_LABELS[exp.status] || exp.status}
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
                    <button type="button" className="btn-secondary" onClick={() => setSelectedExportId(exp.id)}>Voir detail</button>
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
      <div id="exports-advanced" className="card form-card" style={{ marginTop: '1rem' }}>
        <h2>Operations avancees dossier</h2>
        <div className="form-grid">
          <div className="form-group">
            <label>Dossier cible</label>
            <select value={selectedExportId ?? ''} onChange={(e) => setSelectedExportId(e.target.value ? Number(e.target.value) : null)}>
              <option value="">Selectionner...</option>
              {(exportsList as any[]).map((exp: any) => (
                <option key={exp.id} value={exp.id}>{exp.dossier_number || `#${exp.id}`} ({exp.status})</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Lot a lier</label>
            <select value={linkLotId} onChange={(e) => setLinkLotId(e.target.value)}>
              <option value="">Selectionner...</option>
              {(lotsData?.items ?? []).map((lot: any) => (
                <option key={lot.id} value={lot.id}>Lot #{lot.id} - {lot.filiere} - {lot.quantity} {lot.unit}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Quantite export</label>
            <input value={linkQty} onChange={(e) => setLinkQty(e.target.value)} />
          </div>
        </div>
        <div className="form-actions" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button className="btn-secondary" onClick={() => linkLotMutation.mutate()} disabled={!selectedExportId || !linkLotId || !linkQty}>Lier lot</button>
          <button className="btn-secondary" onClick={() => submitMutation.mutate()} disabled={!selectedExportId}>Soumettre dossier</button>
        </div>
        <div className="form-grid" style={{ marginTop: '0.75rem' }}>
          <div className="form-group">
            <label>Etape validation</label>
            <select value={validateStep} onChange={(e) => setValidateStep(e.target.value as 'mines' | 'douanes')}>
              <option value="mines">mines</option>
              <option value="douanes">douanes</option>
            </select>
          </div>
          <div className="form-group">
            <label>Decision</label>
            <select value={validateDecision} onChange={(e) => setValidateDecision(e.target.value as 'approved' | 'rejected')}>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
            </select>
          </div>
          <div className="form-group">
            <label>Seal number (douanes approved)</label>
            <input value={sealNumber} onChange={(e) => setSealNumber(e.target.value)} />
          </div>
        </div>
        <div className="form-actions">
          <button className="btn-primary" onClick={() => validateMutation.mutate()} disabled={!selectedExportId}>Valider etape</button>
        </div>
        {selectedExportId && (
          <div style={{ marginTop: '1rem' }}>
            <h3>Checklist OR (si applicable)</h3>
            {Array.isArray(checklistData) && checklistData.length > 0 ? (
              <ul className="list">
                {checklistData.map((item: any) => (
                  <li key={item.id} className="list-item">
                    <div className="list-item-content">
                      <div className="list-item-title">{item.doc_type} ({item.status})</div>
                    </div>
                    <button className="btn-secondary" onClick={() => verifyChecklistMutation.mutate(item.id)} disabled={item.status === 'verified'}>Verifier</button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-state">Aucune checklist OR sur ce dossier.</p>
            )}
          </div>
        )}
      </div>
      {selectedExportDetail && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h2>Detail dossier export #{selectedExportDetail.id}</h2>
          <div className="profile-info">
            <div className="info-item"><span className="info-label">Numero</span><span className="info-value">{selectedExportDetail.dossier_number || '-'}</span></div>
            <div className="info-item"><span className="info-label">Statut</span><span className="info-value">{selectedExportDetail.status}</span></div>
            <div className="info-item"><span className="info-label">Destination</span><span className="info-value">{selectedExportDetail.destination || '-'}</span></div>
            <div className="info-item"><span className="info-label">Pays</span><span className="info-value">{selectedExportDetail.destination_country || '-'}</span></div>
            <div className="info-item"><span className="info-label">Transport</span><span className="info-value">{selectedExportDetail.transport_mode || '-'}</span></div>
            <div className="info-item"><span className="info-label">Poids</span><span className="info-value">{selectedExportDetail.total_weight ?? '-'}</span></div>
            <div className="info-item"><span className="info-label">Valeur</span><span className="info-value">{selectedExportDetail.declared_value ?? '-'}</span></div>
            <div className="info-item"><span className="info-label">QR scelle</span><span className="info-value">{selectedExportDetail.sealed_qr || '-'}</span></div>
          </div>
        </div>
      )}
    </div>
  )
}
