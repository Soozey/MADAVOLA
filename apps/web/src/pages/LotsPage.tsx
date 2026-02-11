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
        declare_geo_point_id: geo.id,
        declared_by_actor_id: payload.declared_by_actor_id,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lots'] })
      setShowForm(false)
      toast.success('Lot déclaré avec succès. Le grand livre (ledger) a été mis à jour.')
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
      lat: Number(formData.get('lat')),
      lon: Number(formData.get('lon')),
      declared_by_actor_id: user.id,
    })
  }

  const errorDetail = createMutation.isError ? getApiDetailFromError(createMutation.error) : null
  const errorMessage = createMutation.isError
    ? getApiErrorMessage(errorDetail, 'Erreur lors de la déclaration du lot.')
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
          <h2>Déclaration de lot</h2>
          <p className="process-label">Étape 2 du processus : déclarer un lot (filière, type, quantité). Le lieu GPS enregistre le point de déclaration.</p>
          {!user ? (
            <p className="form-warning">Vous devez être connecté pour créer un lot.</p>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="filiere">Filière *</label>
                  <input type="text" id="filiere" name="filiere" required defaultValue="OR" />
                </div>
                <div className="form-group">
                  <label htmlFor="product_type">Type de produit *</label>
                  <input type="text" id="product_type" name="product_type" required placeholder="ex: Riz" />
                </div>
                <div className="form-group">
                  <label htmlFor="quantity">Quantité *</label>
                  <input type="number" id="quantity" name="quantity" step="0.01" required />
                </div>
                <div className="form-group">
                  <label htmlFor="unit">Unité *</label>
                  <select id="unit" name="unit" required>
                    <option value="">Sélectionner...</option>
                    <option value="kg">kg</option>
                    <option value="tonne">tonne</option>
                    <option value="litre">litre</option>
                    <option value="unité">unité</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="lat">Latitude (GPS) *</label>
                  <input type="number" id="lat" name="lat" required step="any" placeholder="ex: -18.8792" />
                  <span className="form-hint">Coordonnées du lieu de déclaration</span>
                </div>
                <div className="form-group">
                  <label htmlFor="lon">Longitude (GPS) *</label>
                  <input type="number" id="lon" name="lon" required step="any" placeholder="ex: 47.5079" />
                </div>
              </div>
              {errorMessage && <div className="alert alert-error">{errorMessage}</div>}
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Création...' : 'Créer'}
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
                <th>Filière</th>
                <th>Type</th>
                <th>Quantité</th>
                <th>Unité</th>
                <th>Statut</th>
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
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state-rich">
                      <div className="empty-title">Aucun lot</div>
                      <p className="empty-desc">La déclaration de lot est l'étape 2 : après avoir inscrit des acteurs, déclarez un lot (filière, type, quantité) pour qu'il puisse être vendu dans une transaction.</p>
                      <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
                        + Déclarer un lot
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
                Précédent
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
