export const APP_ROLES = ['orpailleur', 'collecteur', 'commune', 'controleur', 'comptoir'] as const
export type AppRole = string

export const FILIERES = ['OR', 'PIERRE', 'BOIS'] as const
export type Filiere = (typeof FILIERES)[number]

export type Permission =
  | 'auth.login'
  | 'account.create'
  | 'account.view'
  | 'account.validate.commune'
  | 'account.validate.maire'
  | 'payment.initiate'
  | 'payment.validate'
  | 'territory.read'
  | 'territory.import'
  | 'territory.assign'
  | 'lot.create'
  | 'lot.verify'
  | 'trade.create'
  | 'trade.verify'
  | 'report.view'
  | 'audit.view'

export type RoleProfile = {
  label: string
  menuRole: string
  permissions: Permission[]
  supportedFilieres: Filiere[]
}

export const ROLE_PERMISSION_MAP: Record<string, RoleProfile> = {
  orpailleur: {
    label: 'Orpailleur',
    menuRole: 'orpailleur',
    permissions: ['auth.login', 'account.create', 'account.view', 'payment.initiate', 'territory.read', 'lot.create', 'trade.create'],
    supportedFilieres: ['OR', 'PIERRE', 'BOIS'],
  },
  collecteur: {
    label: 'Collecteur',
    menuRole: 'acteur',
    permissions: ['auth.login', 'account.create', 'account.view', 'payment.initiate', 'territory.read', 'lot.create', 'trade.create', 'report.view'],
    supportedFilieres: ['OR', 'PIERRE', 'BOIS'],
  },
  commune: {
    label: 'Commune',
    menuRole: 'commune_agent',
    permissions: ['auth.login', 'account.view', 'account.validate.commune', 'account.validate.maire', 'payment.validate', 'territory.read', 'territory.assign', 'report.view'],
    supportedFilieres: ['OR', 'PIERRE', 'BOIS'],
  },
  controleur: {
    label: 'Controleur',
    menuRole: 'police',
    permissions: ['auth.login', 'account.view', 'territory.read', 'lot.verify', 'trade.verify', 'audit.view', 'report.view'],
    supportedFilieres: ['OR', 'PIERRE', 'BOIS'],
  },
  comptoir: {
    label: 'Comptoir',
    menuRole: 'com',
    permissions: ['auth.login', 'account.create', 'account.view', 'payment.initiate', 'payment.validate', 'territory.read', 'trade.create', 'report.view'],
    supportedFilieres: ['OR', 'PIERRE', 'BOIS'],
  },
}

function roleCodeToLabel(role: string): string {
  return role
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function getRoleProfile(role: AppRole): RoleProfile {
  if (ROLE_PERMISSION_MAP[role]) return ROLE_PERMISSION_MAP[role]
  return {
    label: roleCodeToLabel(role),
    menuRole: role,
    permissions: ['auth.login'],
    supportedFilieres: ['OR', 'PIERRE', 'BOIS'],
  }
}

export type ValidationStep = {
  key: string
  label: string
  requiredPermission: Permission
}

export const VALIDATION_WORKFLOW: Record<Filiere, ValidationStep[]> = {
  OR: [
    { key: 'account_creation', label: 'Creation de compte acteur', requiredPermission: 'account.create' },
    { key: 'payment', label: 'Paiement des frais communaux', requiredPermission: 'payment.initiate' },
    { key: 'commune_validation', label: 'Validation par la commune / le maire', requiredPermission: 'account.validate.maire' },
  ],
  PIERRE: [
    { key: 'account_creation', label: 'Creation de compte acteur', requiredPermission: 'account.create' },
    { key: 'payment', label: 'Paiement des frais locaux', requiredPermission: 'payment.initiate' },
    { key: 'commune_validation', label: 'Validation communale', requiredPermission: 'account.validate.commune' },
  ],
  BOIS: [
    { key: 'account_creation', label: 'Creation de compte acteur', requiredPermission: 'account.create' },
    { key: 'payment', label: 'Paiement des redevances', requiredPermission: 'payment.initiate' },
    { key: 'commune_validation', label: 'Validation communale', requiredPermission: 'account.validate.commune' },
  ],
}

export function canRole(role: AppRole, permission: Permission): boolean {
  return getRoleProfile(role).permissions.includes(permission)
}

export function getRoleLabel(role: AppRole): string {
  return getRoleProfile(role).label
}
