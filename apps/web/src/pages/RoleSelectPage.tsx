import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AppRole, getRoleLabel } from '../config/rbac'
import { useSession } from '../contexts/SessionContext'
import { api } from '../lib/api'
import type { RbacRoleOut } from '../lib/api'
import './SessionSetup.css'

type ActorTypeFilter = 'all' | 'USAGER' | 'AGENT_ETAT' | 'OPERATEUR_PRIVE' | 'TRANSVERSAL'
const RECENT_ROLES_KEY = 'recentRoles'
const FAVORITE_ROLES_KEY = 'favoriteRoles'

export default function RoleSelectPage() {
  const navigate = useNavigate()
  const { selectedRole, setSelectedRole, setSelectedFiliere } = useSession()
  const [draftRole, setDraftRole] = useState<AppRole | null>(selectedRole ?? null)
  const [searchText, setSearchText] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [actorTypeFilter, setActorTypeFilter] = useState<ActorTypeFilter>('all')
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})
  const [viewFilter, setViewFilter] = useState<'all' | 'favorites' | 'recent'>('all')
  const [recentRoles, setRecentRoles] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(RECENT_ROLES_KEY) || '[]')
    } catch {
      return []
    }
  })
  const [favoriteRoles, setFavoriteRoles] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(FAVORITE_ROLES_KEY) || '[]')
    } catch {
      return []
    }
  })

  const { data: roleRows = [], isLoading, isError } = useQuery({
    queryKey: ['rbac', 'roles', searchText, categoryFilter, actorTypeFilter],
    queryFn: () =>
      api.getRbacRoles({
        include_common: true,
        search: searchText.trim() || undefined,
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
        actor_type: actorTypeFilter !== 'all' ? actorTypeFilter : undefined,
        active_only: true,
        for_current_actor: true,
      }) as Promise<RbacRoleOut[]>,
  })
  const { data: rolePermissions = [] } = useQuery({
    queryKey: ['rbac', 'permissions', draftRole],
    queryFn: async () => {
      if (!draftRole) return []
      const out = await api.getRbacPermissions(draftRole)
      return out.permissions || []
    },
    enabled: !!draftRole,
  })

  const roleOptions = useMemo(() => {
    return roleRows.map((row) => ({
      code: row.code,
      label: row.label || getRoleLabel(row.code),
      description: row.description || '',
      category: row.category || 'Autres',
      actorType: row.actor_type || 'TRANSVERSAL',
      order: row.display_order ?? 999,
      tags: row.tags || [],
    }))
  }, [roleRows])

  const categoryOptions = useMemo(() => {
    const names = Array.from(new Set(roleOptions.map((r) => r.category))).sort((a, b) => a.localeCompare(b))
    return ['all', ...names]
  }, [roleOptions])

  const groupedRoles = useMemo(() => {
    let filtered = roleOptions
    if (viewFilter === 'favorites') {
      filtered = filtered.filter((role) => favoriteRoles.includes(role.code))
    }
    if (viewFilter === 'recent') {
      filtered = filtered.filter((role) => recentRoles.includes(role.code))
    }
    const map: Record<string, typeof roleOptions> = {}
    for (const role of filtered) {
      if (!map[role.category]) map[role.category] = []
      map[role.category].push(role)
    }
    for (const group of Object.values(map)) {
      group.sort((a, b) => a.order - b.order || a.label.localeCompare(b.label))
    }
    return Object.entries(map).sort((a, b) => a[0].localeCompare(b[0]))
  }, [roleOptions, favoriteRoles, recentRoles, viewFilter])

  useEffect(() => {
    if (roleOptions.length === 0) {
      setDraftRole(null)
      return
    }
    const stillValid = draftRole && roleOptions.some((role) => role.code === draftRole)
    if (!stillValid) {
      setDraftRole(roleOptions[0].code)
    }
  }, [roleOptions, draftRole])

  useEffect(() => {
    const next: Record<string, boolean> = {}
    for (const [group] of groupedRoles) {
      next[group] = collapsed[group] ?? false
    }
    setCollapsed(next)
  }, [groupedRoles.length])

  useEffect(() => {
    if (!import.meta.env.DEV) return
    console.info('[select-role] roles=', roleOptions.length)
  }, [roleOptions.length])

  useEffect(() => {
    if (!import.meta.env.DEV) return
    if (!draftRole) return
    console.info('[select-role] chosen-role=', draftRole)
  }, [draftRole])

  const handleValidate = (roleToPersist?: AppRole) => {
    const role = roleToPersist ?? draftRole
    if (!role) return
    setSelectedRole(role)
    setSelectedFiliere(null)
    setRecentRoles((prev) => {
      const next = [role, ...prev.filter((x) => x !== role)].slice(0, 8)
      localStorage.setItem(RECENT_ROLES_KEY, JSON.stringify(next))
      return next
    })
    navigate('/select-filiere')
  }

  const toggleFavorite = (roleCode: string) => {
    setFavoriteRoles((prev) => {
      const exists = prev.includes(roleCode)
      const next = exists ? prev.filter((x) => x !== roleCode) : [roleCode, ...prev].slice(0, 20)
      localStorage.setItem(FAVORITE_ROLES_KEY, JSON.stringify(next))
      return next
    })
  }

  return (
    <div className="session-page">
      <div className="session-card">
        <h1 className="session-title">Choisir votre role</h1>
        <p className="session-subtitle">
          Etape A - Selection du role (source unique: API RBAC). Etape suivante: selection de la filiere.
        </p>

        <div className="role-sticky-controls">
          <div className="role-filters-grid">
            <select
              aria-label="Filtrer par type acteur"
              value={actorTypeFilter}
              onChange={(e) => setActorTypeFilter(e.target.value as ActorTypeFilter)}
            >
              <option value="all">Tous profils</option>
              <option value="USAGER">Usager</option>
              <option value="AGENT_ETAT">Agent de l'Etat</option>
              <option value="OPERATEUR_PRIVE">Operateur prive</option>
              <option value="TRANSVERSAL">Transversal</option>
            </select>
            <input
              aria-label="Rechercher un role"
              placeholder="Rechercher un role, un code, un tag..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <select
              aria-label="Filtrer par categorie"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              {categoryOptions.map((cat) => (
                <option key={cat} value={cat}>
                  {cat === 'all' ? 'Toutes les categories' : cat}
                </option>
              ))}
            </select>
            <div className="filiere-chips" aria-label="Vues rapides des roles">
              <button type="button" className={`chip ${viewFilter === 'all' ? 'active' : ''}`} onClick={() => setViewFilter('all')}>
                Tous
              </button>
              <button type="button" className={`chip ${viewFilter === 'favorites' ? 'active' : ''}`} onClick={() => setViewFilter('favorites')}>
                Favoris ({favoriteRoles.length})
              </button>
              <button type="button" className={`chip ${viewFilter === 'recent' ? 'active' : ''}`} onClick={() => setViewFilter('recent')}>
                Recents ({recentRoles.length})
              </button>
            </div>
          </div>
        </div>

        <div className="role-list-shell" aria-live="polite">
          {isLoading && (
            <div className="role-skeleton-list">
              <div className="role-skeleton" />
              <div className="role-skeleton" />
              <div className="role-skeleton" />
            </div>
          )}
          {isError && (
            <div className="empty-state">
              <p>Erreur reseau RBAC.</p>
              <button type="button" className="btn-secondary" onClick={() => window.location.reload()}>
                Reessayer
              </button>
            </div>
          )}
          {!isLoading && !isError && groupedRoles.length === 0 && (
            <div className="empty-state">
              <p>Aucun role disponible pour cette filiere.</p>
            </div>
          )}
          {!isLoading &&
            !isError &&
            groupedRoles.map(([groupName, roles]) => {
              const isCollapsed = !!collapsed[groupName]
              return (
                <section key={groupName} className="role-group" aria-label={`Categorie ${groupName}`}>
                  <button
                    type="button"
                    className="role-group-header"
                    aria-expanded={!isCollapsed}
                    onClick={() => setCollapsed((p) => ({ ...p, [groupName]: !p[groupName] }))}
                  >
                    <span>{groupName}</span>
                    <span className="badge">{roles.length}</span>
                  </button>
                  {!isCollapsed && (
                    <div className="role-rows">
                      {roles.map((role) => (
                        <div
                          key={role.code}
                          data-testid={`role-row-${role.code}`}
                          className={`role-row ${draftRole === role.code ? 'selected' : ''}`}
                          role="button"
                          tabIndex={0}
                          onClick={() => {
                            setDraftRole(role.code)
                            handleValidate(role.code)
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              setDraftRole(role.code)
                              handleValidate(role.code)
                            }
                          }}
                        >
                          <div className="role-row-main">
                            <div className="role-row-title">{role.label}</div>
                            <div className="role-row-meta">{role.code}</div>
                            <div className="role-row-meta">{role.actorType}</div>
                            {role.description ? <div className="role-row-desc">{role.description}</div> : null}
                          </div>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <button
                              type="button"
                              data-testid={`role-choose-${role.code}`}
                              className="btn-secondary"
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleFavorite(role.code)
                              }}
                            >
                              {favoriteRoles.includes(role.code) ? 'Retirer des favoris' : 'Favori'}
                            </button>
                            <button
                              type="button"
                              className="btn-secondary"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleValidate(role.code)
                              }}
                            >
                              Choisir
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              )
            })}
        </div>

        <div className="session-actions">
          {draftRole && (
            <small style={{ marginRight: 'auto', color: '#54617a' }}>
              Permissions: {(rolePermissions || []).slice(0, 5).join(', ') || 'Aucune'}{(rolePermissions || []).length > 5 ? '...' : ''}
            </small>
          )}
          <button className="btn-primary" data-testid="role-validate" onClick={() => handleValidate()} disabled={!draftRole}>
            Valider
          </button>
        </div>
      </div>
    </div>
  )
}

