import { useMemo } from 'react'
import type { FiliereCode, RbacRole } from './types'

interface MobileRoleSelectorProps {
  filiere: FiliereCode
  onFiliereChange: (next: FiliereCode) => void
  showFiliereSelect?: boolean
  selectedRole: string
  onRoleSelect: (roleCode: string) => void
  roles: RbacRole[]
  search: string
  onSearchChange: (value: string) => void
  category: string
  onCategoryChange: (value: string) => void
  actorType: string
  onActorTypeChange: (value: string) => void
}

export function MobileRoleSelector({
  filiere,
  onFiliereChange,
  showFiliereSelect = true,
  selectedRole,
  onRoleSelect,
  roles,
  search,
  onSearchChange,
  category,
  onCategoryChange,
  actorType,
  onActorTypeChange,
}: MobileRoleSelectorProps) {
  const categories = useMemo(() => {
    const list = Array.from(new Set((roles || []).map((r) => r.category || 'Autres'))).sort()
    return ['all', ...list]
  }, [roles])

  const groupedRoles = useMemo(() => {
    const filtered = (roles || []).filter((r) => {
      const okCategory = category === 'all' || (r.category || 'Autres') === category
      const okActorType = actorType === 'all' || (r.actor_type || 'TRANSVERSAL') === actorType
      const q = search.trim().toLowerCase()
      if (!q) return okCategory && okActorType
      const hay = `${r.code || ''} ${r.label || ''} ${r.description || ''} ${r.category || ''}`.toLowerCase()
      return okCategory && okActorType && hay.includes(q)
    })
    const groups: Record<string, RbacRole[]> = {}
    for (const row of filtered) {
      const key = row.category || 'Autres'
      if (!groups[key]) groups[key] = []
      groups[key].push(row)
    }
    return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))
  }, [roles, category, actorType, search])

  return (
    <>
      {showFiliereSelect && (
        <select value={filiere} onChange={(e) => onFiliereChange(e.target.value as FiliereCode)}>
          <option value="OR">OR</option>
          <option value="PIERRE">PIERRE</option>
          <option value="BOIS">BOIS</option>
        </select>
      )}
      <input placeholder="Rechercher un rôle..." value={search} onChange={(e) => onSearchChange(e.target.value)} />
      <select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c === 'all' ? 'Toutes catégories' : c}
          </option>
        ))}
      </select>
      <select value={actorType} onChange={(e) => onActorTypeChange(e.target.value)}>
        <option value="all">Tous profils</option>
        <option value="USAGER">Usager</option>
        <option value="AGENT_ETAT">Agent État</option>
        <option value="OPERATEUR_PRIVE">Opérateur privé</option>
        <option value="TRANSVERSAL">Transversal</option>
      </select>
      <div style={{ maxHeight: 260, overflowY: 'auto', width: '100%', border: '1px solid #c8d6ea', borderRadius: 10, padding: 10 }}>
        {groupedRoles.length === 0 ? (
          <small>Aucun rôle pour ce filtre.</small>
        ) : (
          groupedRoles.map(([group, groupRoles]) => (
            <div key={group} style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 700, fontSize: 12, color: '#173663', marginBottom: 6 }}>
                {group} ({groupRoles.length})
              </div>
              {groupRoles.map((role) => (
                <button
                  key={role.code}
                  type="button"
                  className={selectedRole === role.code ? '' : 'secondary'}
                  style={{ width: '100%', textAlign: 'left', marginTop: 6, minHeight: 48, padding: '10px 12px' }}
                  onClick={() => onRoleSelect(role.code)}
                >
                  {role.label || role.code} <small>({role.code})</small>
                </button>
              ))}
            </div>
          ))
        )}
      </div>
    </>
  )
}
