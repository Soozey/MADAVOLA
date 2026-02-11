/**
 * Données de territoires en dur (UTF-8) pour éviter les problèmes d'accents
 * et permettre le formulaire d'inscription sans dépendre uniquement de l'API.
 * Codes alignés sur le territoire par défaut créé par create_admin.py (DEFAULT).
 *
 * Vous pouvez remplacer / étendre ces listes avec vos régions, districts,
 * communes et fokontany réels (en conservant les codes attendus par l'API).
 */

export interface TerritoryRegion {
  code: string
  name: string
}

export interface TerritoryDistrict {
  code: string
  name: string
  region_code: string
}

export interface TerritoryCommune {
  code: string
  name: string
  district_code: string
}

export interface TerritoryFokontany {
  code: string
  name: string
  commune_code: string
}

/** Régions (libellés en dur, accents corrects) */
export const HARDCODED_REGIONS: TerritoryRegion[] = [
  { code: 'DEFAULT', name: 'Région par défaut' },
]

/** Districts par région (code région = region_code) */
export const HARDCODED_DISTRICTS: TerritoryDistrict[] = [
  { code: 'DEFAULT', name: 'District par défaut', region_code: 'DEFAULT' },
]

/** Communes par district */
export const HARDCODED_COMMUNES: TerritoryCommune[] = [
  { code: 'DEFAULT', name: 'Commune par défaut', district_code: 'DEFAULT' },
]

/** Fokontany par commune (optionnel) */
export const HARDCODED_FOKONTANY: TerritoryFokontany[] = [
  { code: 'DEFAULT', name: 'Fokontany par défaut', commune_code: 'DEFAULT' },
]

export function getHardcodedDistricts(regionCode: string): TerritoryDistrict[] {
  return HARDCODED_DISTRICTS.filter((d) => d.region_code === regionCode)
}

export function getHardcodedCommunes(districtCode: string): TerritoryCommune[] {
  return HARDCODED_COMMUNES.filter((c) => c.district_code === districtCode)
}

export function getHardcodedFokontany(communeCode: string): TerritoryFokontany[] {
  return HARDCODED_FOKONTANY.filter((f) => f.commune_code === communeCode)
}
