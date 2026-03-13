import { Filiere, getRoleProfile } from '../config/rbac'

type UserRole = { role: string; status?: string | null }

const ROLE_PRIORITY = [
  'admin',
  'dirigeant',
  'com_admin',
  'com_agent',
  'com',
  'commune_agent',
  'commune',
  'pierre_admin_central',
  'bois_admin_central',
]

function normalizeRole(code: string | null | undefined): string {
  return (code || '').trim().toLowerCase()
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values))
}

export function extractActiveRoles(userRoles: UserRole[] | null | undefined): string[] {
  const rows = Array.isArray(userRoles) ? userRoles : []
  const active = rows
    .filter((row) => (row.status || 'active').toLowerCase() === 'active')
    .map((row) => normalizeRole(row.role))
    .filter(Boolean)
  if (active.length > 0) return unique(active)
  return unique(rows.map((row) => normalizeRole(row.role)).filter(Boolean))
}

export function pickPrimaryRole(userRoles: UserRole[] | null | undefined, currentRole?: string | null): string | null {
  const roles = extractActiveRoles(userRoles)
  if (roles.length === 0) return null
  const current = normalizeRole(currentRole)
  if (current && roles.includes(current)) return current
  for (const role of ROLE_PRIORITY) {
    if (roles.includes(role)) return role
  }
  return roles[0]
}

export function inferFiliereFromRole(role: string | null | undefined): Filiere {
  const normalized = normalizeRole(role)
  if (normalized.startsWith('pierre_')) return 'PIERRE'
  if (normalized.startsWith('bois_')) return 'BOIS'
  return 'OR'
}

export function resolveFiliereForRole(role: string | null | undefined, candidate?: string | null): Filiere {
  const normalizedCandidate = (candidate || '').trim().toUpperCase() as Filiere | ''
  const fallback = inferFiliereFromRole(role)
  if (!role) return normalizedCandidate || fallback
  const supported = getRoleProfile(role).supportedFilieres
  if (normalizedCandidate && supported.includes(normalizedCandidate)) return normalizedCandidate
  if (supported.includes(fallback)) return fallback
  return supported[0] || fallback
}
