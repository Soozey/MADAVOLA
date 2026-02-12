import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { getApiDetailFromError, getApiErrorMessage } from '../lib/apiErrors'
import './LotsPage.css'

export default function LotsPage() {
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const toast = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['lots', page],
    queryFn: () => api.getLots({ page, page_size: 20 }),
  })

  const createMutation = useMutation({
    mutationFn: async (payload: {
      filiere: string
      product_type: string
      quantity: number
      unit: string
      notes?: string
      photo_urls: string[]
      lat: number
      lon: number
      declared_by_actor_id: number
    }) => {
      const geo = await api.createGeoPoint({
        lat: payload.lat,
        lon: payload.lon,
        accuracy_m: 10,
        source: 'web',
      })
      return api.createLot({
        filiere: payload.filiere,
        product_type: payload.product_type,
        quantity: payload.quantity,
        unit: payload.unit,
        notes: payload.notes,
        photo_urls: payload.photo_urls,
        declare_geo_point_id: geo.id,
        declared_by_actor_id: payload.declared_by_actor_id,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lots'] })
      setShowForm(false)
      toast.success('Lot declare avec succes. Recu et QR generes.')
    },
  })

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!user?.id) return
    const formData = new FormData(e.currentTarget)
    createMutation.mutate({
      filiere: formData.get('filiere') as string,
      product_type: formData.get('product_type') as string,
      quantity: parseFloat(formData.get('quantity') as string),
      unit: formData.get('unit') as string,
      notes: ((formData.get('notes') as string) || '').trim() || undefined,
      photo_urls: ((formData.get('photo_urls') as string) || '')
        .split(',')
        .map((v) => v.trim())
        .filter(Boolean),
      lat: Number(formData.get('lat')),
      lon: Number(formData.get('lon')),
      declared_by_actor_id: user.id,
    })
  }

  const errorDetail = createMutation.isError ? getApiDetailFromError(createMutation.error) : null
  const errorMessage = createMutation.isError
    ? getApiErrorMessage(errorDetail, 'Erreur lors de la declaration du lot.')
    : ''

  if (isLoading) return <div className="loading">Chargement...</div>

  return (
    <div className="lots-page">
      <div className="page-header">
        <h1>Lots</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouveau lot'}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2>Declaration de lot</h2>
          <p className="process-label">
            Etape 2: declaration lot (or brut/pepites/concentre), quantite, unite, GPS, preuves.
          </p>
          {!user ? (
            <p className="form-warning">Vous devez etre connecte pour creer un lot.</p>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="filiere">Filiere *</label>
                  <input type="text" id="filiere" name="filiere" required defaultValue="OR" />
                </div>
                <div className="form-group">
                  <label htmlFor="product_type">Type produit *</label>
                  <input type="text" id="product_type" name="product_type" required placeholder="or_brut" />
                </div>
                <div className="form-group">
                  <label htmlFor="quantity">Quantite *</label>
                  <input type="number" id="quantity" name="quantity" step="0.01" min="0.01" required />
                </div>
                <div className="form-group">
                  <label htmlFor="unit">Unite *</label>
                  <select id="unit" name="unit" required>
                    <option value="">Selectionner...</option>
                    <option value="g">g</option>
                    <option value="kg">kg</option>
                    <option value="akotry">akotry</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="notes">Notes</label>
                  <input type="text" id="notes" name="notes" />
                </div>
                <div className="form-group">
                  <label htmlFor="photo_urls">Photos URL (comma separated)</label>
                  <input type="text" id="photo_urls" name="photo_urls" placeholder="https://...,https://..." />
                </div>
                <div className="form-group">
                  <label htmlFor="lat">Latitude *</label>
                  <input type="number" id="lat" name="lat" required step="any" placeholder="-18.8792" />
                </div>
                <div className="form-group">
                  <label htmlFor="lon">Longitude *</label>
                  <input type="number" id="lon" name="lon" required step="any" placeholder="47.5079" />
                </div>
              </div>
              {errorMessage && <div className="alert alert-error">{errorMessage}</div>}
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creation...' : 'Creer'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Filiere</th>
                <th>Type</th>
                <th>Quantite</th>
                <th>Unite</th>
                <th>Statut</th>
                <th>Recu</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.length ? (
                data.items.map((lot: any) => (
                  <tr key={lot.id}>
                    <td><Link to={`/lots/${lot.id}`}>{lot.id}</Link></td>
                    <td>{lot.filiere}</td>
                    <td>{lot.product_type}</td>
                    <td>{lot.quantity}</td>
                    <td>{lot.unit}</td>
                    <td>
                      <span className={`status-badge status-${lot.status}`}>{lot.status}</span>
                    </td>
                    <td>{lot.declaration_receipt_number ?? '—'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state-rich">
                      <div className="empty-title">Aucun lot</div>
                      <p className="empty-desc">Declarez un lot pour pouvoir vendre.</p>
                      <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
                        + Declarer un lot
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {data && data.total_pages > 1 && (
          <div className="pagination">
            <div className="pagination-info">
              Page {data.page} sur {data.total_pages} ({data.total} total)
            </div>
            <div className="pagination-controls">
              <button
                className="btn-secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Precedent
              </button>
              <button
                className="btn-secondary"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
              >
                Suivant
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
