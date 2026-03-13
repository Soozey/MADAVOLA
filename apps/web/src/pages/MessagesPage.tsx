import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'

export default function MessagesPage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [targetActorId, setTargetActorId] = useState('')
  const [conversationActorId, setConversationActorId] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { data: contacts = [] } = useQuery({
    queryKey: ['messages', 'contacts'],
    queryFn: () => api.listContactRequests(),
    enabled: !!user,
  })

  const { data: messages = [] } = useQuery({
    queryKey: ['messages', 'list', conversationActorId],
    queryFn: () => api.listMessages(conversationActorId ? { with_actor_id: Number(conversationActorId) } : undefined),
    enabled: !!user,
  })

  const contactRequestMutation = useMutation({
    mutationFn: (id: number) => api.createContactRequest(id),
    onSuccess: () => {
      setSuccess('Demande de contact envoyee.')
      setError('')
      setTargetActorId('')
      queryClient.invalidateQueries({ queryKey: ['messages', 'contacts'] })
    },
    onError: (err) => {
      setError(getErrorMessage(err, 'Demande de contact impossible.'))
      setSuccess('')
    },
  })

  const contactDecisionMutation = useMutation({
    mutationFn: ({ id, decision }: { id: number; decision: 'accepted' | 'rejected' }) => api.decideContactRequest(id, decision),
    onSuccess: () => {
      setSuccess('Decision enregistree.')
      setError('')
      queryClient.invalidateQueries({ queryKey: ['messages', 'contacts'] })
    },
    onError: (err) => {
      setError(getErrorMessage(err, 'Decision contact impossible.'))
      setSuccess('')
    },
  })

  const sendMessageMutation = useMutation({
    mutationFn: () => api.sendMessage({ receiver_actor_id: Number(conversationActorId), body: newMessage }),
    onSuccess: () => {
      setSuccess('Message envoye.')
      setError('')
      setNewMessage('')
      queryClient.invalidateQueries({ queryKey: ['messages', 'list'] })
    },
    onError: (err) => {
      setError(getErrorMessage(err, 'Envoi message impossible.'))
      setSuccess('')
    },
  })

  const pendingForMe = useMemo(
    () => (contacts as any[]).filter((c) => c.status === 'pending' && c.target_actor_id === user?.id),
    [contacts, user?.id]
  )

  const onSubmitContact = (event: FormEvent) => {
    event.preventDefault()
    const target = Number(targetActorId)
    if (!Number.isFinite(target) || target <= 0) return
    contactRequestMutation.mutate(target)
  }

  return (
    <div className="dashboard">
      <h1>Messagerie</h1>
      <p className="dashboard-subtitle">Demande de contact, acceptation/refus, puis messages entre acteurs.</p>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}

      <div className="dashboard-grid">
        <section className="card">
          <h2>Demander un contact</h2>
          <form onSubmit={onSubmitContact}>
            <div className="form-group">
              <label htmlFor="targetActorId">ID acteur cible</label>
              <input
                id="targetActorId"
                value={targetActorId}
                onChange={(e) => setTargetActorId(e.target.value)}
                placeholder="Ex: 23"
              />
            </div>
            <button className="btn-primary" type="submit" disabled={contactRequestMutation.isPending || !targetActorId}>
              {contactRequestMutation.isPending ? 'Envoi...' : 'Envoyer demande'}
            </button>
          </form>

          <h3 style={{ marginTop: 16 }}>Demandes en attente pour moi</h3>
          <ul className="home-list">
            {pendingForMe.length === 0 && <li>Aucune demande en attente.</li>}
            {pendingForMe.map((row: any) => (
              <li key={row.id}>
                Demande #{row.id} de {row.requester_name || `acteur ${row.requester_actor_id}`}
                <button
                  className="btn-primary"
                  style={{ marginLeft: 8 }}
                  onClick={() => contactDecisionMutation.mutate({ id: row.id, decision: 'accepted' })}
                >
                  Accepter
                </button>
                <button
                  className="btn-secondary"
                  style={{ marginLeft: 8 }}
                  onClick={() => contactDecisionMutation.mutate({ id: row.id, decision: 'rejected' })}
                >
                  Refuser
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2>Conversation</h2>
          <div className="form-group">
            <label htmlFor="conversationActorId">ID acteur contact</label>
            <input
              id="conversationActorId"
              value={conversationActorId}
              onChange={(e) => setConversationActorId(e.target.value)}
              placeholder="Ex: 23"
            />
          </div>
          <div className="form-group">
            <label htmlFor="newMessage">Nouveau message</label>
            <textarea id="newMessage" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} rows={3} />
          </div>
          <button
            className="btn-primary"
            disabled={sendMessageMutation.isPending || !conversationActorId || !newMessage.trim()}
            onClick={() => sendMessageMutation.mutate()}
          >
            {sendMessageMutation.isPending ? 'Envoi...' : 'Envoyer'}
          </button>

          <h3 style={{ marginTop: 16 }}>Historique</h3>
          <ul className="home-list">
            {(messages as any[]).length === 0 && <li>Aucun message.</li>}
            {(messages as any[]).map((row: any) => (
              <li key={row.id}>
                <strong>{row.sender_name || row.sender_actor_id}</strong> - {row.body}
                <div style={{ color: '#6b7b95' }}>{new Date(row.created_at).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
