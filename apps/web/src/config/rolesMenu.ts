/**
 * Configuration des menus et dashboards selon les rôles MADAVOLA.
 * Aligné sur le référentiel des autorités (stratégique, central, contrôle, territorial, communautaire, judiciaire).
 */

export type MenuItem = {
  path: string
  label: string
  icon: string
  /** Rôles autorisés à voir cet item (au moins un) */
  roles: string[]
}

export const MENU_ITEMS: MenuItem[] = [
  {
    path: '/dashboard',
    label: 'Tableau de bord',
    icon: '📊',
    roles: ['admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'decentralisation', 'region', 'commune_agent', 'acteur', 'orpailleur', 'com', 'bcmm', 'forets', 'tresor', 'dgd'],
  },
  {
    path: '/dashboard/national',
    label: 'Vue nationale',
    icon: '🇲🇬',
    roles: ['admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'decentralisation', 'tresor', 'dgd', 'com', 'bcmm', 'forets'],
  },
  {
    path: '/dashboard/regional',
    label: 'Vue régionale',
    icon: '🗺️',
    roles: ['admin', 'dirigeant', 'region', 'commune_agent', 'decentralisation'],
  },
  {
    path: '/dashboard/commune',
    label: 'Vue communale',
    icon: '🏘️',
    roles: ['admin', 'dirigeant', 'commune_agent'],
  },
  {
    path: '/ma-carte',
    label: 'Ma carte (QR)',
    icon: '📇',
    roles: ['acteur', 'orpailleur', 'admin', 'dirigeant', 'commune_agent'],
  },
  {
    path: '/actors',
    label: 'Acteurs',
    icon: '👥',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'mmrs', 'com', 'forets'],
  },
  {
    path: '/lots',
    label: 'Lots',
    icon: '📦',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'mmrs', 'com', 'forets'],
  },
  {
    path: '/transactions',
    label: 'Transactions',
    icon: '💳',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'mmrs', 'com', 'forets'],
  },
  {
    path: '/exports',
    label: 'Dossiers export',
    icon: '📤',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'mmrs', 'com', 'dgd'],
  },
  {
    path: '/invoices',
    label: 'Factures',
    icon: '🧾',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'mmrs', 'com', 'forets'],
  },
  {
    path: '/ledger',
    label: 'Grand livre',
    icon: '📒',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'mmrs', 'com', 'forets'],
  },
  {
    path: '/reports',
    label: 'Rapports',
    icon: '📈',
    roles: ['admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'region', 'commune_agent', 'decentralisation', 'tresor', 'dgd', 'com', 'bcmm', 'forets'],
  },
  {
    path: '/audit',
    label: 'Audit / Traces',
    icon: '📋',
    roles: ['admin', 'dirigeant', 'bianco'],
  },
  {
    path: '/inspections',
    label: 'Contrôles / Inspections',
    icon: '🔍',
    roles: ['admin', 'dirigeant', 'mmrs', 'dgd', 'police', 'gendarmerie', 'forets'],
  },
  {
    path: '/violations',
    label: 'Violations',
    icon: '⚠️',
    roles: ['admin', 'dirigeant', 'mmrs', 'dgd', 'police', 'gendarmerie', 'forets'],
  },
  {
    path: '/penalties',
    label: 'Pénalités',
    icon: '💰',
    roles: ['admin', 'dirigeant', 'mmrs', 'dgd', 'police', 'gendarmerie', 'forets'],
  },
  {
    path: '/verify',
    label: 'Vérification acteur (QR)',
    icon: '📱',
    roles: ['admin', 'dirigeant', 'dgd', 'police', 'gendarmerie', 'commune_agent'],
  },
]

/** Libellés des rôles */
export const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrateur',
  dirigeant: 'Dirigeant',
  pr: 'Présidence (PR)',
  pm: 'Primature (PM)',
  mmrs: 'MMRS (Mines)',
  mef: 'MEF (Finances)',
  bfm: 'BFM (Banque centrale)',
  decentralisation: 'Décentralisation',
  region: 'Région',
  commune_agent: 'Commune / Maire',
  acteur: 'Acteur',
  orpailleur: 'Orpailleur',
  bianco: 'BIANCO',
  police: 'Police',
  gendarmerie: 'Gendarmerie',
  dgd: 'Douanes (DGD)',
  tresor: 'Trésor',
  com: 'COM (Or)',
  bcmm: 'BCMM (Cadastre minier)',
  forets: 'Forêts / Environnement',
  fokontany: 'Fokontany',
  justice: 'Justice',
}

/** Rôles qui peuvent voir le dashboard national (indicateurs agrégés) */
export const ROLES_DASHBOARD_NATIONAL = [
  'admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'decentralisation', 'tresor', 'dgd', 'com', 'bcmm', 'forets',
]

/** Rôles qui peuvent voir le dashboard régional */
export const ROLES_DASHBOARD_REGIONAL = ['admin', 'dirigeant', 'region', 'commune_agent', 'decentralisation']

/** Rôles qui peuvent voir le dashboard communal */
export const ROLES_DASHBOARD_COMMUNE = ['admin', 'dirigeant', 'commune_agent']

export function canAccessMenu(userRoles: string[], item: MenuItem): boolean {
  if (!userRoles?.length) return false
  return item.roles.some((r) => userRoles.includes(r))
}

export function getVisibleMenuItems(userRoles: string[]): MenuItem[] {
  return MENU_ITEMS.filter((item) => canAccessMenu(userRoles, item))
}

export function canSeeDashboardNational(userRoles: string[]): boolean {
  return userRoles?.some((r) => ROLES_DASHBOARD_NATIONAL.includes(r)) ?? false
}

export function canSeeDashboardRegional(userRoles: string[]): boolean {
  return userRoles?.some((r) => ROLES_DASHBOARD_REGIONAL.includes(r)) ?? false
}

export function canSeeDashboardCommune(userRoles: string[]): boolean {
  return userRoles?.some((r) => ROLES_DASHBOARD_COMMUNE.includes(r)) ?? false
}
