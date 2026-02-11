/** Traduction des codes d'erreur API en messages utilisateur (démo / UX). */
export type ApiDetail = string | Array<{ msg?: string }> | { message?: string }

const LABELS: Record<string, string> = {
  token_manquant: 'Session expirée. Reconnectez-vous.',
  token_invalide: 'Session invalide. Reconnectez-vous.',
  compte_inactif: 'Compte désactivé.',
  identifiants_invalides: 'Identifiant ou mot de passe incorrect.',
  auth_desactivee: 'Compte désactivé. Contactez l\'administration.',
  role_insuffisant: 'Droits insuffisants pour cette action.',
  permission_insuffisante: 'Habilitations insuffisantes.',
  acces_refuse: 'Accès refusé.',
  acces_refuse_region: 'Vous ne pouvez consulter que votre région.',
  acces_refuse_commune: 'Vous ne pouvez consulter que votre commune.',
  territoire_non_charge: 'Aucun territoire chargé. Importez un fichier territoire (admin).',
  territoire_invalide: 'Région, district ou commune invalide.',
  gps_obligatoire: 'Point GPS (lieu de déclaration) obligatoire.',
  gps_introuvable: 'Point GPS introuvable.',
  telephone_deja_utilise: 'Ce numéro est déjà utilisé.',
  email_deja_utilise: 'Cet email est déjà utilisé.',
  telephone_invalide: 'Téléphone invalide. Format : 03XXXXXXXX.',
  roles_obligatoires: 'Au moins un rôle requis.',
  role_deja_attribue: 'Ce rôle est déjà attribué.',
  acteur_invalide: 'Acteur invalide.',
  acteur_introuvable: 'Acteur introuvable.',
  items_obligatoires: 'Ajoutez au moins une ligne (lot, quantité, prix).',
  intervalle_invalide: 'La date de fin doit être après la date de début.',
  region_introuvable: 'Région introuvable.',
  commune_introuvable: 'Commune introuvable.',
}

export function getApiErrorMessage(detail: ApiDetail | null | undefined, fallback = 'Une erreur est survenue.'): string {
  if (detail == null) return fallback
  if (typeof detail === 'string') return LABELS[detail] ?? detail
  if (Array.isArray(detail)) {
    const msgs = (detail as { msg?: string }[]).map((d) => d?.msg).filter(Boolean)
    return msgs.length ? msgs.join('. ') : fallback
  }
  if (typeof detail === 'object' && detail !== null && 'message' in detail)
    return LABELS[(detail as { message: string }).message] ?? (detail as { message: string }).message ?? fallback
  return fallback
}

export function getApiDetailFromError(err: unknown): ApiDetail | null {
  if (err && typeof err === 'object' && 'response' in err)
    return (err as { response?: { data?: { detail?: ApiDetail } } }).response?.data?.detail ?? null
  return null
}

export function getErrorMessage(err: unknown, fallback: string): string {
  const ax = err && typeof err === 'object' && 'response' in err
    ? (err as { response?: { status?: number; data?: { detail?: unknown } } }).response
    : undefined
  const status = ax?.status
  const detail = getApiDetailFromError(err)

  if (status === 404) {
    return "Service API introuvable (404). Démarrez l'API MADAVOLA sur le port 8000 (ex: docker compose -f infra/docker/compose.yml up -d depuis la racine du projet)."
  }
  if (detail != null) return getApiErrorMessage(detail, fallback)
  if (err && typeof err === 'object' && !('response' in err)) {
    return "Impossible de joindre l'API (port 8000). Démarrez l'API : avec Docker « docker compose -f infra/docker/compose.yml up -d », ou sans Docker « .\\scripts\\run-local.ps1 » (après avoir lancé la base : docker compose -f infra/docker/compose.dev-db-only.yml up -d)."
  }
  return fallback
}
