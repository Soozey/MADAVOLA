import { FormEvent, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../lib/apiErrors'

export default function AdminConfigPage() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [search, setSearch] = useState('')
  const [key, setKey] = useState('')
  const [value, setValue] = useState('')
  const [description, setDescription] = useState('')
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ['admin-configs', search],
    queryFn: () => api.listAdminConfigs(search.trim() ? { key: search.trim() } : undefined),
  })

  const createMutation = useMutation({
    mutationFn: () => api.createAdminConfig({ key: key.trim(), value, description }),
    onSuccess: () => {
      toast.success('Configuration creee')
      setKey('')
      setValue('')
      setDescription('')
      queryClient.invalidateQueries({ queryKey: ['admin-configs'] })
    },
    onError: (e) => toast.error(getErrorMessage(e, 'Creation impossible')),
  })

  const patchMutation = useMutation({
    mutationFn: () => {
      if (!selectedId) throw new Error('Config non selectionnee')
      return api.patchAdminConfig(selectedId, { value, description })
    },
    onSuccess: () => {
      toast.success('Configuration mise a jour')
      queryClient.invalidateQueries({ queryKey: ['admin-configs'] })
    },
    onError: (e) => toast.error(getErrorMessage(e, 'Mise a jour impossible')),
  })

  const deleteMutation = useMutation({
    mutationFn: () => {
      if (!selectedId) throw new Error('Config non selectionnee')
      return api.deleteAdminConfig(selectedId)
    },
    onSuccess: () => {
      toast.success('Configuration supprimee')
      setSelectedId(null)
      setKey('')
      setValue('')
      setDescription('')
      queryClient.invalidateQueries({ queryKey: ['admin-configs'] })
    },
    onError: (e) => toast.error(getErrorMessage(e, 'Suppression impossible')),
  })

  const selectedRow = useMemo(
    () => (Array.isArray(rows) ? rows.find((r: any) => r.id === selectedId) : null),
    [rows, selectedId]
  )

  const onCreate = (e: FormEvent) => {
    e.preventDefault()
    if (!key.trim()) return toast.error('La cle est obligatoire')
    createMutation.mutate()
  }

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Admin Config</h1>
      </div>
      <p className="dashboard-subtitle">Gestion dediee de `/admin/config` (create/list/update/delete).</p>

      <div className="card">
        <h2>Rechercher</h2>
        <div className="form-grid">
          <div className="form-group">
            <label>Filtre par cle</label>
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="ex: fee.policy" />
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Creer / Modifier</h2>
        <form onSubmit={onCreate}>
          <div className="form-grid">
            <div className="form-group">
              <label>Key *</label>
              <input
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="system.flag.demo"
                disabled={!!selectedId}
              />
            </div>
            <div className="form-group">
              <label>Value</label>
              <input value={value} onChange={(e) => setValue(e.target.value)} placeholder="true" />
            </div>
            <div className="form-group">
              <label>Description</label>
              <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Feature flag" />
            </div>
          </div>
          <div className="form-actions">
            {!selectedId && (
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creation...' : 'Creer'}
              </button>
            )}
            {selectedId && (
              <>
                <button type="button" className="btn-primary" onClick={() => patchMutation.mutate()} disabled={patchMutation.isPending}>
                  {patchMutation.isPending ? 'Maj...' : 'Mettre a jour'}
                </button>
                <button type="button" className="btn-secondary" onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending}>
                  {deleteMutation.isPending ? 'Suppression...' : 'Supprimer'}
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setSelectedId(null)
                    setKey('')
                    setValue('')
                    setDescription('')
                  }}
                >
                  Annuler
                </button>
              </>
            )}
          </div>
        </form>
        {selectedRow && (
          <small style={{ color: '#5b6475' }}>
            Selection en cours: #{selectedRow.id} ({selectedRow.key})
          </small>
        )}
      </div>

      <div className="card">
        <h2>Configurations</h2>
        {isLoading ? (
          <div className="loading">Chargement...</div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Key</th>
                  <th>Value</th>
                  <th>Description</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {(rows as any[]).map((row: any) => (
                  <tr key={row.id}>
                    <td>{row.id}</td>
                    <td>{row.key}</td>
                    <td>{row.value || '-'}</td>
                    <td>{row.description || '-'}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => {
                          setSelectedId(row.id)
                          setKey(row.key || '')
                          setValue(row.value || '')
                          setDescription(row.description || '')
                        }}
                      >
                        Editer
                      </button>
                    </td>
                  </tr>
                ))}
                {(rows as any[]).length === 0 && (
                  <tr>
                    <td colSpan={5}>Aucune configuration.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

