import { useParams, Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'
import { useToast } from '../contexts/ToastContext'

export default function LotDetailPage() {
  const { id } = useParams<{ id: string }>()
  const lotId = id ? parseInt(id, 10) : NaN
  const queryClient = useQueryClient()
  const toast = useToast()

  const { data, isLoading, error } = useQuery({
    queryKey: ['lot', lotId],
    queryFn: () => api.getLot(lotId),
    enabled: Number.isInteger(lotId),
  })

  const splitMutation = useMutation({
    mutationFn: (quantities: number[]) => api.splitLot(lotId, quantities),
    onSuccess: (rows) => {
      queryClient.invalidateQueries({ queryKey: ['lot', lotId] })
      queryClient.invalidateQueries({ queryKey: ['lots'] })
      toast.success(`Lot scinde en ${rows.length} sous-lots.`)
    },
  })

  const transferMutation = useMutation({
    mutationFn: (payload: { new_owner_actor_id: number; payment_request_id: number }) =>
      api.transferLot(lotId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lot', lotId] })
      queryClient.invalidateQueries({ queryKey: ['lots'] })
      toast.success('Lot transfere.')
    },
  })
  const classifyMutation = useMutation({
    mutationFn: (payload: {
      wood_classification: 'LEGAL_EXPORTABLE' | 'LEGAL_NON_EXPORTABLE' | 'ILLEGAL' | 'A_DETRUIRE'
      cites_laf_status?: 'not_required' | 'required' | 'pending' | 'approved' | 'rejected'
      cites_ndf_status?: 'not_required' | 'required' | 'pending' | 'approved' | 'rejected'
      cites_international_status?: 'not_required' | 'required' | 'pending' | 'approved' | 'rejected'
      notes?: string
    }) => api.patchLotWoodClassification(lotId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lot', lotId] })
      queryClient.invalidateQueries({ queryKey: ['lots'] })
      toast.success('Classification bois mise a jour.')
    },
  })

  if (!Number.isInteger(lotId)) {
    return <div className="dashboard"><p className="error">ID invalide.</p><Link to="/lots">Retour</Link></div>
  }
  if (error) {
    return <div className="dashboard"><h1>Lot #{lotId}</h1><p className="error">Erreur.</p><Link to="/lots">Retour</Link></div>
  }
  if (isLoading) return <div className="loading">Chargement...</div>
  if (!data) return null

  return (
    <div className="dashboard">
      <h1>Lot #{data.id}</h1>
      <p className="dashboard-subtitle"><Link to="/lots">Retour aux lots</Link></p>
      <div className="card">
        <div className="profile-info">
          <div className="info-item"><span className="info-label">Filiere</span><span className="info-value">{data.filiere}</span></div>
          <div className="info-item"><span className="info-label">Type</span><span className="info-value">{data.product_type}</span></div>
          <div className="info-item"><span className="info-label">Quantite</span><span className="info-value">{data.quantity} {data.unit}</span></div>
          <div className="info-item"><span className="info-label">Proprietaire (ID)</span><span className="info-value">{data.current_owner_actor_id}</span></div>
          <div className="info-item"><span className="info-label">Statut</span><span className="info-value">{data.status}</span></div>
          <div className="info-item"><span className="info-label">Classification bois</span><span className="info-value">{data.wood_classification || '-'}</span></div>
          <div className="info-item"><span className="info-label">LAF</span><span className="info-value">{data.cites_laf_status || '-'}</span></div>
          <div className="info-item"><span className="info-label">NDF</span><span className="info-value">{data.cites_ndf_status || '-'}</span></div>
          <div className="info-item"><span className="info-label">Validation internationale</span><span className="info-value">{data.cites_international_status || '-'}</span></div>
          <div className="info-item"><span className="info-label">Destruction</span><span className="info-value">{data.destruction_status || '-'}</span></div>
        </div>
      </div>
      <div className="card">
        <h2>Operations</h2>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            const v1 = Number(window.prompt('Quantite 1', '0'))
            const v2 = Number(window.prompt('Quantite 2', '0'))
            if (!Number.isFinite(v1) || !Number.isFinite(v2) || v1 <= 0 || v2 <= 0) return
            splitMutation.mutate([v1, v2])
          }}
          disabled={splitMutation.isPending || data.status !== 'available'}
        >
          Scinder ce lot (2 sous-lots)
        </button>
        <button
          type="button"
          className="btn-secondary"
          style={{ marginLeft: 8 }}
          onClick={() => {
            const owner = Number(window.prompt('Nouvel owner actor_id', '0'))
            const paymentRequestId = Number(window.prompt('Payment request id (status success)', '0'))
            if (!Number.isFinite(owner) || !Number.isFinite(paymentRequestId) || owner <= 0 || paymentRequestId <= 0) return
            transferMutation.mutate({ new_owner_actor_id: owner, payment_request_id: paymentRequestId })
          }}
          disabled={transferMutation.isPending || data.status !== 'available'}
        >
          Transferer ce lot
        </button>
        <button
          type="button"
          className="btn-secondary"
          style={{ marginLeft: 8 }}
          onClick={() => {
            const nextClassification = (window.prompt(
              'Classification (LEGAL_EXPORTABLE, LEGAL_NON_EXPORTABLE, ILLEGAL, A_DETRUIRE)',
              String(data.wood_classification || 'LEGAL_NON_EXPORTABLE')
            ) || '').trim().toUpperCase()
            if (!nextClassification) return
            const laf = (window.prompt('LAF status (not_required, required, pending, approved, rejected)', String(data.cites_laf_status || 'required')) || '').trim().toLowerCase()
            const ndf = (window.prompt('NDF status (not_required, required, pending, approved, rejected)', String(data.cites_ndf_status || 'required')) || '').trim().toLowerCase()
            const intl = (window.prompt('Validation internationale (not_required, required, pending, approved, rejected)', String(data.cites_international_status || 'required')) || '').trim().toLowerCase()
            classifyMutation.mutate({
              wood_classification: nextClassification as 'LEGAL_EXPORTABLE' | 'LEGAL_NON_EXPORTABLE' | 'ILLEGAL' | 'A_DETRUIRE',
              cites_laf_status: laf as 'not_required' | 'required' | 'pending' | 'approved' | 'rejected',
              cites_ndf_status: ndf as 'not_required' | 'required' | 'pending' | 'approved' | 'rejected',
              cites_international_status: intl as 'not_required' | 'required' | 'pending' | 'approved' | 'rejected',
              notes: 'Mise a jour manuelle CITES',
            })
          }}
          disabled={classifyMutation.isPending || data.filiere !== 'BOIS'}
        >
          Mettre a jour CITES
        </button>
      </div>
    </div>
  )
}
