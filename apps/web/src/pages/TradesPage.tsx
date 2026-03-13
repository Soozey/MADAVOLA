import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { getApiDetailFromError, getApiErrorMessage } from '../lib/apiErrors'
import './TransactionsPage.css'

export default function TradesPage() {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [tradeIdForPay, setTradeIdForPay] = useState('')
  const [tradeIdForConfirm, setTradeIdForConfirm] = useState('')

  const { data: actorsRaw } = useQuery({ queryKey: ['actors', 'trade', 'all'], queryFn: () => api.getActors({ page: 1, page_size: 500 }) })
  const { data: lotsRaw } = useQuery({ queryKey: ['lots', 'trade', 'all'], queryFn: () => api.getLots({ page: 1, page_size: 500 }) })
  const actors = (actorsRaw?.items ?? actorsRaw ?? []) as any[]
  const lots = (lotsRaw?.items ?? lotsRaw ?? []) as any[]

  const [line, setLine] = useState({ lot_id: 0, quantity: 0, unit_price: 0 })

  const createMutation = useMutation({
    mutationFn: (payload: any) => api.createTrade(payload),
    onSuccess: (data) => {
      toast.success(`Trade #${data.id} cree (status=${data.status})`)
      setShowForm(false)
      queryClient.invalidateQueries({ queryKey: ['lots', 'trade', 'all'] })
    },
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, 'Creation trade impossible.'))
    },
  })

  const payMutation = useMutation({
    mutationFn: (tradeId: number) => api.payTrade(tradeId, { payment_mode: 'cash_declared' }),
    onSuccess: (data) => toast.success(`Trade #${data.id} paye (status=${data.status})`),
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, 'Paiement trade impossible.'))
    },
  })

  const confirmMutation = useMutation({
    mutationFn: (tradeId: number) => api.confirmTrade(tradeId),
    onSuccess: (data) => {
      toast.success(`Trade #${data.id} confirme (status=${data.status})`)
      queryClient.invalidateQueries({ queryKey: ['lots'] })
    },
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, 'Confirmation transaction impossible.'))
    },
  })

  const sellers = useMemo(() => actors, [actors])
  const buyers = useMemo(() => actors, [actors])

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    createMutation.mutate({
      seller_actor_id: Number(fd.get('seller_actor_id')),
      buyer_actor_id: Number(fd.get('buyer_actor_id')),
      currency: 'MGA',
      items: [line],
    })
  }

  return (
    <div className="transactions-page">
      <div className="page-header">
        <h1>Transactions (workflow simplifie)</h1>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>{showForm ? 'Annuler' : '+ Nouveau trade'}</button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2>Creer trade</h2>
          <form onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-group">
                <label>Vendeur *</label>
                <select name="seller_actor_id" required defaultValue={user?.id ?? ''}>
                  <option value="">Selectionner...</option>
                  {sellers.map((a: any) => <option key={a.id} value={a.id}>{a.id} - {a.nom}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Acheteur *</label>
                <select name="buyer_actor_id" required>
                  <option value="">Selectionner...</option>
                  {buyers.map((a: any) => <option key={a.id} value={a.id}>{a.id} - {a.nom}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Lot *</label>
                <select value={line.lot_id || ''} onChange={(e) => setLine((p) => ({ ...p, lot_id: Number(e.target.value) }))} required>
                  <option value="">Selectionner...</option>
                  {lots.map((l: any) => <option key={l.id} value={l.id}>Lot #{l.id} - {l.filiere} - {l.quantity} {l.unit}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Quantite *</label>
                <input type="number" min="0.0001" step="0.0001" value={line.quantity || ''} onChange={(e) => setLine((p) => ({ ...p, quantity: Number(e.target.value) }))} required />
              </div>
              <div className="form-group">
                <label>Prix unitaire *</label>
                <input type="number" min="0" step="0.01" value={line.unit_price || ''} onChange={(e) => setLine((p) => ({ ...p, unit_price: Number(e.target.value) }))} required />
              </div>
            </div>
            <div className="form-actions"><button className="btn-primary" type="submit" disabled={createMutation.isPending}>Creer trade</button></div>
          </form>
        </div>
      )}

      <div className="card form-card">
        <h2>Payer transaction (cash declare)</h2>
        <div className="form-grid">
          <div className="form-group"><label>ID transaction</label><input value={tradeIdForPay} onChange={(e) => setTradeIdForPay(e.target.value)} /></div>
        </div>
        <div className="form-actions"><button className="btn-secondary" onClick={() => payMutation.mutate(Number(tradeIdForPay))} disabled={!tradeIdForPay || payMutation.isPending}>Payer</button></div>
      </div>

      <div className="card form-card">
        <h2>Confirmer transfert transaction</h2>
        <div className="form-grid">
          <div className="form-group"><label>ID transaction</label><input value={tradeIdForConfirm} onChange={(e) => setTradeIdForConfirm(e.target.value)} /></div>
        </div>
        <div className="form-actions"><button className="btn-primary" onClick={() => confirmMutation.mutate(Number(tradeIdForConfirm))} disabled={!tradeIdForConfirm || confirmMutation.isPending}>Confirmer</button></div>
      </div>
    </div>
  )
}
