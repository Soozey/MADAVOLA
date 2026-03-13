import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { getApiDetailFromError, getApiErrorMessage } from '../lib/apiErrors'
import './LotsPage.css'

export default function LotsPage() {
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [selectedFiliere, setSelectedFiliere] = useState('OR')
  const [selectedSousFiliere, setSelectedSousFiliere] = useState('GEMME')
  const [selectedProductId, setSelectedProductId] = useState('')
  const [selectedEssenceId, setSelectedEssenceId] = useState('')
  const [selectedWoodForm, setSelectedWoodForm] = useState('grume')
  const [dynamicAttributes, setDynamicAttributes] = useState<Record<string, string>>({})
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const toast = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['lots', page],
    queryFn: () => api.getLots({ page, page_size: 20 }),
  })

  const { data: catalogProducts = [] } = useQuery({
    queryKey: ['catalog', 'products', selectedFiliere, selectedSousFiliere],
    queryFn: () => api.getCatalogProducts({ filiere: selectedFiliere, sous_filiere: selectedSousFiliere }),
    enabled: showForm && selectedFiliere === 'PIERRE',
  })
  const { data: essences = [] } = useQuery({
    queryKey: ['catalog', 'essences'],
    queryFn: () => api.getEssences(),
    enabled: showForm && selectedFiliere === 'BOIS',
  })
  const selectedProduct = (catalogProducts as any[]).find((p: any) => String(p.id) === selectedProductId)
  const requiredAttributes: string[] = selectedProduct?.required_attributes ?? []
  const allowedUnits: string[] = selectedProduct?.allowed_units ?? []

  const createMutation = useMutation({
    mutationFn: async (payload: {
      filiere: string
      sous_filiere?: string
      product_catalog_id?: number
      wood_essence_id?: number
      wood_form?: string
      volume_m3?: number
      attributes?: Record<string, unknown>
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
        sous_filiere: payload.sous_filiere,
        product_catalog_id: payload.product_catalog_id,
        wood_essence_id: payload.wood_essence_id,
        wood_form: payload.wood_form,
        volume_m3: payload.volume_m3,
        attributes: payload.attributes,
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
  const consolidateMutation = useMutation({
    mutationFn: async (payload: { lot_ids: number[]; product_type: string; unit: string; lat: number; lon: number }) => {
      const geo = await api.createGeoPoint({ lat: payload.lat, lon: payload.lon, accuracy_m: 10, source: 'web' })
      return api.consolidateLots({
        lot_ids: payload.lot_ids,
        product_type: payload.product_type,
        unit: payload.unit,
        declare_geo_point_id: geo.id,
      })
    },
    onSuccess: (row) => {
      queryClient.invalidateQueries({ queryKey: ['lots'] })
      toast.success(`Lot consolide cree (#${row.id}).`)
    },
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, 'Consolidation impossible.'))
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!user?.id) return
    const formData = new FormData(e.currentTarget)
    createMutation.mutate({
      filiere: formData.get('filiere') as string,
      sous_filiere: (formData.get('sous_filiere') as string) || undefined,
      product_catalog_id: formData.get('product_catalog_id') ? Number(formData.get('product_catalog_id')) : undefined,
      wood_essence_id: formData.get('wood_essence_id') ? Number(formData.get('wood_essence_id')) : undefined,
      wood_form: (formData.get('wood_form') as string) || undefined,
      volume_m3: formData.get('volume_m3') ? Number(formData.get('volume_m3')) : undefined,
      attributes:
        (formData.get('filiere') as string) === 'PIERRE'
          ? Object.fromEntries(Object.entries(dynamicAttributes).map(([k, v]) => [k, v.trim()]))
          : undefined,
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

  const handleConsolidatePrompt = () => {
    const rawIds = window.prompt('IDs lots a consolider (ex: 12,13)', '')
    if (!rawIds) return
    const ids = rawIds.split(',').map((x) => Number(x.trim())).filter((x) => Number.isFinite(x) && x > 0)
    if (ids.length < 2) return
    const product_type = window.prompt('Type produit consolide', 'mixte') || 'mixte'
    const unit = window.prompt('Unite', 'm3') || 'm3'
    const lat = Number(window.prompt('Latitude', '-18.8792'))
    const lon = Number(window.prompt('Longitude', '47.5079'))
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return
    consolidateMutation.mutate({ lot_ids: ids, product_type, unit, lat, lon })
  }

  if (isLoading) return <div className="loading">Chargement...</div>

  return (
    <div className="lots-page">
      <div className="page-header">
        <h1>Lots</h1>
      </div>

      <div className="card tasks-of-day">
        <h2>Taches du jour</h2>
        <p className="process-label">
          Demarrez par la declaration d'un lot, puis preparez les consolidations si besoin.
        </p>
        <div className="tasks-actions">
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Annuler la declaration' : 'Declarer un lot'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleConsolidatePrompt}
            disabled={consolidateMutation.isPending}
          >
            Consolider des lots
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => document.getElementById('lots-list')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Voir mes lots
          </button>
        </div>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2>Declaration de lot</h2>
          <p className="process-label">OR / PIERRE / BOIS avec validation catalogue pour PIERRE.</p>
          {!user ? (
            <p className="form-warning">Vous devez etre connecte pour creer un lot.</p>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="filiere">Filiere *</label>
                  <select
                    id="filiere"
                    name="filiere"
                    required
                    value={selectedFiliere}
                    onChange={(e) => {
                      setSelectedFiliere(e.target.value)
                      if (e.target.value !== 'PIERRE') {
                        setSelectedProductId('')
                        setDynamicAttributes({})
                      }
                      if (e.target.value !== 'BOIS') {
                        setSelectedEssenceId('')
                      }
                    }}
                  >
                    <option value="OR">OR</option>
                    <option value="PIERRE">PIERRE</option>
                    <option value="BOIS">BOIS</option>
                  </select>
                </div>
                {selectedFiliere === 'PIERRE' && (
                  <>
                    <div className="form-group">
                      <label htmlFor="sous_filiere">Sous-filiere *</label>
                      <select
                        id="sous_filiere"
                        name="sous_filiere"
                        required
                        value={selectedSousFiliere}
                        onChange={(e) => {
                          setSelectedSousFiliere(e.target.value)
                          setSelectedProductId('')
                          setDynamicAttributes({})
                        }}
                      >
                        <option value="GEMME">GEMME</option>
                        <option value="INDUSTRIELLE">INDUSTRIELLE</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label htmlFor="product_catalog_id">Produit catalogue *</label>
                      <select
                        id="product_catalog_id"
                        name="product_catalog_id"
                        required
                        value={selectedProductId}
                        onChange={(e) => {
                          setSelectedProductId(e.target.value)
                          setDynamicAttributes({})
                        }}
                      >
                        <option value="">Selectionner...</option>
                        {(catalogProducts as any[]).map((p: any) => (
                          <option key={p.id} value={p.id}>
                            {p.code} - {p.nom}
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                )}
                {selectedFiliere === 'BOIS' && (
                  <>
                    <div className="form-group">
                      <label htmlFor="wood_essence_id">Essence *</label>
                      <select
                        id="wood_essence_id"
                        name="wood_essence_id"
                        required
                        value={selectedEssenceId}
                        onChange={(e) => setSelectedEssenceId(e.target.value)}
                      >
                        <option value="">Selectionner...</option>
                        {(essences as any[]).map((e: any) => (
                          <option key={e.id} value={e.id}>
                            {e.code_essence} - {e.nom} ({e.categorie})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label htmlFor="wood_form">Forme *</label>
                      <select
                        id="wood_form"
                        name="wood_form"
                        required
                        value={selectedWoodForm}
                        onChange={(e) => setSelectedWoodForm(e.target.value)}
                      >
                        <option value="tronc">tronc</option>
                        <option value="grume">grume</option>
                        <option value="billon">billon</option>
                        <option value="planche">planche</option>
                        <option value="lot_scie">lot_scie</option>
                        <option value="produit_fini">produit_fini</option>
                      </select>
                    </div>
                  </>
                )}
                <div className="form-group">
                  <label htmlFor="product_type">Type produit *</label>
                  <input type="text" id="product_type" name="product_type" required />
                </div>
                <div className="form-group">
                  <label htmlFor="quantity">Quantite *</label>
                  <input type="number" id="quantity" name="quantity" step="0.01" min="0.01" required />
                </div>
                <div className="form-group">
                  <label htmlFor="unit">Unite *</label>
                  <select id="unit" name="unit" required>
                    <option value="">Selectionner...</option>
                    {(selectedFiliere === 'PIERRE' && allowedUnits.length > 0
                      ? allowedUnits
                      : selectedFiliere === 'BOIS'
                        ? ['m3', 'piece', 'kg']
                        : ['g', 'kg', 'akotry', 'carat', 'piece', 'lot', 'tonne', 'm3', 'sac', 'palette']
                    ).map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>
                {selectedFiliere === 'BOIS' && (
                  <div className="form-group">
                    <label htmlFor="volume_m3">Volume (m3)</label>
                    <input type="number" id="volume_m3" name="volume_m3" min="0" step="0.0001" />
                  </div>
                )}
                {selectedFiliere === 'PIERRE' && requiredAttributes.map((attr) => (
                  <div className="form-group" key={attr}>
                    <label htmlFor={`attr_${attr}`}>{attr} *</label>
                    <input
                      id={`attr_${attr}`}
                      value={dynamicAttributes[attr] || ''}
                      onChange={(e) => setDynamicAttributes((prev) => ({ ...prev, [attr]: e.target.value }))}
                      required
                    />
                  </div>
                ))}
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

      <div id="lots-list" className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Filiere</th>
                <th>Sous-filiere</th>
                <th>Type</th>
                <th>Quantite</th>
                <th>Unite</th>
                <th>Statut</th>
                <th>Classification bois</th>
                <th>LAF/NDF/CITES</th>
                <th>Recu</th>
                <th>Numero lot</th>
                <th>ID tracabilite</th>
                <th>Offre</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.length ? (
                data.items.map((lot: any) => (
                  <tr key={lot.id}>
                    <td><Link to={`/lots/${lot.id}`}>{lot.id}</Link></td>
                    <td>{lot.filiere}</td>
                    <td>{lot.sous_filiere || '-'}</td>
                    <td>{lot.product_type}</td>
                    <td>{lot.quantity}</td>
                    <td>{lot.unit}</td>
                    <td>
                      <span className={`status-badge status-${lot.status}`}>{lot.status}</span>
                    </td>
                    <td>{lot.wood_classification || '-'}</td>
                    <td>
                      {[lot.cites_laf_status, lot.cites_ndf_status, lot.cites_international_status].filter(Boolean).join(' / ') || '-'}
                    </td>
                    <td>{lot.declaration_receipt_number || '-'}</td>
                    <td>{lot.lot_number || '-'}</td>
                    <td>{lot.traceability_id || '-'}</td>
                    <td>
                      <Link className="btn-secondary" to={`/marketplace?lot_id=${lot.id}`}>
                        Mettre en vente
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={13}>
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
              <button className="btn-secondary" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                Precedent
              </button>
              <button className="btn-secondary" onClick={() => setPage((p) => p + 1)} disabled={page >= data.total_pages}>
                Suivant
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
