import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'

type CardRequestKind = 'kara_orpailleur' | 'collector_collecteur' | 'collector_bijoutier'

export default function OrCompliancePage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [requestKind, setRequestKind] = useState<CardRequestKind>('kara_orpailleur')
  const [cinInput, setCinInput] = useState('')
  const [queueStatus, setQueueStatus] = useState('pending')

  const actorId = user?.id ?? 0
  const communeId = Number((user?.commune as unknown as { id?: number } | null)?.id ?? 0)
  const [selectedCommuneId, setSelectedCommuneId] = useState<number>(communeId || 0)
  const userRoleCodes = useMemo(() => (user?.roles || []).map((r) => r.role), [user?.roles])
  const canValidateCommune = userRoleCodes.some((r) => ['admin', 'dirigeant', 'commune', 'commune_agent', 'com', 'com_admin', 'com_agent'].includes(r))
  const canTargetCommune = userRoleCodes.some((r) => ['admin', 'dirigeant', 'com', 'com_admin', 'com_agent'].includes(r))
  const { data: communes = [] } = useQuery({
    queryKey: ['territories', 'communes-all', 'or-compliance'],
    queryFn: () => api.getAllCommunes(),
    enabled: canValidateCommune,
  })

  const { data: myCards } = useQuery({
    queryKey: ['or-compliance', 'my-cards', actorId],
    queryFn: () => api.getMyOrCards(),
    enabled: !!actorId,
  })

  const { data: myFees = [] } = useQuery({
    queryKey: ['or-compliance', 'fees', actorId],
    queryFn: () => api.getFees({ actor_id: actorId }),
    enabled: !!actorId,
  })

  const { data: communeQueue = [] } = useQuery({
    queryKey: ['or-compliance', 'commune-queue', selectedCommuneId || communeId, queueStatus],
    queryFn: () => api.getCommuneCardQueue({ commune_id: selectedCommuneId || communeId, status: queueStatus }),
    enabled: canValidateCommune && !!(selectedCommuneId || communeId),
  })

  const requestMutation = useMutation({
    mutationFn: async () => {
      const targetCommune = selectedCommuneId || communeId
      if (!actorId || !targetCommune) throw new Error('Profil incomplet: commune requise')
      if (requestKind === 'kara_orpailleur') {
        return api.createKaraCard({
          actor_id: actorId,
          commune_id: targetCommune,
          cin: cinInput || user?.cin || 'CIN_NON_RENSEIGNE',
          nationality: 'mg',
          residence_verified: true,
          tax_compliant: true,
          zone_allowed: true,
          public_order_clear: true,
          notes: 'demande_orpailleur',
        })
      }
      return api.createCollectorCard({
        actor_id: actorId,
        issuing_commune_id: targetCommune,
        notes: requestKind === 'collector_bijoutier' ? 'demande_bijoutier' : 'demande_collecteur',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['or-compliance'] })
    },
  })

  const markFeePaidMutation = useMutation({
    mutationFn: (feeId: number) => api.markFeePaid(feeId, { payment_ref: `self-${Date.now()}` }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['or-compliance'] }),
  })

  const decideMutation = useMutation({
    mutationFn: async (payload: { cardType: string; cardId: number; decision: 'approved' | 'rejected' }) => {
      if (payload.cardType === 'kara_bolamena') return api.decideKaraCard(payload.cardId, payload.decision, 'decision_commune')
      return api.decideCollectorCard(payload.cardId, payload.decision, 'decision_commune')
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['or-compliance'] }),
  })

  const pendingFees = (myFees as any[]).filter((f) => f.status === 'pending')
  const karaCards = (myCards?.kara_cards || []) as any[]
  const collectorCards = (myCards?.collector_cards || []) as any[]

  const onSubmitRequest = (e: FormEvent) => {
    e.preventDefault()
    requestMutation.mutate()
  }

  return (
    <div className="dashboard">
      <h1>Demandes de cartes OR</h1>
      <p>Flux complet: demande acteur -&gt; paiement -&gt; validation commune -&gt; carte active dans le compte.</p>

      <div className="dashboard-grid">
        <div className="card">
          <h2>Nouvelle demande (acteur)</h2>
          <form onSubmit={onSubmitRequest}>
            <div className="form-group">
              <label htmlFor="request-kind">Type de carte</label>
              <select id="request-kind" value={requestKind} onChange={(e) => setRequestKind(e.target.value as CardRequestKind)}>
                <option value="kara_orpailleur">Carte orpailleur (Kara-bolamena)</option>
                <option value="collector_collecteur">Carte collecteur</option>
                <option value="collector_bijoutier">Carte collecteur (profil bijoutier)</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="cin">CIN (orpailleur)</label>
              <input id="cin" value={cinInput} onChange={(e) => setCinInput(e.target.value)} placeholder={user?.cin || 'Saisir CIN'} />
            </div>
            {canValidateCommune && (
              <div className="form-group">
                <label htmlFor="request-commune">Commune cible</label>
                <select
                  id="request-commune"
                  value={selectedCommuneId || ''}
                  onChange={(e) => setSelectedCommuneId(Number(e.target.value) || 0)}
                  disabled={!canTargetCommune}
                >
                  <option value="">-- Choisir --</option>
                  {communes.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
            )}
            <button className="btn-primary" type="submit" disabled={requestMutation.isPending || !actorId || !(selectedCommuneId || communeId)}>
              {requestMutation.isPending ? 'Envoi...' : 'Soumettre la demande'}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Mes frais a payer</h2>
          {pendingFees.length === 0 ? (
            <p>Aucun frais en attente.</p>
          ) : (
            <ul className="home-list">
              {pendingFees.map((fee: any) => (
                <li key={fee.id}>
                  #{fee.id} | {fee.fee_type} | {fee.amount} {fee.currency}
                  <button
                    className="btn-secondary"
                    style={{ marginLeft: 8 }}
                    onClick={() => markFeePaidMutation.mutate(fee.id)}
                    disabled={markFeePaidMutation.isPending}
                  >
                    Marquer paye
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h2>Mes cartes (compte acteur)</h2>
          <h3>Kara-bolamena</h3>
          <ul className="home-list">
            {karaCards.length === 0 && <li>Aucune carte kara.</li>}
            {karaCards.map((c) => <li key={c.id}>#{c.id} | {c.status} | exp={c.expires_at ?? '-'}</li>)}
          </ul>
          <h3>Cartes collecteur</h3>
          <ul className="home-list">
            {collectorCards.length === 0 && <li>Aucune carte collecteur.</li>}
            {collectorCards.map((c) => <li key={c.id}>#{c.id} | {c.status} | exp={c.expires_at ?? '-'}</li>)}
          </ul>
        </div>

        <div className="card">
          <h2>Validation Commune / Agent</h2>
          {!canValidateCommune ? (
            <p>Vous n'avez pas les droits de validation communale.</p>
          ) : (
            <>
              <div className="form-group">
                <label htmlFor="queue-status">Statut</label>
                <select id="queue-status" value={queueStatus} onChange={(e) => setQueueStatus(e.target.value)}>
                  <option value="pending">pending</option>
                  <option value="active">active</option>
                  <option value="rejected">rejected</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="queue-commune">Commune</label>
                <select
                  id="queue-commune"
                  value={selectedCommuneId || ''}
                  onChange={(e) => setSelectedCommuneId(Number(e.target.value) || 0)}
                  disabled={!canTargetCommune}
                >
                  <option value="">-- Choisir --</option>
                  {communes.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
              <ul className="home-list">
                {(communeQueue as any[]).length === 0 && <li>Aucune demande pour ce statut.</li>}
                {(communeQueue as any[]).map((item: any) => (
                  <li key={`${item.card_type}-${item.card_id}`}>
                    {item.card_type} #{item.card_id} | acteur={item.actor_name || item.actor_id} | frais={item.fee_status || '-'}
                    {item.status === 'pending' && (
                      <>
                        <button
                          className="btn-primary"
                          style={{ marginLeft: 8 }}
                          onClick={() => decideMutation.mutate({ cardType: item.card_type, cardId: item.card_id, decision: 'approved' })}
                        >
                          Valider
                        </button>
                        <button
                          className="btn-secondary"
                          style={{ marginLeft: 8 }}
                          onClick={() => decideMutation.mutate({ cardType: item.card_type, cardId: item.card_id, decision: 'rejected' })}
                        >
                          Refuser
                        </button>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
