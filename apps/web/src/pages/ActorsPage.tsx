import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MapContainer, Marker, Popup, TileLayer, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useSession } from '../contexts/SessionContext'
import { getApiDetailFromError, getApiErrorMessage } from '../lib/apiErrors'
import { useToast } from '../contexts/ToastContext'
import { buildRoleOptionsByFilieres } from '../utils/rbacOptions'
import './ActorsPage.css'

const DEFAULT_LAT = -18.8792
const DEFAULT_LON = 47.5079

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

const FILIERE_OPTIONS = ['OR', 'PIERRE', 'BOIS'] as const

function MapClickHandler({ onSelect }: { onSelect: (lat: number, lon: number) => void }) {
  useMapEvents({
    click: (e) => onSelect(e.latlng.lat, e.latlng.lng),
  })
  return null
}

function defaultRoleFromSession(role: string | null): string {
  const map: Record<string, string> = {
    orpailleur: 'orpailleur',
    collecteur: 'collecteur',
    commune: 'commune_agent',
    controleur: 'police',
    comptoir: 'comptoir_operator',
  }
  return map[role ?? ''] ?? 'acteur'
}

export default function ActorsPage() {
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [regionCode, setRegionCode] = useState('')
  const [districtCode, setDistrictCode] = useState('')
  const [communeCode, setCommuneCode] = useState('')
  const [providerCode, setProviderCode] = useState('mvola')
  const [mapLat, setMapLat] = useState(DEFAULT_LAT)
  const [mapLon, setMapLon] = useState(DEFAULT_LON)
  const { selectedRole, selectedFiliere } = useSession()
  const [selectedRolesForCreate, setSelectedRolesForCreate] = useState<string[]>([
    defaultRoleFromSession(selectedRole),
  ])
  const [selectedFilieresForCreate, setSelectedFilieresForCreate] = useState<string[]>([
    (selectedFiliere ?? 'OR').toUpperCase(),
  ])
  const { data: rbacRoles = [], isLoading: rbacRolesLoading } = useQuery({
    queryKey: ['rbac', 'roles', [...selectedFilieresForCreate].sort().join(',')],
    queryFn: async () => {
      const filieres = selectedFilieresForCreate.length ? selectedFilieresForCreate : ['OR']
      const responses = await Promise.all(
        filieres.map((f) => api.getRbacRoles({ filiere: f, include_common: true }))
      )
      return buildRoleOptionsByFilieres(
        filieres,
        responses.flat() as any[]
      )
    },
    enabled: showForm,
  })
  const availableRoleOptions = rbacRoles

  const toast = useToast()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const activeSessionRole = (selectedRole ?? '').toLowerCase()
  const hasSessionRole = Boolean(activeSessionRole)
  const validationRoles = ['commune', 'commune_agent', 'com', 'com_admin', 'com_agent']
  const managementRoles = ['admin', 'dirigeant', ...validationRoles]
  const fallbackCanManage = userRoles.some((r) => managementRoles.includes(r))
  const fallbackCanValidate = userRoles.some((r) => validationRoles.includes(r))

  // En mode demo multi-role, l'UI suit d'abord le role de session choisi
  // pour eviter d'exposer des ecrans commune a un acteur terrain.
  const canManageActors = hasSessionRole ? managementRoles.includes(activeSessionRole) : fallbackCanManage
  const canValidateActors = hasSessionRole ? validationRoles.includes(activeSessionRole) : fallbackCanValidate
  const showValidationSection = canValidateActors

  const { data: activeTerritory } = useQuery({
    queryKey: ['territories', 'active-version'],
    queryFn: () => api.getActiveTerritoryVersion(),
  })
  const territoryVersionTag = activeTerritory?.version_tag ?? 'unknown'

  const { data: regions = [] } = useQuery({
    queryKey: ['territories', 'regions', territoryVersionTag],
    queryFn: () => api.getRegions(),
  })

  const { data: districts = [], isLoading: districtsLoading } = useQuery({
    queryKey: ['territories', 'districts', territoryVersionTag, regionCode],
    queryFn: () => api.getDistricts(regionCode),
    enabled: !!regionCode,
  })

  const { data: communes = [], isLoading: communesLoading } = useQuery({
    queryKey: ['territories', 'communes', territoryVersionTag, districtCode],
    queryFn: () => api.getCommunes(districtCode),
    enabled: !!districtCode,
  })

  const { data: fokontanyList = [] } = useQuery({
    queryKey: ['territories', 'fokontany', territoryVersionTag, communeCode],
    queryFn: () => api.getFokontany(communeCode),
    enabled: !!communeCode,
  })

  const selectedCommune = (communes as any[]).find((c: any) => c.code === communeCode)

  useEffect(() => {
    if (!regionCode) setDistrictCode('')
    if (!districtCode) setCommuneCode('')
  }, [regionCode, districtCode])

  useEffect(() => {
    const allowed = new Set(availableRoleOptions.map((r) => r.value))
    setSelectedRolesForCreate((current) => {
      const filtered = current.filter((r) => allowed.has(r))
      if (filtered.length > 0) return filtered
      const fallback = availableRoleOptions[0]?.value
      return fallback ? [fallback] : []
    })
  }, [availableRoleOptions])

  useEffect(() => {
    if (!hasSessionRole || canManageActors) return
    const preferred = availableRoleOptions.find((r) => r.value === activeSessionRole)?.value
    if (preferred) {
      setSelectedRolesForCreate([preferred])
    }
  }, [hasSessionRole, canManageActors, activeSessionRole, availableRoleOptions])

  useEffect(() => {
    if (!canManageActors && selectedFiliere) {
      setSelectedFilieresForCreate([selectedFiliere.toUpperCase()])
    }
  }, [canManageActors, selectedFiliere])

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

  const { data: feesData = [] } = useQuery({
    queryKey: ['fees'],
    queryFn: () => api.getFees(),
    enabled: canValidateActors && showValidationSection,
  })

  const latestOpeningFeeByActor = useMemo(() => {
    const map = new Map<number, any>()
    const fees = Array.isArray(feesData) ? feesData : []
    fees
      .filter((f: any) => f.fee_type === 'account_opening_commune')
      .forEach((fee: any) => {
        const prev = map.get(fee.actor_id)
        if (!prev || fee.id > prev.id) map.set(fee.actor_id, fee)
      })
    return map
  }, [feesData])

  const validateMutation = useMutation({
    mutationFn: ({ actorId, status }: { actorId: number; status: 'active' | 'rejected' }) =>
      api.updateActorStatus(actorId, status),
    onSuccess: (_, { status }) => {
      queryClient.invalidateQueries({ queryKey: ['actors'] })
      queryClient.invalidateQueries({ queryKey: ['fees'] })
      toast.success(status === 'active' ? 'Acteur valide.' : 'Acteur refuse.')
    },
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, 'Erreur lors de la validation.'))
    },
  })

  const markFeePaidMutation = useMutation({
    mutationFn: (feeId: number) => api.updateFeeStatus(feeId, 'paid'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fees'] })
      queryClient.invalidateQueries({ queryKey: ['actors'] })
      toast.success('Paiement marque comme recu. Vous pouvez valider le compte.')
    },
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, 'Impossible de marquer le paiement.'))
    },
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
      filieres: string[]
    }) => {
      const geo = await api.createGeoPoint({
        lat: payload.lat,
        lon: payload.lon,
        accuracy_m: 10,
        source: 'web',
      })
      const actor = await api.createActor({
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
        filieres: payload.filieres,
      })
      if (actor.opening_fee_id) {
        try {
          const payment = await api.initiateFeePayment(actor.opening_fee_id, {
            provider_code: providerCode,
            external_ref: `signup-fee-${actor.opening_fee_id}-${Date.now()}`,
          })
          return { actor, payment, paymentInitFailed: false }
        } catch {
          return { actor, payment: null, paymentInitFailed: true }
        }
      }
      return { actor, payment: null, paymentInitFailed: false }
    },
    onSuccess: (result: any) => {
      queryClient.invalidateQueries({ queryKey: ['actors'] })
      queryClient.invalidateQueries({ queryKey: ['fees'] })
      setShowForm(false)
      if (result?.payment?.beneficiary_msisdn) {
        toast.success(`Compte cree. Paiement initie vers ${result.payment.beneficiary_msisdn}.`)
      } else if (result?.paymentInitFailed) {
        toast.success('Compte cree. Paiement non initialise automatiquement, validez via workflow commune.')
      } else {
        toast.success('Acteur cree avec succes.')
      }
    },
    onError: (error) => {
      const detail = getApiDetailFromError(error)
      toast.error(getApiErrorMessage(detail, "Erreur lors de la creation de l'acteur."))
    },
  })

  const handleRoleToggle = (roleCode: string) => {
    setSelectedRolesForCreate((current) =>
      current.includes(roleCode) ? current.filter((r) => r !== roleCode) : [...current, roleCode]
    )
  }

  const handleFiliereToggle = (filiere: string) => {
    setSelectedFilieresForCreate((current) =>
      current.includes(filiere) ? current.filter((f) => f !== filiere) : [...current, filiere]
    )
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    if (selectedRolesForCreate.length === 0) {
      toast.error('Selectionnez au moins un role.')
      return
    }
    if (selectedFilieresForCreate.length === 0) {
      toast.error('Selectionnez au moins une filiere.')
      return
    }

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
      fokontany_code: (formData.get('fokontany_code') as string) || '',
      lat: mapLat,
      lon: mapLon,
      roles: selectedRolesForCreate,
      filieres: selectedFilieresForCreate,
    })
  }

  const errorDetail = createMutation.isError ? getApiDetailFromError(createMutation.error) : null
  const errorMessage = createMutation.isError
    ? getApiErrorMessage(errorDetail, "Erreur lors de la creation de l'acteur.")
    : ''

  const actorFacingRoleSet = new Set([
    'acteur', 'orpailleur', 'collecteur', 'bijoutier', 'transporteur', 'transporteur_agree',
    'comptoir_operator', 'comptoir_compliance', 'comptoir_director',
    'pierre_exploitant', 'pierre_collecteur', 'pierre_lapidaire', 'pierre_exportateur',
    'bois_exploitant', 'bois_collecteur', 'bois_transporteur', 'bois_transformateur', 'bois_artisan', 'bois_exportateur',
  ])
  const isActorFacing = hasSessionRole ? actorFacingRoleSet.has(activeSessionRole) : userRoles.some((r) => actorFacingRoleSet.has(r))
  const pageTitle = isActorFacing ? 'Mon parcours acteur' : 'Acteurs'
  const activeCreateFiliere = (selectedFiliere ?? 'OR').toUpperCase() as (typeof FILIERE_OPTIONS)[number]
  const roleOptionsForCreate = canManageActors
    ? availableRoleOptions
    : availableRoleOptions.filter((r) => r.value === activeSessionRole)
  const filiereOptionsForCreate = canManageActors
    ? FILIERE_OPTIONS
    : FILIERE_OPTIONS.filter((f) => f === activeCreateFiliere)

  if (canManageActors && isLoading) return <div className="loading">Chargement...</div>

  return (
    <div className="actors-page">
      <div className="page-header">
        <h1>{pageTitle}</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : isActorFacing ? '+ Demander activation / mise a jour' : '+ Nouvel acteur'}
        </button>
      </div>

      {!canManageActors && (
        <div className="card">
          <h2>Ce que vous pouvez faire</h2>
          <p className="process-label">
            Cet ecran est limite au parcours acteur. Les validations communales et la liste complete des demandes
            sont reservees aux roles Commune/COM/Admin.
          </p>
          <ul className="home-list">
            <li>Mettre a jour votre profil et votre rattachement territorial.</li>
            <li>Soumettre une demande d'activation avec frais d'ouverture.</li>
            <li>Suivre votre statut (pending/active) dans vos modules.</li>
          </ul>
        </div>
      )}

      {showValidationSection && (
        <div className="card validation-card">
          <h2>Validation mairie/commune apres paiement</h2>
          <div className="workflow-strip" aria-label="Etapes workflow">
            <span className="workflow-step active">1. Creation compte</span>
            <span className="workflow-step active">2. Paiement frais</span>
            <span className="workflow-step">3. Validation commune/maire</span>
          </div>
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
                    <th>Filieres</th>
                    <th>Frais ouverture</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingList.map((actor: any) => {
                    const fee = latestOpeningFeeByActor.get(actor.id)
                    const feeStatus = fee?.status ?? actor.opening_fee_status
                    const requiresPaidFee = Boolean(actor.opening_fee_id)
                    const canActivate = !requiresPaidFee || feeStatus === 'paid'
                    return (
                      <tr key={actor.id}>
                        <td><Link to={`/actors/${actor.id}`}>{actor.id}</Link></td>
                        <td>{actor.nom} {actor.prenoms}</td>
                        <td>{Array.isArray(actor.filieres) && actor.filieres.length ? actor.filieres.join(', ') : 'OR'}</td>
                        <td>
                          <span className={`status-badge status-${feeStatus ?? 'pending'}`}>{feeStatus ?? 'pending'}</span>
                          {fee?.id ? (
                            <>
                              {' '}
                              <Link to={`/fees/${fee.id}`}>Voir frais</Link>
                            </>
                          ) : null}
                        </td>
                        <td>
                          {fee?.id && feeStatus !== 'paid' && (
                            <button
                              type="button"
                              className="btn-secondary btn-sm"
                              onClick={() => markFeePaidMutation.mutate(fee.id)}
                              disabled={markFeePaidMutation.isPending}
                            >
                              Marquer paiement recu
                            </button>
                          )}
                          {' '}
                          <button
                            type="button"
                            className="btn-primary btn-sm icon-action icon-action-approve"
                            disabled={validateMutation.isPending || !canActivate}
                            onClick={() => validateMutation.mutate({ actorId: actor.id, status: 'active' })}
                            title={!canActivate ? "Paiement requis avant validation." : undefined}
                            aria-label={`Valider acteur ${actor.id}`}
                          >
                            ✓
                          </button>
                          {' '}
                          <button
                            type="button"
                            className="btn-secondary btn-sm icon-action icon-action-reject"
                            disabled={validateMutation.isPending}
                            onClick={() => validateMutation.mutate({ actorId: actor.id, status: 'rejected' })}
                            aria-label={`Refuser acteur ${actor.id}`}
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {showForm && (
        <div className="card form-card">
          <h2>Inscription acteur multi-role / multi-filiere</h2>
          <p className="process-label">
            L acteur peut etre rattache a plusieurs roles et plusieurs filieres des la creation.
          </p>
          {regions.length === 0 ? (
            <p className="form-warning">Aucun territoire configure. Chargez d abord le referentiel territorial.</p>
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
                  <label htmlFor="prenoms">Prenoms</label>
                  <input type="text" id="prenoms" name="prenoms" />
                </div>
                <div className="form-group">
                  <label htmlFor="email">Email *</label>
                  <input type="email" id="email" name="email" required />
                </div>
                <div className="form-group">
                  <label htmlFor="telephone">Telephone *</label>
                  <input type="tel" id="telephone" name="telephone" required placeholder="0340000000" />
                  <span className="form-hint">Format: 03XXXXXXXX</span>
                </div>
                <div className="form-group">
                  <label htmlFor="password">Mot de passe *</label>
                  <input type="password" id="password" name="password" required minLength={6} />
                </div>
                <div className="form-group">
                  <label htmlFor="region_code">Region *</label>
                  <select id="region_code" name="region_code" required value={regionCode} onChange={(e) => setRegionCode(e.target.value)}>
                    <option value="">-- Choisir --</option>
                    {regions.map((r: { code: string; name: string }) => (
                      <option key={r.code} value={r.code}>{r.name}</option>
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
                    <option value="">-- Choisir --</option>
                    {districts.map((d: { code: string; name: string }) => (
                      <option key={d.code} value={d.code}>{d.name}</option>
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
                    <option value="">-- Choisir --</option>
                    {communes.map((c: { code: string; name: string }) => (
                      <option key={c.code} value={c.code}>{c.name}</option>
                    ))}
                  </select>
                  {selectedCommune?.commune_mobile_money_msisdn && (
                    <span className="form-hint">
                      Beneficiaire communal: {selectedCommune.commune_mobile_money_msisdn}
                    </span>
                  )}
                </div>
                <div className="form-group">
                  <label htmlFor="fokontany_code">Fokontany</label>
                  <select id="fokontany_code" name="fokontany_code" disabled={!communeCode}>
                    <option value="">-- Optionnel --</option>
                    {fokontanyList.map((f: { code?: string; name: string }) => (
                      <option key={f.code ?? f.name} value={f.code ?? ''}>{f.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Roles (multi-selection) *</label>
                  <div className="choice-inline-grid">
                    {rbacRolesLoading ? (
                      <p className="form-hint">Chargement des roles...</p>
                    ) : roleOptionsForCreate.map((role) => (
                      <label key={role.value} className="choice-inline">
                        <input
                          type="checkbox"
                          checked={selectedRolesForCreate.includes(role.value)}
                          disabled={!canManageActors}
                          onChange={() => handleRoleToggle(role.value)}
                        />
                        <span>{role.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label>Filieres (multi-selection) *</label>
                  <div className="choice-inline-grid">
                    {filiereOptionsForCreate.map((filiere) => (
                      <label key={filiere} className="choice-inline">
                        <input
                          type="checkbox"
                          checked={selectedFilieresForCreate.includes(filiere)}
                          disabled={!canManageActors}
                          onChange={() => handleFiliereToggle(filiere)}
                        />
                        <span>{filiere}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label htmlFor="provider_code">Paiement frais ouverture</label>
                  <select id="provider_code" name="provider_code" value={providerCode} onChange={(e) => setProviderCode(e.target.value)}>
                    <option value="mvola">Mvola</option>
                    <option value="orange_money">Orange Money</option>
                    <option value="airtel_money">Airtel Money</option>
                  </select>
                </div>
                <div className="form-group form-group-map">
                  <label>Lieu inscription (cliquez sur la carte) *</label>
                  <div className="map-wrapper">
                    <MapContainer center={[mapLat, mapLon]} zoom={6} style={{ height: '280px', width: '100%' }} scrollWheelZoom>
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      <MapClickHandler onSelect={(lat, lon) => { setMapLat(lat); setMapLon(lon) }} />
                      <Marker position={[mapLat, mapLon]} icon={defaultIcon}>
                        <Popup>Lieu inscription</Popup>
                      </Marker>
                    </MapContainer>
                  </div>
                  <span className="form-hint">
                    Latitude: {mapLat.toFixed(5)} - Longitude: {mapLon.toFixed(5)}
                  </span>
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

      {canManageActors && (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nom</th>
                  <th>Email</th>
                  <th>Telephone</th>
                  <th>Filieres</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {data?.items?.length ? (
                  data.items.map((actor: any) => (
                    <tr key={actor.id}>
                      <td><Link to={`/actors/${actor.id}`}>{actor.id}</Link></td>
                      <td><Link to={`/actors/${actor.id}`}>{actor.nom} {actor.prenoms}</Link></td>
                      <td>{actor.email}</td>
                      <td>{actor.telephone}</td>
                      <td>{Array.isArray(actor.filieres) && actor.filieres.length ? actor.filieres.join(', ') : 'OR'}</td>
                      <td><span className={`status-badge status-${actor.status}`}>{actor.status}</span></td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6}>
                      <div className="empty-state-rich">
                        <div className="empty-title">Aucun acteur</div>
                        <p className="empty-desc">Inscrivez un acteur pour declencher le workflow creation, paiement, validation mairie.</p>
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
              <div className="pagination-info">Page {data.page} sur {data.total_pages} ({data.total} total)</div>
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
      )}
    </div>
  )
}
