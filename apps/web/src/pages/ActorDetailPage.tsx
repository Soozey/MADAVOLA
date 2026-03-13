import { useParams, Link } from 'react-router-dom'
import { FormEvent, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'

export default function ActorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const actorId = id ? parseInt(id, 10) : NaN
  const queryClient = useQueryClient()
  const toast = useToast()
  const [filiere, setFiliere] = useState('BOIS')
  const [authorizationType, setAuthorizationType] = useState('autorisation_generique')
  const [numero, setNumero] = useState('')
  const [validFrom, setValidFrom] = useState('')
  const [validTo, setValidTo] = useState('')
  const [status, setStatus] = useState('active')
  const [notes, setNotes] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['actor', actorId],
    queryFn: () => api.getActor(actorId),
    enabled: Number.isInteger(actorId),
  })
  const { data: authorizations = [], isLoading: loadingAuth } = useQuery({
    queryKey: ['actor-authorizations', actorId],
    queryFn: () => api.getActorAuthorizations(actorId),
    enabled: Number.isInteger(actorId),
  })
  const { data: actorRoles = [] } = useQuery({
    queryKey: ['actor-roles', actorId],
    queryFn: () => api.getActorRoles(actorId),
    enabled: Number.isInteger(actorId),
  })

  const createAuthorization = useMutation({
    mutationFn: () =>
      api.createActorAuthorization(actorId, {
        filiere,
        authorization_type: authorizationType,
        numero,
        valid_from: new Date(validFrom).toISOString(),
        valid_to: new Date(validTo).toISOString(),
        status,
        notes: notes || undefined,
      }),
    onSuccess: () => {
      toast.success('Autorisation enregistree.')
      queryClient.invalidateQueries({ queryKey: ['actor-authorizations', actorId] })
      setNumero('')
      setValidFrom('')
      setValidTo('')
      setNotes('')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Creation autorisation impossible.')),
  })

  const handleCreateAuthorization = (e: FormEvent) => {
    e.preventDefault()
    if (!numero || !validFrom || !validTo) return
    createAuthorization.mutate()
  }

  if (!Number.isInteger(actorId)) {
    return (
      <div className="dashboard">
        <p className="error">ID d'acteur invalide.</p>
        <Link to="/actors">Retour aux acteurs</Link>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dashboard">
        <h1>Acteur #{actorId}</h1>
        <p className="error">Erreur lors du chargement.</p>
        <Link to="/actors">Retour aux acteurs</Link>
      </div>
    )
  }

  if (isLoading) return <div className="loading">Chargement...</div>
  if (!data) return null

  return (
    <div className="dashboard">
      <h1>Acteur #{data.id}</h1>
      <p className="dashboard-subtitle">
        <Link to="/actors">← Retour aux acteurs</Link>
      </p>
      <div className="card">
        <div className="profile-info">
          <div className="info-item">
            <span className="info-label">Nom</span>
            <span className="info-value">{data.nom} {data.prenoms}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Email</span>
            <span className="info-value">{data.email || '—'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Téléphone</span>
            <span className="info-value">{data.telephone}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Région / District / Commune</span>
            <span className="info-value">{data.region_code} / {data.district_code} / {data.commune_code}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Statut</span>
            <span className="info-value">{data.status}</span>
          </div>
        </div>
      </div>
      <div className="card">
        <h2>Roles actifs</h2>
        {Array.isArray(actorRoles) && actorRoles.length ? (
          <ul className="home-list">
            {actorRoles.map((row: { id: number; role: string; status: string; valid_to?: string | null }) => (
              <li key={row.id}>
                {row.role} | {row.status}{row.valid_to ? ` | exp=${new Date(row.valid_to).toLocaleDateString()}` : ''}
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-state">Aucun role.</p>
        )}
      </div>

      <div className="card">
        <h2>Autorisations / Cartes</h2>
        <p className="dashboard-subtitle">Branchage API: `GET/POST /actors/{'{id}'}/authorizations`.</p>
        <form onSubmit={handleCreateAuthorization}>
          <div className="form-grid">
            <div className="form-group">
              <label>Filiere</label>
              <select value={filiere} onChange={(e) => setFiliere(e.target.value)}>
                <option value="OR">OR</option>
                <option value="PIERRE">PIERRE</option>
                <option value="BOIS">BOIS</option>
              </select>
            </div>
            <div className="form-group">
              <label>Type</label>
              <input value={authorizationType} onChange={(e) => setAuthorizationType(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Numero</label>
              <input value={numero} onChange={(e) => setNumero(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Debut</label>
              <input type="datetime-local" value={validFrom} onChange={(e) => setValidFrom(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Fin</label>
              <input type="datetime-local" value={validTo} onChange={(e) => setValidTo(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Statut</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="active">active</option>
                <option value="suspended">suspended</option>
                <option value="expired">expired</option>
              </select>
            </div>
            <div className="form-group">
              <label>Notes</label>
              <input value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
          </div>
          <button className="btn-primary" type="submit" disabled={createAuthorization.isPending}>
            {createAuthorization.isPending ? 'Enregistrement...' : 'Ajouter autorisation'}
          </button>
        </form>
        {loadingAuth ? (
          <div className="loading">Chargement autorisations...</div>
        ) : authorizations.length === 0 ? (
          <p className="empty-state">Aucune autorisation.</p>
        ) : (
          <ul className="list" style={{ marginTop: '1rem' }}>
            {authorizations.map((row: {
              id: number
              filiere: string
              authorization_type: string
              numero: string
              status: string
              valid_from: string
              valid_to: string
            }) => (
              <li key={row.id} className="list-item">
                <div className="list-item-content">
                  <div className="list-item-title">
                    #{row.id} - {row.filiere} - {row.authorization_type} - {row.numero}
                  </div>
                  <div className="list-item-subtitle">
                    {row.status} | {new Date(row.valid_from).toLocaleString()} - {new Date(row.valid_to).toLocaleString()}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
