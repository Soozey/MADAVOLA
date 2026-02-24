import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'

type WalletProvider = 'mobile_money' | 'bank' | 'card'

export default function AccountOpsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const toast = useToast()
  const actorId = user?.id ?? 0
  const userCommuneId = Number((user?.commune as unknown as { id?: number } | null)?.id ?? 0)

  const roleCodes = useMemo(() => (user?.roles || []).map((r) => r.role), [user?.roles])
  const canManageCommuneProfile = roleCodes.some((r) =>
    ['admin', 'dirigeant', 'commune', 'commune_agent', 'com', 'com_admin', 'com_agent'].includes(r)
  )
  const canTargetAnyCommune = roleCodes.some((r) => ['admin', 'dirigeant', 'com', 'com_admin', 'com_agent'].includes(r))

  const [selectedCommuneId, setSelectedCommuneId] = useState<number>(userCommuneId || 0)
  const [kycPieces, setKycPieces] = useState('')
  const [kycNote, setKycNote] = useState('')
  const [walletProvider, setWalletProvider] = useState<WalletProvider>('mobile_money')
  const [walletOperator, setWalletOperator] = useState('mvola')
  const [walletRef, setWalletRef] = useState('')
  const [walletPrimary, setWalletPrimary] = useState(true)
  const [communeAccountRef, setCommuneAccountRef] = useState('')
  const [communeReceiverName, setCommuneReceiverName] = useState('')
  const [communeReceiverPhone, setCommuneReceiverPhone] = useState('')
  const [communeActive, setCommuneActive] = useState(true)

  const { data: communes = [] } = useQuery({
    queryKey: ['territories', 'communes-all', 'account-ops'],
    queryFn: () => api.getAllCommunes(),
    enabled: canManageCommuneProfile,
  })

  const { data: kycs = [] } = useQuery({
    queryKey: ['account-ops', 'kyc', actorId],
    queryFn: () => api.getActorKyc(actorId),
    enabled: !!actorId,
  })

  const { data: wallets = [] } = useQuery({
    queryKey: ['account-ops', 'wallets', actorId],
    queryFn: () => api.getActorWallets(actorId),
    enabled: !!actorId,
  })

  const effectiveCommuneId = selectedCommuneId || userCommuneId
  const { data: communeProfile } = useQuery({
    queryKey: ['account-ops', 'commune-profile', effectiveCommuneId],
    queryFn: async () => {
      const out = await api.getCommuneProfile(effectiveCommuneId)
      setCommuneAccountRef(out.mobile_money_account_ref || '')
      setCommuneReceiverName(out.receiver_name || '')
      setCommuneReceiverPhone(out.receiver_phone || '')
      setCommuneActive(Boolean(out.active))
      return out
    },
    enabled: canManageCommuneProfile && !!effectiveCommuneId,
  })

  const kycMutation = useMutation({
    mutationFn: () =>
      api.createActorKyc(actorId, {
        pieces: kycPieces
          .split(',')
          .map((x) => x.trim())
          .filter(Boolean),
        note: kycNote || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account-ops', 'kyc', actorId] })
      setKycPieces('')
      setKycNote('')
      toast.success('KYC ajouté.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Ajout KYC impossible.')),
  })

  const walletMutation = useMutation({
    mutationFn: () =>
      api.createActorWallet(actorId, {
        provider: walletProvider,
        operator_name: walletOperator || undefined,
        account_ref: walletRef,
        is_primary: walletPrimary,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account-ops', 'wallets', actorId] })
      setWalletRef('')
      toast.success('Wallet ajouté.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Ajout wallet impossible.')),
  })

  const communeProfileMutation = useMutation({
    mutationFn: () =>
      api.patchCommuneProfile(effectiveCommuneId, {
        mobile_money_account_ref: communeAccountRef || undefined,
        receiver_name: communeReceiverName || undefined,
        receiver_phone: communeReceiverPhone || undefined,
        active: communeActive,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account-ops', 'commune-profile', effectiveCommuneId] })
      toast.success('Profil commune mis à jour.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Mise à jour profil commune impossible.')),
  })

  const onSubmitKyc = (e: FormEvent) => {
    e.preventDefault()
    if (!actorId) return
    if (!kycPieces.trim()) {
      toast.error('Au moins une pièce est obligatoire.')
      return
    }
    kycMutation.mutate()
  }

  const onSubmitWallet = (e: FormEvent) => {
    e.preventDefault()
    if (!actorId || !walletRef.trim()) return
    walletMutation.mutate()
  }

  const onSubmitCommuneProfile = (e: FormEvent) => {
    e.preventDefault()
    if (!effectiveCommuneId) return
    communeProfileMutation.mutate()
  }

  return (
    <div className="dashboard">
      <h1>KYC, wallets et profil commune</h1>
      <p className="dashboard-subtitle">Écrans métier dédiés pour ActorKYC, ActorWallet et CommuneProfile.</p>

      <div className="dashboard-grid">
        <div className="card">
          <h2>KYC acteur</h2>
          <form onSubmit={onSubmitKyc}>
            <div className="form-group">
              <label>Pièces (CSV)</label>
              <input
                value={kycPieces}
                onChange={(e) => setKycPieces(e.target.value)}
                placeholder="cin_recto.jpg,cin_verso.jpg,selfie.jpg"
              />
            </div>
            <div className="form-group">
              <label>Note</label>
              <input value={kycNote} onChange={(e) => setKycNote(e.target.value)} />
            </div>
            <button className="btn-primary" type="submit" disabled={kycMutation.isPending || !actorId}>
              {kycMutation.isPending ? 'Enregistrement...' : 'Ajouter KYC'}
            </button>
          </form>
          <ul className="home-list" style={{ marginTop: '1rem' }}>
            {(kycs as any[]).length === 0 && <li>Aucun KYC.</li>}
            {(kycs as any[]).map((k: any) => (
              <li key={k.id}>
                #{k.id} | pièces={Array.isArray(k.pieces) ? k.pieces.join(', ') : ''} | note={k.note || '-'}
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2>Wallets acteur</h2>
          <form onSubmit={onSubmitWallet}>
            <div className="form-group">
              <label>Canal</label>
              <select value={walletProvider} onChange={(e) => setWalletProvider(e.target.value as WalletProvider)}>
                <option value="mobile_money">mobile_money</option>
                <option value="bank">bank</option>
                <option value="card">card</option>
              </select>
            </div>
            <div className="form-group">
              <label>Opérateur</label>
              <input value={walletOperator} onChange={(e) => setWalletOperator(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Référence compte</label>
              <input value={walletRef} onChange={(e) => setWalletRef(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>
                <input type="checkbox" checked={walletPrimary} onChange={(e) => setWalletPrimary(e.target.checked)} /> Wallet principal
              </label>
            </div>
            <button className="btn-primary" type="submit" disabled={walletMutation.isPending || !actorId}>
              {walletMutation.isPending ? 'Enregistrement...' : 'Ajouter wallet'}
            </button>
          </form>
          <ul className="home-list" style={{ marginTop: '1rem' }}>
            {(wallets as any[]).length === 0 && <li>Aucun wallet.</li>}
            {(wallets as any[]).map((w: any) => (
              <li key={w.id}>
                #{w.id} | {w.provider} | {w.account_ref} {w.is_primary ? '(principal)' : ''}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        <h2>Profil commune</h2>
        {!canManageCommuneProfile ? (
          <p>RBAC: réservé aux rôles Commune/COM/Admin.</p>
        ) : !effectiveCommuneId ? (
          <p>Aucune commune liée au compte.</p>
        ) : (
          <form onSubmit={onSubmitCommuneProfile}>
            {canTargetAnyCommune && (
              <div className="form-group">
                <label htmlFor="commune-target">Commune cible</label>
                <select
                  id="commune-target"
                  value={selectedCommuneId || ''}
                  onChange={(e) => setSelectedCommuneId(Number(e.target.value) || 0)}
                >
                  <option value="">-- Choisir --</option>
                  {(communes as any[]).map((c: any) => (
                    <option key={c.id} value={c.id}>
                      {c.code} - {c.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div className="form-grid">
              <div className="form-group">
                <label>Référence compte Mobile Money</label>
                <input value={communeAccountRef} onChange={(e) => setCommuneAccountRef(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Nom du receveur</label>
                <input value={communeReceiverName} onChange={(e) => setCommuneReceiverName(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Téléphone receveur</label>
                <input value={communeReceiverPhone} onChange={(e) => setCommuneReceiverPhone(e.target.value)} />
              </div>
              <div className="form-group">
                <label>
                  <input type="checkbox" checked={communeActive} onChange={(e) => setCommuneActive(e.target.checked)} /> Profil actif
                </label>
              </div>
            </div>
            <button className="btn-primary" type="submit" disabled={communeProfileMutation.isPending}>
              {communeProfileMutation.isPending ? 'Mise à jour...' : 'Mettre à jour le profil commune'}
            </button>
          </form>
        )}
        {communeProfile && (
          <p style={{ marginTop: '0.75rem' }}>
            Profil actuel: {communeProfile.receiver_name || '-'} / {communeProfile.receiver_phone || '-'} / {communeProfile.mobile_money_account_ref || '-'}
          </p>
        )}
      </div>
    </div>
  )
}
