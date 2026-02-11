import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import './DashboardPage.css'

export default function LedgerPage() {
  const [actorIdFilter, setActorIdFilter] = useState('')
  const [lotIdFilter, setLotIdFilter] = useState('')
  const actorId = actorIdFilter ? parseInt(actorIdFilter, 10) : undefined
  const lotId = lotIdFilter ? parseInt(lotIdFilter, 10) : undefined

  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['ledger', actorId, lotId],
    queryFn: () => api.getLedgerEntries({ actor_id: actorId, lot_id: lotId }),
  })

  const { data: balance = [] } = useQuery({
    queryKey: ['ledger-balance', actorId],
    queryFn: () => api.getLedgerBalance({ actor_id: actorId }),
  })

  return (
    <div className="dashboard">
      <h1>Grand livre</h1>
      <p className="dashboard-subtitle">
        Mouvements d inventaire (création, transfert) et soldes par acteur/lot.
      </p>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>Filtres</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Acteur ID</label>
            <input
              type="number"
              className="form-control"
              style={{ width: 120 }}
              value={actorIdFilter}
              onChange={(e) => setActorIdFilter(e.target.value)}
              placeholder="optionnel"
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Lot ID</label>
            <input
              type="number"
              className="form-control"
              style={{ width: 120 }}
              value={lotIdFilter}
              onChange={(e) => setLotIdFilter(e.target.value)}
              placeholder="optionnel"
            />
          </div>
        </div>
      </div>

      {balance.length > 0 && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h2>Soldes</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Acteur ID</th>
                <th>Lot ID</th>
                <th>Quantité</th>
              </tr>
            </thead>
            <tbody>
              {balance.map((b: { actor_id: number; lot_id: number; quantity: number }, i: number) => (
                <tr key={String(b.actor_id) + b.lot_id + i}>
                  <td><Link to={`/actors/${b.actor_id}`}>{b.actor_id}</Link></td>
                  <td><Link to={`/lots/${b.lot_id}`}>{b.lot_id}</Link></td>
                  <td>{b.quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card">
        <h2>Mouvements</h2>
        {isLoading && <div className="loading">Chargement...</div>}
        {!isLoading && entries.length === 0 && <p className="empty-state">Aucun mouvement.</p>}
        {!isLoading && entries.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Acteur</th>
                <th>Lot</th>
                <th>Type</th>
                <th>Delta quantité</th>
                <th>Événement</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e: { id: number; actor_id: number; lot_id: number; movement_type: string; quantity_delta: number; ref_event_type: string; ref_event_id: string | null }) => (
                <tr key={e.id}>
                  <td>{e.id}</td>
                  <td><Link to={`/actors/${e.actor_id}`}>{e.actor_id}</Link></td>
                  <td><Link to={`/lots/${e.lot_id}`}>{e.lot_id}</Link></td>
                  <td>{e.movement_type}</td>
                  <td>{e.quantity_delta > 0 ? '+' : ''}{e.quantity_delta}</td>
                  <td>{e.ref_event_type}{e.ref_event_id ? ' #' + e.ref_event_id : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
