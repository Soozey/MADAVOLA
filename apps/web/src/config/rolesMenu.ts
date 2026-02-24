export type MenuItem = {
  path: string
  label: string
  icon: string
  roles: string[]
}

export const MENU_ITEMS: MenuItem[] = [
  {
    path: '/dashboard',
    label: 'Tableau de bord',
    icon: 'DB',
    roles: [
      'admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'decentralisation',
      'region', 'commune_agent', 'acteur', 'orpailleur', 'com', 'bcmm', 'forets', 'tresor', 'dgd',
      'com_admin', 'com_agent', 'mines_region_agent', 'region_agent', 'district_agent',
    ],
  },
  {
    path: '/dashboard/national',
    label: 'Vue nationale',
    icon: 'NAT',
    roles: ['admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'decentralisation', 'tresor', 'dgd', 'com', 'bcmm', 'forets', 'com_admin'],
  },
  {
    path: '/dashboard/regional',
    label: 'Vue régionale',
    icon: 'REG',
    roles: ['admin', 'dirigeant', 'region', 'commune_agent', 'decentralisation', 'mines_region_agent', 'region_agent', 'district_agent'],
  },
  {
    path: '/dashboard/commune',
    label: 'Vue communale',
    icon: 'COM',
    roles: ['admin', 'dirigeant', 'commune_agent', 'commune'],
  },
  {
    path: '/ma-carte',
    label: 'Ma carte (QR)',
    icon: 'QR',
    roles: ['acteur', 'orpailleur', 'collecteur', 'bijoutier', 'admin', 'dirigeant', 'commune_agent'],
  },
  {
    path: '/actors',
    label: 'Acteurs',
    icon: 'ACT',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'collecteur', 'mmrs', 'com', 'com_admin', 'com_agent', 'forets'],
  },
  {
    path: '/lots',
    label: 'Lots',
    icon: 'LOT',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'collecteur', 'bijoutier', 'mmrs', 'com', 'com_admin', 'com_agent', 'forets', 'transporteur', 'pierre_exploitant', 'pierre_collecteur', 'pierre_lapidaire', 'pierre_exportateur', 'pierre_admin_central', 'bois_exploitant', 'bois_collecteur', 'bois_transformateur', 'bois_artisan', 'bois_exportateur', 'bois_admin_central'],
  },
  {
    path: '/transactions',
    label: 'Transactions',
    icon: 'TRX',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'collecteur', 'bijoutier', 'mmrs', 'com', 'com_admin', 'com_agent', 'forets', 'comptoir_operator', 'comptoir_compliance', 'comptoir_director', 'pierre_exploitant', 'pierre_collecteur', 'pierre_lapidaire', 'pierre_exportateur', 'pierre_admin_central', 'bois_exploitant', 'bois_collecteur', 'bois_transformateur', 'bois_artisan', 'bois_exportateur', 'bois_admin_central'],
  },
  {
    path: '/trades',
    label: 'Transactions avancées',
    icon: 'TRD',
    roles: ['admin', 'dirigeant', 'acteur', 'collecteur', 'orpailleur', 'pierre_exploitant', 'pierre_collecteur', 'pierre_lapidaire', 'pierre_exportateur', 'bois_exploitant', 'bois_collecteur', 'bois_transformateur', 'bois_artisan', 'bois_exportateur'],
  },
  {
    path: '/exports',
    label: 'Exportations',
    icon: 'EXP',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'mmrs', 'com', 'com_admin', 'com_agent', 'dgd', 'douanes_agent', 'gue_or_agent', 'pierre_exportateur', 'pierre_controleur_mines', 'pierre_douanes', 'pierre_admin_central', 'bois_exportateur', 'bois_douanes', 'bois_admin_central', 'forets'],
  },
  {
    path: '/transports',
    label: 'Transports',
    icon: 'TRP',
    roles: ['admin', 'dirigeant', 'transporteur', 'transporteur_agree', 'bois_transporteur', 'bois_controleur', 'bois_douanes', 'forets', 'bois_admin_central'],
  },
  {
    path: '/transformations',
    label: 'Transformations',
    icon: 'TRF',
    roles: ['admin', 'dirigeant', 'bois_transformateur', 'bois_artisan', 'bois_admin_central', 'forets'],
  },
  {
    path: '/invoices',
    label: 'Factures',
    icon: 'INV',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'mmrs', 'com', 'collecteur', 'forets'],
  },
  {
    path: '/ledger',
    label: 'Grand livre',
    icon: 'LED',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'collecteur', 'mmrs', 'com', 'com_admin', 'forets'],
  },
  {
    path: '/reports',
    label: 'Rapports',
    icon: 'RPT',
    roles: [
      'admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'region', 'commune_agent',
      'decentralisation', 'tresor', 'dgd', 'com', 'com_admin', 'com_agent', 'bcmm', 'forets',
      'mines_region_agent', 'region_agent', 'district_agent',
    ],
  },
  {
    path: '/audit',
    label: 'Audit et traces',
    icon: 'AUD',
    roles: ['admin', 'dirigeant', 'bianco', 'com_admin'],
  },
  {
    path: '/inspections',
    label: 'Contrôles / Inspections',
    icon: 'CTL',
    roles: ['admin', 'dirigeant', 'mmrs', 'dgd', 'douanes_agent', 'police', 'gendarmerie', 'forets', 'com_agent', 'pierre_controleur_mines', 'pierre_douanes'],
  },
  {
    path: '/violations',
    label: 'Violations',
    icon: 'VIO',
    roles: ['admin', 'dirigeant', 'mmrs', 'dgd', 'douanes_agent', 'police', 'gendarmerie', 'forets', 'com_agent', 'pierre_controleur_mines', 'pierre_douanes'],
  },
  {
    path: '/penalties',
    label: 'Pénalités',
    icon: 'PEN',
    roles: ['admin', 'dirigeant', 'mmrs', 'dgd', 'douanes_agent', 'police', 'gendarmerie', 'forets', 'com_admin'],
  },
  {
    path: '/verify',
    label: 'Vérification acteur (QR)',
    icon: 'VRF',
    roles: ['admin', 'dirigeant', 'dgd', 'douanes_agent', 'police', 'gendarmerie', 'commune_agent', 'transporteur'],
  },
  {
    path: '/notifications',
    label: 'Notifications',
    icon: 'NTF',
    roles: ['admin', 'dirigeant', 'acteur', 'orpailleur', 'collecteur', 'pierre_exploitant', 'pierre_collecteur', 'pierre_exportateur', 'bois_exploitant', 'bois_collecteur', 'bois_exportateur', 'bois_admin_central'],
  },
  {
    path: '/map',
    label: 'Cartographie',
    icon: 'MAP',
    roles: ['admin', 'dirigeant', 'commune_agent', 'acteur', 'orpailleur', 'collecteur', 'transporteur', 'police', 'gendarmerie', 'forets', 'com_agent', 'com_admin', 'pierre_admin_central', 'bois_admin_central'],
  },
  {
    path: '/admin-config',
    label: 'Configuration admin',
    icon: 'CFG',
    roles: ['admin'],
  },
  {
    path: '/documents',
    label: 'Documents',
    icon: 'DOC',
    roles: ['admin', 'dirigeant', 'acteur', 'orpailleur', 'collecteur', 'commune_agent', 'com', 'com_admin', 'com_agent', 'pierre_admin_central', 'bois_admin_central', 'bois_exportateur', 'pierre_exportateur'],
  },
  {
    path: '/ops-coverage',
    label: 'Couverture API/UI',
    icon: 'OPS',
    roles: ['admin', 'dirigeant', 'com_admin'],
  },
  {
    path: '/or-compliance',
    label: 'Conformité OR',
    icon: 'OR',
    roles: [
      'admin', 'dirigeant', 'com', 'com_admin', 'com_agent', 'commune', 'commune_agent',
      'collecteur', 'orpailleur', 'bijoutier', 'douanes_agent', 'gue_or_agent',
      'mines_region_agent', 'lab_bgglm', 'raffinerie_agent',
    ],
  },
]

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
  commune: 'Commune',
  commune_agent: 'Commune / Maire',
  acteur: 'Acteur',
  orpailleur: 'Orpailleur',
  collecteur: 'Collecteur',
  bianco: 'BIANCO',
  police: 'Police',
  gendarmerie: 'Gendarmerie',
  dgd: 'Douanes (DGD)',
  douanes_agent: 'Douanes Agent',
  gue_or_agent: 'GUE OR Agent',
  tresor: 'Trésor',
  com: 'COM (Or)',
  com_admin: 'COM Admin',
  com_agent: 'COM Agent',
  bcmm: 'BCMM',
  forets: 'Forêts / Environnement',
  mines_region_agent: 'Mines Région Agent',
  lab_bgglm: 'BGGLM',
  raffinerie_agent: 'Raffinerie Agent',
  transporteur: 'Transporteur',
  region_agent: 'Région Agent',
  district_agent: 'District Agent',
  fokontany: 'Fokontany',
  justice: 'Justice',
  bijoutier: 'Bijoutier',
  pierre_exploitant: 'Pierre Exploitant',
  pierre_collecteur: 'Pierre Collecteur',
  pierre_lapidaire: 'Pierre Lapidaire',
  pierre_exportateur: 'Pierre Exportateur',
  pierre_controleur_mines: 'Pierre Contrôleur Mines',
  pierre_douanes: 'Pierre Douanes',
  pierre_commune_agent: 'Pierre Commune Agent',
  pierre_admin_central: 'Pierre Admin Central',
  bois_exploitant: 'Bois Exploitant',
  bois_collecteur: 'Bois Collecteur',
  bois_transporteur: 'Bois Transporteur',
  bois_transformateur: 'Bois Transformateur',
  bois_artisan: 'Bois Artisan',
  bois_exportateur: 'Bois Exportateur',
  bois_forest_admin: 'Bois Administration Forestière',
  bois_douanes: 'Bois Douanes',
  bois_commune_agent: 'Bois Commune Agent',
  bois_controleur: 'Bois Contrôleur',
  bois_admin_central: 'Bois Admin Central',
}

export const ROLES_DASHBOARD_NATIONAL = [
  'admin', 'dirigeant', 'pr', 'pm', 'mmrs', 'mef', 'bfm', 'decentralisation',
  'tresor', 'dgd', 'com', 'com_admin', 'bcmm', 'forets',
]

export const ROLES_DASHBOARD_REGIONAL = ['admin', 'dirigeant', 'region', 'commune_agent', 'decentralisation', 'mines_region_agent', 'region_agent', 'district_agent']
export const ROLES_DASHBOARD_COMMUNE = ['admin', 'dirigeant', 'commune_agent', 'commune']

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
