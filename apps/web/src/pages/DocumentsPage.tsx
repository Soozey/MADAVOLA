import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'

type DocumentRow = {
  id: number
  doc_type: string
  owner_actor_id: number
  related_entity_type?: string | null
  related_entity_id?: string | null
  original_filename: string
  sha256: string
}

export default function DocumentsPage() {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [ownerActorId, setOwnerActorId] = useState<string>('')
  const [docTypeFilter, setDocTypeFilter] = useState<string>('')
  const [relatedEntityType, setRelatedEntityType] = useState<string>('')
  const [relatedEntityId, setRelatedEntityId] = useState<string>('')
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null)

  const [uploadDocType, setUploadDocType] = useState('piece_identite')
  const [uploadRelatedType, setUploadRelatedType] = useState('actor')
  const [uploadRelatedId, setUploadRelatedId] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)

  const ownerActorIdNum = ownerActorId ? Number(ownerActorId) : undefined

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents', ownerActorIdNum, docTypeFilter, relatedEntityType, relatedEntityId],
    queryFn: () =>
      api.getDocuments({
        owner_actor_id: ownerActorIdNum,
        doc_type: docTypeFilter || undefined,
        related_entity_type: relatedEntityType || undefined,
        related_entity_id: relatedEntityId || undefined,
      }) as Promise<DocumentRow[]>,
  })

  const { data: selectedDoc } = useQuery({
    queryKey: ['document', selectedDocId],
    queryFn: () => api.getDocument(selectedDocId as number),
    enabled: selectedDocId != null,
  })

  const uploadMutation = useMutation({
    mutationFn: () =>
      api.uploadDocument({
        doc_type: uploadDocType,
        owner_actor_id: ownerActorIdNum ?? user?.id ?? 0,
        related_entity_type: uploadRelatedType || undefined,
        related_entity_id: uploadRelatedId || undefined,
        file: uploadFile as File,
      }),
    onSuccess: () => {
      toast.success('Document charge.')
      setUploadFile(null)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
    onError: (error) => toast.error(getErrorMessage(error, 'Televersement impossible.')),
  })

  const canUpload = useMemo(
    () => !!uploadFile && !!(ownerActorIdNum ?? user?.id),
    [uploadFile, ownerActorIdNum, user?.id]
  )

  const handleUpload = (e: FormEvent) => {
    e.preventDefault()
    if (!canUpload) return
    uploadMutation.mutate()
  }

  return (
    <div className="dashboard">
      <h1>Documents</h1>
      <p className="dashboard-subtitle">Branchement complet de l'API documents: liste, detail et televersement.</p>

      <div className="card tasks-of-day">
        <h2>Taches du jour</h2>
        <p className="process-label">
          Televersez un document, puis verifiez qu'il est bien lie a l'acteur et a l'objet metier attendu.
        </p>
        <div className="tasks-actions">
          <button
            type="button"
            className="btn-primary"
            onClick={() => document.getElementById('documents-upload')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Televerser un document
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => document.getElementById('documents-list')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Acceder a la liste des documents
          </button>
        </div>
      </div>

      <div className="card">
        <h2>Filtres</h2>
        <div className="filters-grid">
          <div className="filter-group">
            <label>acteur proprietaire (actor_id)</label>
            <input value={ownerActorId} onChange={(e) => setOwnerActorId(e.target.value)} placeholder={`${user?.id ?? ''}`} />
          </div>
          <div className="filter-group">
            <label>Type document</label>
            <input value={docTypeFilter} onChange={(e) => setDocTypeFilter(e.target.value)} placeholder="piece_identite" />
          </div>
          <div className="filter-group">
            <label>Type d'entite liee</label>
            <input value={relatedEntityType} onChange={(e) => setRelatedEntityType(e.target.value)} placeholder="actor|lot|export" />
          </div>
          <div className="filter-group">
            <label>ID entite liee</label>
            <input value={relatedEntityId} onChange={(e) => setRelatedEntityId(e.target.value)} placeholder="12" />
          </div>
        </div>
      </div>

      <div id="documents-upload" className="card">
        <h2>Televerser un document</h2>
        <form onSubmit={handleUpload}>
          <div className="form-grid">
            <div className="form-group">
              <label>Type de document</label>
              <input value={uploadDocType} onChange={(e) => setUploadDocType(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>acteur proprietaire (actor_id)</label>
              <input value={ownerActorId} onChange={(e) => setOwnerActorId(e.target.value)} placeholder={`${user?.id ?? ''}`} />
            </div>
            <div className="form-group">
              <label>Type d'entite liee</label>
              <input value={uploadRelatedType} onChange={(e) => setUploadRelatedType(e.target.value)} placeholder="actor|lot|export" />
            </div>
            <div className="form-group">
              <label>ID entite liee</label>
              <input value={uploadRelatedId} onChange={(e) => setUploadRelatedId(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Fichier</label>
              <input
                type="file"
                onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                required
              />
            </div>
          </div>
          <button type="submit" className="btn-primary" disabled={!canUpload || uploadMutation.isPending}>
            {uploadMutation.isPending ? 'Televersement...' : 'Televerser'}
          </button>
        </form>
      </div>

      <div id="documents-list" className="card">
        <h2>Liste documents</h2>
        {isLoading ? (
          <div className="loading">Chargement...</div>
        ) : documents.length === 0 ? (
          <p className="empty-state">Aucun document.</p>
        ) : (
          <ul className="list">
            {documents.map((doc) => (
              <li key={doc.id} className="list-item">
                <div className="list-item-content">
                  <div className="list-item-title">
                    #{doc.id} - {doc.doc_type}
                  </div>
                  <div className="list-item-subtitle">
                    proprietaire #{doc.owner_actor_id} - {doc.original_filename}
                    {doc.related_entity_type ? ` - ${doc.related_entity_type}:${doc.related_entity_id}` : ''}
                  </div>
                </div>
                <button className="btn-secondary" onClick={() => setSelectedDocId(doc.id)}>Voir</button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {selectedDoc && (
        <div className="card">
          <h2>Detail du document #{selectedDoc.id}</h2>
          <pre>{JSON.stringify(selectedDoc, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
