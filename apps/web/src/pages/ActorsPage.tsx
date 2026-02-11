import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { useAuth } from '../contexts/AuthContext'
import { getApiDetailFromError, getApiErrorMessage } from '../lib/apiErrors'
import {
  HARDCODED_REGIONS,
  getHardcodedDistricts,
  getHardcodedCommunes,
  getHardcodedFokontany,
} from '../data/territories'
import './ActorsPage.css'

// Centre Madagascar (pour la carte)
const DEFAULT_LAT = -18.8792
const DEFAULT_LON = 47.5079

// IcÃ´ne marqueur par dÃ©faut (Ã©viter 404 avec icÃ´nes Leaflet)
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

function MapClickHandler({ onSelect }: { onSelect: (lat: number, lon: number) => void }) {
  useMapEvents({
    click: (e) => onSelect(e.latlng.lat, e.latlng.lng),
  })
  return null
}

const ROLES_OPTIONS = [
  { value: 'acteur', label: 'Acteur' },
  { value: 'orpailleur', label: 'Orpailleur' },
  { value: 'commune_agent', label: 'Agent commune' },
]

export default function ActorsPage() {
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [regionCode, setRegionCode] = useState('')
  const [districtCode, setDistrictCode] = useState('')
  const [communeCode, setCommuneCode] = useState('')
  const [mapLat, setMapLat] = useState(DEFAULT_LAT)
  const [mapLon, setMapLon] = useState(DEFAULT_LON)
  const queryClient = useQueryClient()
  const toast = useToast()
  const { user } = useAuth()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const effectiveRoles = userRoles
  const canValidateActors = userRoles.some((r) => ['admin', 'dirigeant', 'commune_agent'].includes(r))
  const showValidationSection = effectiveRoles.some((r) => ['admin', 'commune_agent'].includes(r))

  // Utiliser les territoires en dur (UTF-8) pour des libellÃ©s avec accents corrects
  const regions = HARDCODED_REGIONS
  const districts = regionCode ? getHardcodedDistricts(regionCode) : []
  const communes = districtCode ? getHardcodedCommunes(districtCode) : []
  const fokontanyList = communeCode ? getHardcodedFokontany(communeCode) : []
  const districtsLoading = false
  const communesLoading = false

  useEffect(() => {
    if (!regionCode) setDistrictCode('')
    if (!districtCode) setCommuneCode('')
  }, [regionCode, districtCode])

  const { data: rawData, isLoading } = useQuery({
    queryKey: ['actors', page],
    queryFn: () => api.getActors({ page, page_size: 20 }),
    enabled: canValidateActors,
  })
  const data = rawData && Array.isArray(rawData)
    ? { items: rawData, total: rawData.length, page: 1, total_pages: 1 }
    : rawData

  const { data: pendingActors = [], isLoading: pendingLoading } = useQuery({
    queryKey: ['actors', 'pending'],
    queryFn: () => api.getActors({ status: 'pending' }),
    enabled: canValidateActors && showValidationSection,
  })
  const pendingList = Array.isArray(pendingActors) ? pendingActors : []

  const validateMutation = useMutation({
    mutationFn: ({ actorId, status }: { actorId: number; status: 'active' | 'rejected' }) =>
      api.updateActorStatus(actorId, status),
    onSuccess: (_, { status }) => {
      queryClient.invalidateQueries({ queryKey: ['actors'] })
      toast.success(status === 'active' ? 'Acteur validÃ©.' : 'Acteur refusÃ©.')
    },
    onError: () => toast.error('Erreur lors de la validation.'),
  })

  const createMutation = useMutation({
    mutationFn: async (payload: {
      type_personne: string
      nom: string
      prenoms: string
      email: string
      telephone: string
      password: string
      region_code: string
      district_code: string
      commune_code: string
      fokontany_code: string
      lat: number
      lon: number
      roles: string[]
    }) => {
      const geo = await api.createGeoPoint({
        lat: payload.lat,
        lon: payload.lon,
        accuracy_m: 10,
        source: 'web',
      })
      return api.createActor({
        type_personne: payload.type_personne,
        nom: payload.nom,
        prenoms: payload.prenoms || '',
        email: payload.email || undefined,
        telephone: payload.telephone,
        password: payload.password,
        region_code: payload.region_code,
        district_code: payload.district_code,
        commune_code: payload.commune_code,
        fokontany_code: payload.fokontany_code || undefined,
        geo_point_id: geo.id,
        roles: payload.roles,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actors'] })
      setShowForm(false)
      toast.success("Acteur crÃ©Ã© avec succÃ¨s. L'acteur pourra se connecter aprÃ¨s validation par la commune si nÃ©cessaire.")
    },
  })

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const fokontany = formData.get('fokontany_code') as string
    createMutation.mutate({
      type_personne: (formData.get('type_personne') as string) || 'personne_physique',
      nom: formData.get('nom') as string,
      prenoms: (formData.get('prenoms') as string) || '',
      email: formData.get('email') as string,
      telephone: formData.get('telephone') as string,
      password: formData.get('password') as string,
      region_code: formData.get('region_code') as string,
      district_code: formData.get('district_code') as string,
      commune_code: formData.get('commune_code') as string,
      fokontany_code: fokontany || '',
      lat: mapLat,
      lon: mapLon,
      roles: [(formData.get('roles') as string) || 'acteur'],
    })
  }

  const errorDetail = createMutation.isError ? getApiDetailFromError(createMutation.error) : null
  const errorMessage = createMutation.isError
    ? getApiErrorMessage(errorDetail, "Erreur lors de la crÃ©ation de l'acteur.")
    : ''
  const errorRaw =
    createMutation.isError &&
    errorDetail != null &&
    typeof errorDetail === 'object' &&
    !Array.isArray(errorDetail) &&
    !('message' in (errorDetail as object))
      ? JSON.stringify(errorDetail)
      : null

  const isOrpailleurOrActeur = effectiveRoles.some((r) => ['orpailleur', 'acteur'].includes(r))
  const isMaireOrAdmin = showValidationSection

  if (canValidateActors && isLoading) return <div className="loading">Chargement...</div>

  return (
    <div className="actors-page">
      <div className="page-header">
        <h1>
          {isOrpailleurOrActeur ? 'CrÃ©ation ou modification de compte' : 'Acteurs'}
        </h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : isOrpailleurOrActeur ? '+ CrÃ©er mon compte' : '+ Nouvel acteur'}
        </button>
      </div>
      {isOrpailleurOrActeur && !showForm && (
        <p className="role-hint">
          En tant qu&apos;orpailleur ou acteur : crÃ©ez votre compte pour dÃ©clarer des lots et effectuer des transactions. Vous pouvez aussi modifier votre profil aprÃ¨s validation par la commune.
        </p>
      )}
      {isMaireOrAdmin && !showForm && (
        <p className="role-hint">
          En tant que maire / agent commune : validez les inscriptions des nouveaux orpailleurs et acteurs de votre commune ciâ€‘dessous.
        </p>
      )}

      {showValidationSection && (
        <div className="card validation-card">
          <h2>En attente de validation</h2>
          <p className="process-label">Nouveaux orpailleurs et acteurs inscrits dans votre commune. Validez ou refusez l&apos;inscription.</p>
          {pendingLoading ? (
            <div className="loading">Chargement...</div>
          ) : pendingList.length === 0 ? (
            <p className="empty-desc">Aucune inscription en attente.</p>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Nom</th>
                    <th>Email</th>
                    <th>TÃ©lÃ©phone</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingList.map((actor: any) => (
                    <tr key={actor.id}>
                      <td><Link to={`/actors/${actor.id}`}>{actor.id}</Link></td>
                      <td>{actor.nom} {actor.prenoms}</td>
                      <td>{actor.email}</td>
                      <td>{actor.telephone}</td>
                      <td>
                        <button
                          type="button"
                          className="btn-primary btn-sm"
                          disabled={validateMutation.isPending}
                          onClick={() => validateMutation.mutate({ actorId: actor.id, status: 'active' })}
                        >
                          Valider
                        </button>
                        {' '}
                        <button
                          type="button"
                          className="btn-secondary btn-sm"
                          disabled={validateMutation.isPending}
                          onClick={() => validateMutation.mutate({ actorId: actor.id, status: 'rejected' })}
                        >
                          Refuser
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {showForm && (
        <div className="card form-card">
          <h2>Inscription acteur</h2>
          <p className="process-label">Ã‰tape 1 du processus : crÃ©er un acteur (collecteur, opÃ©rateur, orpailleur, etc.) avec localisation (RÃ©gion â†’ District â†’ Commune) et point GPS.</p>
          {regions.length === 0 ? (
            <p className="form-warning">
              Aucun territoire configurÃ©. VÃ©rifiez que le script create_admin a crÃ©Ã© un territoire par dÃ©faut (code DEFAULT).
            </p>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="type_personne">Type de personne *</label>
                  <select id="type_personne" name="type_personne" required defaultValue="personne_physique">
                    <option value="personne_physique">Personne physique</option>
                    <option value="personne_morale">Personne morale</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="nom">Nom *</label>
                  <input type="text" id="nom" name="nom" required />
                </div>
                <div className="form-group">
                  <label htmlFor="prenoms">PrÃ©noms</label>
                  <input type="text" id="prenoms" name="prenoms" />
                </div>
                <div className="form-group">
                  <label htmlFor="email">Email *</label>
                  <input type="email" id="email" name="email" required />
                </div>
                <div className="form-group">
                  <label htmlFor="telephone">TÃ©lÃ©phone *</label>
                  <input type="tel" id="telephone" name="telephone" required placeholder="0340000000" />
                  <span className="form-hint">Format : 03XXXXXXXX (10 chiffres, Madagascar)</span>
                </div>
                <div className="form-group">
                  <label htmlFor="password">Mot de passe *</label>
                  <input type="password" id="password" name="password" required minLength={6} />
                </div>
                <div className="form-group">
                  <label htmlFor="region_code">RÃ©gion *</label>
                  <select
                    id="region_code"
                    name="region_code"
                    required
                    value={regionCode}
                    onChange={(e) => setRegionCode(e.target.value)}
                  >
                    <option value="">â€” Choisir â€”</option>
                    {regions.map((r: { code: string; name: string }) => (
                      <option key={r.code} value={r.code}>
                        {r.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="district_code">District *</label>
                  <select
                    id="district_code"
                    name="district_code"
                    required
                    value={districtCode}
                    onChange={(e) => setDistrictCode(e.target.value)}
                    disabled={!regionCode || districtsLoading}
                  >
                    <option value="">â€” Choisir â€”</option>
                    {districts.map((d: { code: string; name: string }) => (
                      <option key={d.code} value={d.code}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="commune_code">Commune *</label>
                  <select
                    id="commune_code"
                    name="commune_code"
                    required
                    value={communeCode}
                    onChange={(e) => setCommuneCode(e.target.value)}
                    disabled={!districtCode || communesLoading}
                  >
                    <option value="">â€” Choisir â€”</option>
                    {communes.map((c: { code: string; name: string }) => (
                      <option key={c.code} value={c.code}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="fokontany_code">Fokontany</label>
                  <select
                    id="fokontany_code"
                    name="fokontany_code"
                    disabled={!communeCode}
                  >
                    <option value="">â€” Optionnel â€”</option>
                    {fokontanyList.map((f: { code?: string; name: string }) => (
                      <option key={f.code ?? f.name} value={f.code ?? ''}>
                        {f.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="roles">RÃ´le *</label>
                  <select id="roles" name="roles" required defaultValue="acteur">
                    {ROLES_OPTIONS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group form-group-map">
                  <label>Lieu d&apos;inscription (cliquez sur la carte) *</label>
                  <div className="map-wrapper">
                    <MapContainer
                      center={[mapLat, mapLon]}
                      zoom={6}
                      style={{ height: '280px', width: '100%' }}
                      scrollWheelZoom
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <MapClickHandler onSelect={(lat, lon) => { setMapLat(lat); setMapLon(lon) }} />
                      <Marker position={[mapLat, mapLon]} icon={defaultIcon}>
                        <Popup>Lieu d&apos;inscription</Popup>
                      </Marker>
                    </MapContainer>
                  </div>
                  <span className="form-hint">
                    Latitude : {mapLat.toFixed(5)} â€” Longitude : {mapLon.toFixed(5)}
                  </span>
                </div>
              </div>
              {errorMessage && (
                <div className="alert alert-error">
                  {errorMessage}
                  {errorRaw && <pre className="error-detail">{errorRaw}</pre>}
                </div>
              )}
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'CrÃ©ation...' : 'CrÃ©er'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {!canValidateActors && isOrpailleurOrActeur && !showForm && (
        <div className="card role-empty-card">
          <p>Pour crÃ©er votre compte orpailleur ou acteur, cliquez sur <strong>Â« CrÃ©er mon compte Â»</strong> ciâ€‘dessus. AprÃ¨s inscription, la commune validera votre compte.</p>
        </div>
      )}
      {canValidateActors && (
      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Nom</th>
                <th>Email</th>
                <th>TÃ©lÃ©phone</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.length ? (
                data.items.map((actor: any) => (
                  <tr key={actor.id}>
                    <td><Link to={`/actors/${actor.id}`}>{actor.id}</Link></td>
                    <td>
                      <Link to={`/actors/${actor.id}`}>{actor.nom} {actor.prenoms}</Link>
                    </td>
                    <td>{actor.email}</td>
                    <td>{actor.telephone}</td>
                    <td>
                      <span className={`status-badge status-${actor.status}`}>
                        {actor.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state-rich">
                      <div className="empty-title">Aucun acteur</div>
                      <p className="empty-desc">L'inscription d'un acteur est la premiÃ¨re Ã©tape : crÃ©ez un acteur (collecteur, opÃ©rateur, etc.) pour qu'il puisse ensuite dÃ©clarer des lots et effectuer des transactions.</p>
                      <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
                        + Inscrire un acteur
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
                PrÃ©cÃ©dent
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
      )}
    </div>
  )
}
