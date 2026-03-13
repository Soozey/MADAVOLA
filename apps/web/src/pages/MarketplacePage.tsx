import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'

export default function MarketplacePage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const lotIdFromRoute = searchParams.get('lot_id') || ''
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [filters, setFilters] = useState({
    filiere: '',
    offer_type: '',
    min_price: '',
    max_price: '',
    min_quantity: '',
    max_quantity: '',
  })
  const [form, setForm] = useState({
    offer_type: 'sell',
    filiere: 'OR',
    lot_id: lotIdFromRoute,
    product_type: 'or_brut',
    quantity: '1',
    unit: 'g',
    unit_price: '1000',
    notes: '',
  })

  const offerQueryParams = useMemo(() => ({
    filiere: filters.filiere || undefined,
    offer_type: (filters.offer_type as 'sell' | 'buy') || undefined,
    min_price: filters.min_price ? Number(filters.min_price) : undefined,
    max_price: filters.max_price ? Number(filters.max_price) : undefined,
    min_quantity: filters.min_quantity ? Number(filters.min_quantity) : undefined,
    max_quantity: filters.max_quantity ? Number(filters.max_quantity) : undefined,
  }), [filters])

  const { data: offers = [] } = useQuery({
    queryKey: ['marketplace', 'offers', offerQueryParams],
    queryFn: () => api.listMarketplaceOffers(offerQueryParams),
    enabled: !!user,
  })

  const createOfferMutation = useMutation({
    mutationFn: () =>
      api.createMarketplaceOffer({
        offer_type: form.offer_type as 'sell' | 'buy',
        filiere: form.filiere,
        lot_id: form.lot_id ? Number(form.lot_id) : undefined,
        product_type: form.product_type,
        quantity: Number(form.quantity),
        unit: form.unit,
        unit_price: Number(form.unit_price),
        notes: form.notes || undefined,
      }),
    onSuccess: () => {
      setSuccess('Offre publiee.')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['marketplace', 'offers'] })
    },
    onError: (err) => {
      setError(getErrorMessage(err, 'Publication offre impossible.'))
      setSuccess('')
    },
  })

  const closeOfferMutation = useMutation({
    mutationFn: (offerId: number) => api.closeMarketplaceOffer(offerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace', 'offers'] })
    },
  })

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    createOfferMutation.mutate()
  }

  return (
    <div className="dashboard">
      <h1>Marketplace terrain</h1>
      <p className="dashboard-subtitle">Offres de vente/achat filtrables par prix, quantite, zone et filiere.</p>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}

      <div className="dashboard-grid">
        <section className="card">
          <h2>Publier une offre</h2>
          <form onSubmit={onSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="offer_type">Type</label>
                <select id="offer_type" value={form.offer_type} onChange={(e) => setForm((p) => ({ ...p, offer_type: e.target.value }))}>
                  <option value="sell">Offre de vente</option>
                  <option value="buy">Offre d'achat</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="filiere">Filiere</label>
                <select id="filiere" value={form.filiere} onChange={(e) => setForm((p) => ({ ...p, filiere: e.target.value }))}>
                  <option value="OR">OR</option>
                  <option value="PIERRE">PIERRE</option>
                  <option value="BOIS">BOIS</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="lot_id">Lot (vente)</label>
                <input id="lot_id" value={form.lot_id} onChange={(e) => setForm((p) => ({ ...p, lot_id: e.target.value }))} placeholder="ID lot" />
              </div>
              <div className="form-group">
                <label htmlFor="product_type">Produit</label>
                <input id="product_type" value={form.product_type} onChange={(e) => setForm((p) => ({ ...p, product_type: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="quantity">Quantite</label>
                <input id="quantity" type="number" min="0.0001" step="0.0001" value={form.quantity} onChange={(e) => setForm((p) => ({ ...p, quantity: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="unit">Unite</label>
                <input id="unit" value={form.unit} onChange={(e) => setForm((p) => ({ ...p, unit: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="unit_price">Prix unitaire</label>
                <input id="unit_price" type="number" min="0.01" step="0.01" value={form.unit_price} onChange={(e) => setForm((p) => ({ ...p, unit_price: e.target.value }))} />
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label htmlFor="notes">Notes</label>
                <input id="notes" value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} />
              </div>
            </div>
            <button className="btn-primary" type="submit" disabled={createOfferMutation.isPending}>
              {createOfferMutation.isPending ? 'Publication...' : 'Publier'}
            </button>
          </form>
        </section>

        <section className="card">
          <h2>Rechercher des offres</h2>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="filter_type">Type</label>
              <select id="filter_type" value={filters.offer_type} onChange={(e) => setFilters((p) => ({ ...p, offer_type: e.target.value }))}>
                <option value="">Tous</option>
                <option value="sell">Vente</option>
                <option value="buy">Achat</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="filter_filiere">Filiere</label>
              <select id="filter_filiere" value={filters.filiere} onChange={(e) => setFilters((p) => ({ ...p, filiere: e.target.value }))}>
                <option value="">Toutes</option>
                <option value="OR">OR</option>
                <option value="PIERRE">PIERRE</option>
                <option value="BOIS">BOIS</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="min_price">Prix min</label>
              <input id="min_price" type="number" value={filters.min_price} onChange={(e) => setFilters((p) => ({ ...p, min_price: e.target.value }))} />
            </div>
            <div className="form-group">
              <label htmlFor="max_price">Prix max</label>
              <input id="max_price" type="number" value={filters.max_price} onChange={(e) => setFilters((p) => ({ ...p, max_price: e.target.value }))} />
            </div>
            <div className="form-group">
              <label htmlFor="min_qty">Quantite min</label>
              <input id="min_qty" type="number" value={filters.min_quantity} onChange={(e) => setFilters((p) => ({ ...p, min_quantity: e.target.value }))} />
            </div>
            <div className="form-group">
              <label htmlFor="max_qty">Quantite max</label>
              <input id="max_qty" type="number" value={filters.max_quantity} onChange={(e) => setFilters((p) => ({ ...p, max_quantity: e.target.value }))} />
            </div>
          </div>
        </section>
      </div>

      <section className="card">
        <h2>Offres disponibles</h2>
        <ul className="home-list">
          {(offers as any[]).length === 0 && <li>Aucune offre.</li>}
          {(offers as any[]).map((row: any) => (
            <li key={row.id}>
              #{row.id} | {row.offer_type} | {row.filiere} | {row.product_type} | {row.quantity} {row.unit} | {row.unit_price} {row.currency}
              {' | '}acteur: {row.actor_name || row.actor_id}
              {row.notes ? ` | note: ${row.notes}` : ''}
              {row.actor_id === user?.id && row.status === 'active' && (
                <button className="btn-secondary" style={{ marginLeft: 8 }} onClick={() => closeOfferMutation.mutate(row.id)}>
                  Cloturer
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
