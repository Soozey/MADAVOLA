import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'

export default function NotificationsPage() {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const canManageEmergency = userRoles.some((r) => ['admin', 'dirigeant', 'police', 'gendarmerie', 'bianco', 'forets', 'environnement'].includes(r))
  const [title, setTitle] = useState('Alerte terrain')
  const [messageInput, setMessageInput] = useState('')
  const [severity, setSeverity] = useState<'medium' | 'high' | 'critical'>('high')
  const [targetService, setTargetService] = useState<'police' | 'gendarmerie' | 'both' | 'bianco' | 'environnement' | 'institutionnel'>('both')
  const [filiere, setFiliere] = useState('OR')
  const [lat, setLat] = useState('')
  const [lon, setLon] = useState('')

  const { data: rows = [], isLoading, refetch } = useQuery({
    queryKey: ['notifications', user?.id],
    queryFn: () => api.getNotifications(user?.id ? { actor_id: user.id } : undefined),
    enabled: !!user,
  })
  const { data: emergencyRows = [], isLoading: emergencyLoading } = useQuery({
    queryKey: ['emergency-alerts'],
    queryFn: () => api.getEmergencyAlerts(),
    enabled: !!user,
  })

  const runMutation = useMutation({
    mutationFn: () => api.runExpiryReminders('30,7,1'),
    onSuccess: (data) => {
      toast.success(`Rappels executes: ${data.created_notifications}`)
      refetch()
    },
  })
  const emergencyCreateMutation = useMutation({
    mutationFn: async () => {
      let geoPointId: number | undefined
      if (lat && lon) {
        const geo = await api.createGeoPoint({
          lat: Number(lat),
          lon: Number(lon),
          accuracy_m: 20,
          source: 'web_emergency',
        })
        geoPointId = geo.id
      }
      return api.createEmergencyAlert({
        title,
        message: messageInput,
        severity,
        target_service: targetService,
        filiere,
        geo_point_id: geoPointId,
      })
    },
    onSuccess: () => {
      toast.success('Alerte d urgence envoyee.')
      setMessageInput('')
      setLat('')
      setLon('')
      queryClient.invalidateQueries({ queryKey: ['emergency-alerts'] })
    },
    onError: (err) => {
      toast.error(getErrorMessage(err, 'Envoi alerte impossible'))
    },
  })

  const emergencyStatusMutation = useMutation({
    mutationFn: (payload: { id: number; status: 'acknowledged' | 'resolved' | 'rejected' }) =>
      api.updateEmergencyAlertStatus(payload.id, payload.status),
    onSuccess: () => {
      toast.success('Statut alerte mis a jour')
      queryClient.invalidateQueries({ queryKey: ['emergency-alerts'] })
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Mise a jour alerte impossible')),
  })

  return (
    <div className="dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Notifications</h1>
        <button className="btn-primary" onClick={() => runMutation.mutate()} disabled={runMutation.isPending}>Lancer rappels</button>
      </div>
      <div className="card">
        <h2>Alerte d urgence vers Police/Gendarmerie</h2>
        <div className="form-grid">
          <div className="form-group">
            <label>Titre</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Message</label>
            <input value={messageInput} onChange={(e) => setMessageInput(e.target.value)} placeholder="Decrivez la situation..." />
          </div>
          <div className="form-group">
            <label>Service cible</label>
            <select
              value={targetService}
              onChange={(e) => setTargetService(e.target.value as 'police' | 'gendarmerie' | 'both' | 'bianco' | 'environnement' | 'institutionnel')}
            >
              <option value="both">Police + Gendarmerie</option>
              <option value="police">Police</option>
              <option value="gendarmerie">Gendarmerie</option>
              <option value="bianco">BIANCO</option>
              <option value="environnement">Environnement / Forets</option>
              <option value="institutionnel">Tous institutionnels</option>
            </select>
          </div>
          <div className="form-group">
            <label>Severite</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value as 'medium' | 'high' | 'critical')}>
              <option value="medium">Moyenne</option>
              <option value="high">Haute</option>
              <option value="critical">Critique</option>
            </select>
          </div>
          <div className="form-group">
            <label>Filiere</label>
            <select value={filiere} onChange={(e) => setFiliere(e.target.value)}>
              <option value="OR">OR</option>
              <option value="PIERRE">PIERRE</option>
              <option value="BOIS">BOIS</option>
            </select>
          </div>
          <div className="form-group">
            <label>Latitude (optionnel)</label>
            <input value={lat} onChange={(e) => setLat(e.target.value)} placeholder="-18.8792" />
          </div>
          <div className="form-group">
            <label>Longitude (optionnel)</label>
            <input value={lon} onChange={(e) => setLon(e.target.value)} placeholder="47.5079" />
          </div>
        </div>
        <div className="form-actions">
          <button
            className="btn-primary"
            onClick={() => emergencyCreateMutation.mutate()}
            disabled={emergencyCreateMutation.isPending || !messageInput.trim()}
          >
            {emergencyCreateMutation.isPending ? 'Envoi...' : 'Envoyer alerte'}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="loading">Chargement...</div>
      ) : rows.length === 0 ? (
        <div className="card"><p>Aucune notification.</p></div>
      ) : (
        <div className="card">
          <ul className="list">
            {(rows as any[]).map((n: any) => (
              <li key={n.id} className="list-item">
                <div className="list-item-content">
                  <div className="list-item-title">{n.message}</div>
                  <div className="list-item-subtitle">{n.entity_type} #{n.entity_id} - J-{n.days_before} - {n.status}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h2>Alertes d urgence</h2>
        {emergencyLoading ? (
          <div className="loading">Chargement...</div>
        ) : (emergencyRows as any[]).length === 0 ? (
          <p>Aucune alerte d urgence.</p>
        ) : (
          <ul className="list">
            {(emergencyRows as any[]).map((n: any) => (
              <li key={n.id} className="list-item">
                <div className="list-item-content">
                  <div className="list-item-title">{n.title} - {n.severity.toUpperCase()}</div>
                  <div className="list-item-subtitle">
                    {n.target_service} | {n.filiere || '-'} | statut: <strong>{n.status}</strong>
                  </div>
                  <div className="list-item-subtitle">{n.message}</div>
                  {canManageEmergency && (
                    <div className="form-actions" style={{ marginTop: 8 }}>
                      <button className="btn-secondary" onClick={() => emergencyStatusMutation.mutate({ id: n.id, status: 'acknowledged' })}>Accuser reception</button>
                      <button className="btn-secondary" onClick={() => emergencyStatusMutation.mutate({ id: n.id, status: 'resolved' })}>Resoudre</button>
                      <button className="btn-secondary" onClick={() => emergencyStatusMutation.mutate({ id: n.id, status: 'rejected' })}>Rejeter</button>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
