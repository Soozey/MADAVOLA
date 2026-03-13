import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'

export default function FeeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const feeId = Number(id)
  const queryClient = useQueryClient()
  const toast = useToast()
  const [providerCode, setProviderCode] = useState('mvola')
  const [externalRef, setExternalRef] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['fee', feeId],
    queryFn: () => api.getFee(feeId),
    enabled: Number.isFinite(feeId) && feeId > 0,
  })

  const paymentMutation = useMutation({
    mutationFn: () => api.initiateFeePayment(feeId, { provider_code: providerCode, external_ref: externalRef || undefined }),
    onSuccess: (out) => {
      toast.success(`Paiement initie: requete #${out.payment_request_id}`)
      queryClient.invalidateQueries({ queryKey: ['fee', feeId] })
    },
    onError: (e) => toast.error(getErrorMessage(e, 'Echec initiation paiement')),
  })

  const statusMutation = useMutation({
    mutationFn: (status: 'pending' | 'paid' | 'cancelled') => api.updateFeeStatus(feeId, status),
    onSuccess: () => {
      toast.success('Statut frais mis a jour')
      queryClient.invalidateQueries({ queryKey: ['fee', feeId] })
      queryClient.invalidateQueries({ queryKey: ['fees'] })
    },
    onError: (e) => toast.error(getErrorMessage(e, 'Mise a jour statut impossible')),
  })

  const canInitiate = useMemo(() => data?.status === 'pending', [data?.status])

  if (!Number.isFinite(feeId) || feeId <= 0) {
    return <div className="dashboard"><p className="error">ID frais invalide.</p></div>
  }
  if (isLoading) return <div className="loading">Chargement...</div>
  if (isError || !data) {
    return <div className="dashboard"><p className="error">Frais introuvable ou acces refuse.</p></div>
  }

  return (
    <div className="dashboard">
      <h1>Frais #{data.id}</h1>
      <p className="dashboard-subtitle"><Link to="/actors">Retour acteurs</Link></p>
      <div className="card">
        <div className="profile-info">
          <div className="info-item"><span className="info-label">Type</span><span className="info-value">{data.fee_type}</span></div>
          <div className="info-item"><span className="info-label">Acteur ID</span><span className="info-value">{data.actor_id}</span></div>
          <div className="info-item"><span className="info-label">Commune ID</span><span className="info-value">{data.commune_id}</span></div>
          <div className="info-item"><span className="info-label">Montant</span><span className="info-value">{data.amount} {data.currency}</span></div>
          <div className="info-item"><span className="info-label">Statut</span><span className="info-value">{data.status}</span></div>
          <div className="info-item"><span className="info-label">MSISDN commune</span><span className="info-value">{data.commune_mobile_money_msisdn || '-'}</span></div>
        </div>
      </div>

      <div className="card">
        <h2>Paiement</h2>
        <div className="form-grid">
          <div className="form-group">
            <label>Provider</label>
            <select value={providerCode} onChange={(e) => setProviderCode(e.target.value)}>
              <option value="mvola">Mvola</option>
              <option value="orange_money">Orange Money</option>
              <option value="airtel_money">Airtel Money</option>
            </select>
          </div>
          <div className="form-group">
            <label>Reference externe</label>
            <input value={externalRef} onChange={(e) => setExternalRef(e.target.value)} placeholder={`fee-${feeId}`} />
          </div>
        </div>
        <div className="form-actions">
          <button type="button" className="btn-primary" onClick={() => paymentMutation.mutate()} disabled={!canInitiate || paymentMutation.isPending}>
            {paymentMutation.isPending ? 'Traitement...' : 'Initier paiement'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => statusMutation.mutate('paid')} disabled={statusMutation.isPending}>Marquer paye</button>
          <button type="button" className="btn-secondary" onClick={() => statusMutation.mutate('cancelled')} disabled={statusMutation.isPending}>Annuler</button>
        </div>
      </div>
    </div>
  )
}

