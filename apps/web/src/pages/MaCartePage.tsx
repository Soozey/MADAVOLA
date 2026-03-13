import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { QRCodeSVG } from 'qrcode.react'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import './DashboardPage.css'
import './MaCartePage.css'

type CardRow = {
  id: number
  card_type: 'kara_bolamena' | 'collector_card'
  role_label: string
  status: string
  card_number?: string
  commune_id: number
  fee_id?: number
  validated_at?: string
  expires_at?: string
  qr_value?: string
  front_document_id?: number
  back_document_id?: number
}

const statusLabel: Record<string, string> = {
  draft: 'Brouillon',
  pending_payment: 'Paiement en attente',
  pending_validation: 'Validation commune en attente',
  validated: 'Validée',
  rejected: 'Refusée',
  expired: 'Expirée',
  suspended: 'Suspendue',
  revoked: 'Révoquée',
}

export default function MaCartePage() {
  const { user } = useAuth()
  const [activeSide, setActiveSide] = useState<'front' | 'back'>('front')
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const photoInputRef = useRef<HTMLInputElement | null>(null)

  const meQuery = useQuery({
    queryKey: ['actor-detail', user?.id],
    queryFn: () => api.getActor(user!.id),
    enabled: !!user?.id,
  })
  const cardsQuery = useQuery({
    queryKey: ['my-cards-v2', user?.id],
    queryFn: () => api.getMyOrCards(),
    enabled: !!user?.id,
  })
  const feesQuery = useQuery({
    queryKey: ['my-fees-cards', user?.id],
    queryFn: () => api.getFees({ actor_id: user!.id }),
    enabled: !!user?.id,
  })

  const allCards = useMemo<CardRow[]>(() => {
    const kara = (cardsQuery.data?.kara_cards || []).map((card: any) => ({
      id: card.id,
      card_type: 'kara_bolamena' as const,
      role_label: 'Orpailleur',
      status: String(card.status || 'pending_payment'),
      card_number: card.card_number,
      commune_id: card.commune_id,
      fee_id: card.fee_id,
      validated_at: card.validated_at,
      expires_at: card.expires_at,
      qr_value: card.qr_value,
      front_document_id: card.front_document_id,
      back_document_id: card.back_document_id,
    }))
    const collector = (cardsQuery.data?.collector_cards || []).map((card: any) => ({
      id: card.id,
      card_type: 'collector_card' as const,
      role_label: card.role === 'bijoutier' ? 'Bijoutier' : 'Collecteur',
      status: String(card.status || 'pending_payment'),
      card_number: card.card_number,
      commune_id: card.issuing_commune_id,
      fee_id: card.fee_id,
      validated_at: card.validated_at,
      expires_at: card.expires_at,
      qr_value: card.qr_value,
      front_document_id: card.front_document_id,
      back_document_id: card.back_document_id,
    }))
    return [...kara, ...collector].sort((a, b) => b.id - a.id)
  }, [cardsQuery.data])

  const selectedCard = useMemo(() => {
    if (allCards.length === 0) return null
    const found = allCards.find((c) => c.id === selectedCardId)
    return found || allCards[0]
  }, [allCards, selectedCardId])

  const selectedFee = useMemo(() => {
    if (!selectedCard?.fee_id) return null
    const fees = Array.isArray(feesQuery.data) ? feesQuery.data : []
    return fees.find((f: any) => f.id === selectedCard.fee_id) || null
  }, [selectedCard, feesQuery.data])

  const communeCode = user?.commune?.code || meQuery.data?.commune_code || '-'
  const fullName = `${meQuery.data?.nom || user?.nom || ''} ${meQuery.data?.prenoms || user?.prenoms || ''}`.trim()
  const photoUrl = meQuery.data?.photo_profile_url
    ? meQuery.data.photo_profile_url.startsWith('/api/')
      ? meQuery.data.photo_profile_url
      : `/api${meQuery.data.photo_profile_url}`
    : ''

  const requestCard = async (cardType: 'kara_bolamena' | 'collector_card' | 'bijoutier_card') => {
    if (!user) return
    const communeId = Number((user as any)?.commune?.id || selectedCard?.commune_id || 0)
    if (!communeId) {
      setMessage('Impossible de créer la carte: commune non rattachée au profil.')
      return
    }
    setBusy(true)
    setMessage('')
    try {
      const card = await api.requestCard({
        card_type: cardType,
        actor_id: user.id,
        commune_id: communeId,
        cin: meQuery.data?.cin || user.cin || undefined,
      })
      setSelectedCardId(card.id)
      await Promise.all([cardsQuery.refetch(), feesQuery.refetch()])
      setMessage('Demande de carte créée.')
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message || 'Impossible de créer la demande.')
    } finally {
      setBusy(false)
    }
  }

  const payOpeningFee = async () => {
    if (!selectedCard?.fee_id) return
    setBusy(true)
    setMessage('')
    try {
      await api.markFeePaid(selectedCard.fee_id)
      await Promise.all([cardsQuery.refetch(), feesQuery.refetch()])
      setMessage('Paiement enregistré. La carte passe en attente de validation commune.')
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message || 'Paiement impossible.')
    } finally {
      setBusy(false)
    }
  }

  const downloadDocument = async (documentId?: number) => {
    if (!documentId) return
    try {
      const file = await api.downloadDocumentFile(documentId)
      const url = URL.createObjectURL(file.blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = file.filename
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message || 'Téléchargement impossible.')
    }
  }

  const uploadPhoto = async (file: File | null) => {
    if (!user || !file) return
    setBusy(true)
    setMessage('')
    try {
      await api.uploadActorPhoto(user.id, file)
      await meQuery.refetch()
      setMessage('Photo de carte mise à jour.')
    } catch (error: any) {
      setMessage(error?.response?.data?.detail?.message || 'Upload photo impossible.')
    } finally {
      setBusy(false)
    }
  }

  if (!user) return <div className="dashboard"><p className="error">Session non disponible.</p></div>

  return (
    <div className="dashboard">
      <h1>Ma carte</h1>
      <p className="dashboard-subtitle">Carte recto/verso, statut de validation commune, QR vérifiable et documents téléchargeables.</p>

      {message && <p className={message.includes('impossible') ? 'error' : 'success'}>{message}</p>}

      <div className="home-grid" style={{ gridTemplateColumns: 'minmax(340px, 480px) minmax(280px, 1fr)' }}>
        <div className="card">
          {!selectedCard && (
            <>
              <h2>Aucune carte active</h2>
              <p>Créez votre demande de carte métier pour lancer le circuit paiement - validation commune - QR.</p>
              <div className="session-actions" style={{ justifyContent: 'flex-start', flexWrap: 'wrap' }}>
                <button className="btn-primary" disabled={busy} onClick={() => requestCard('kara_bolamena')}>
                  Demander carte orpailleur
                </button>
                <button className="btn-secondary" disabled={busy} onClick={() => requestCard('collector_card')}>
                  Demander carte collecteur
                </button>
                <button className="btn-secondary" disabled={busy} onClick={() => requestCard('bijoutier_card')}>
                  Demander carte bijoutier
                </button>
              </div>
            </>
          )}

          {selectedCard && (
            <>
              <div className="session-actions" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h2 style={{ marginBottom: 0 }}>Carte {selectedCard.role_label}</h2>
                <span className={`status-badge status-${selectedCard.status}`}>{statusLabel[selectedCard.status] || selectedCard.status}</span>
              </div>
              <input
                ref={photoInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={(event) => uploadPhoto(event.target.files?.[0] || null)}
              />

              {activeSide === 'front' ? (
                <div className="card" style={{ border: '1px solid #dbe6f7', boxShadow: 'none' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '96px 1fr', gap: 16, alignItems: 'start' }}>
                    <div>
                      {photoUrl ? (
                        <img src={photoUrl} alt="Photo profil" style={{ width: 96, height: 120, objectFit: 'cover', borderRadius: 8 }} />
                      ) : (
                        <div style={{ width: 96, height: 120, borderRadius: 8, background: '#e7edf7', display: 'grid', placeItems: 'center', color: '#415575' }}>
                          Photo
                        </div>
                      )}
                    </div>
                    <div>
                      <p><strong>{fullName || `Acteur #${user.id}`}</strong></p>
                      <p>Carte: <strong>{selectedCard.card_number || `#${selectedCard.id}`}</strong></p>
                      <p>Rôle: {selectedCard.role_label}</p>
                      <p>Filière: OR</p>
                      <p>Commune: {communeCode}</p>
                      <p>Validation: {selectedCard.validated_at ? new Date(selectedCard.validated_at).toLocaleString() : '-'}</p>
                      <p>Expiration: {selectedCard.expires_at ? new Date(selectedCard.expires_at).toLocaleDateString() : '-'}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="card" style={{ border: '1px solid #dbe6f7', boxShadow: 'none', textAlign: 'center' }}>
                  <QRCodeSVG value={selectedCard.qr_value || String(selectedCard.id)} size={220} includeMargin />
                  <p style={{ marginTop: 12 }}><strong>{selectedCard.card_number || `#${selectedCard.id}`}</strong></p>
                  <p className="carte-qr-hint">Le QR contient le hash et la signature de vérification.</p>
                </div>
              )}

              <div className="session-actions" style={{ justifyContent: 'space-between', marginTop: 12 }}>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-secondary" onClick={() => setActiveSide('front')} disabled={activeSide === 'front'}>
                    Voir recto
                  </button>
                  <button className="btn-secondary" onClick={() => setActiveSide('back')} disabled={activeSide === 'back'}>
                    Voir verso
                  </button>
                  <button className="btn-secondary" disabled={busy} onClick={() => photoInputRef.current?.click()}>
                    Mettre à jour la photo
                  </button>
                </div>
                <button className="btn-secondary" onClick={() => window.open(`/api/v1/verify/card/${selectedCard.card_number || selectedCard.id}`, '_blank')}>
                  Vérifier la carte
                </button>
              </div>
            </>
          )}
        </div>

        <div className="card">
          <h2>Timeline et documents</h2>
          {selectedCard ? (
            <>
              <ul className="home-list">
                <li>Demande: {selectedCard.status === 'pending_payment' || selectedCard.status === 'pending_validation' || selectedCard.status === 'validated' ? 'faite' : 'non'}</li>
                <li>Paiement: {selectedFee?.status === 'paid' ? 'confirmé' : 'en attente'}</li>
                <li>Validation commune: {selectedCard.status === 'validated' ? 'faite' : 'en attente'}</li>
              </ul>

              <div className="session-actions" style={{ justifyContent: 'flex-start', flexWrap: 'wrap', marginTop: 12 }}>
                {selectedFee?.status !== 'paid' && (
                  <button className="btn-primary" disabled={busy} onClick={payOpeningFee}>
                    Payer les frais carte
                  </button>
                )}
                <button className="btn-secondary" disabled={!selectedCard.front_document_id} onClick={() => downloadDocument(selectedCard.front_document_id)}>
                  Télécharger recto (PDF)
                </button>
                <button className="btn-secondary" disabled={!selectedCard.back_document_id} onClick={() => downloadDocument(selectedCard.back_document_id)}>
                  Télécharger verso (PDF)
                </button>
                <button className="btn-secondary" disabled={!selectedFee?.receipt_document_id} onClick={() => downloadDocument(selectedFee?.receipt_document_id)}>
                  Télécharger reçu paiement
                </button>
              </div>
            </>
          ) : (
            <p>Créez une carte pour afficher sa timeline.</p>
          )}

          <h3 style={{ marginTop: 20 }}>Mes cartes</h3>
          <ul className="home-list">
            {allCards.length === 0 && <li>Aucune carte.</li>}
            {allCards.map((card) => (
              <li key={`${card.card_type}-${card.id}`}>
                <button
                  className="btn-secondary"
                  style={{ width: '100%', justifyContent: 'space-between' }}
                  onClick={() => setSelectedCardId(card.id)}
                >
                  <span>{card.role_label} {card.card_number || `#${card.id}`}</span>
                  <span>{statusLabel[card.status] || card.status}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
