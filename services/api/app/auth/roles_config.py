"""
Référentiel des rôles MADAVOLA : 19 autorités/institutions avec niveaux et habilitations.
Aligné sur le tableau des rôles et attributions (présentation).
"""

from typing import TypedDict


class RoleDefinition(TypedDict):
    level: str
    institution: str
    acronym: str
    permissions: list[str]
    description: str


# Niveaux d'autorité
LEVELS = (
    "strategique",
    "central",
    "regulation",
    "controle",
    "territorial",
    "communautaire",
    "judiciaire",
)

# Permissions (habilitations) utilisées dans les endpoints
PERM_READ_ONLY = "lecture_seule"
PERM_DASHBOARD_NATIONAL = "dashboard_national"
PERM_ALERTES_STRATEGIQUES = "alertes_strategiques"
PERM_PILOTAGE_KPI = "pilotage_kpi"
PERM_ADMIN_FILIERE_MINES = "admin_filiere_mines"
PERM_ADMIN_FILIERE_OR = "admin_filiere_or"
PERM_ADMIN_FILIERE_BOIS = "admin_filiere_bois"
PERM_FOURNISSEUR_DONNEES = "fournisseur_donnees"
PERM_PARAMETRAGE_FISCAL = "parametrage_fiscal"
PERM_SUPERVISION_RECETTES = "supervision_recettes"
PERM_RAPPROCHEMENT = "rapprochement"
PERM_CONTROLE_EXPORT = "controle_export"
PERM_RAPATRIEMENT_DEVISES = "rapatriement_devises"
PERM_PROFIL_CONTROLEUR = "profil_controleur"
PERM_AUDIT_LOGS = "audit_logs"
PERM_SUPERVISION_TERRITORIALE = "supervision_territoriale"
PERM_DASHBOARD_REGIONAL = "dashboard_regional"
PERM_ADMIN_COMMUNE = "admin_commune"
PERM_APPUI_FOKONTANY = "appui_fokontany"
PERM_JUSTICE_REQUISITION = "justice_requisition"

# Référentiel complet des 19 rôles (code = clé, utilisé dans actor_roles.role)
ROLE_DEFINITIONS: dict[str, RoleDefinition] = {
    "pr": {
        "level": "strategique",
        "institution": "Présidence de la République",
        "acronym": "PR",
        "permissions": [PERM_READ_ONLY, PERM_DASHBOARD_NATIONAL, PERM_ALERTES_STRATEGIQUES],
        "description": "Orientation stratégique, arbitrages, suivi macro (indicateurs nationaux).",
    },
    "pm": {
        "level": "strategique",
        "institution": "Primature (Coordination gouvernementale)",
        "acronym": "PM",
        "permissions": [PERM_READ_ONLY, PERM_PILOTAGE_KPI, PERM_DASHBOARD_NATIONAL],
        "description": "Pilotage intersectoriel, coordination des ministères, suivi du déploiement.",
    },
    "mmrs": {
        "level": "central",
        "institution": "Ministère des Mines et des Ressources Stratégiques",
        "acronym": "MMRS",
        "permissions": [PERM_ADMIN_FILIERE_MINES, PERM_DASHBOARD_NATIONAL],
        "description": "Tutelle technique (mines) : réglementation, procédures, supervision or/petite mine/pierres.",
    },
    "com": {
        "level": "central",
        "institution": "Centrale de l'Or de Madagascar",
        "acronym": "COM",
        "permissions": [PERM_ADMIN_FILIERE_OR, PERM_CONTROLE_EXPORT],
        "description": "Chaîne légale de l'or : enregistrement collecteurs, agrément comptoirs, validations avant export.",
    },
    "bcmm": {
        "level": "central",
        "institution": "Bureau du Cadastre Minier de Madagascar",
        "acronym": "BCMM",
        "permissions": [PERM_FOURNISSEUR_DONNEES, PERM_READ_ONLY],
        "description": "Cadastre/titres miniers : référentiel des permis et zones.",
    },
    "forets": {
        "level": "central",
        "institution": "Ministère chargé de l'Environnement et des Forêts",
        "acronym": "",
        "permissions": [PERM_ADMIN_FILIERE_BOIS, PERM_CONTROLE_EXPORT],
        "description": "Tutelle technique filière bois : autorisations, contrôle, conformité, CITES si applicable.",
    },
    "mef": {
        "level": "central",
        "institution": "Ministère de l'Économie et des Finances",
        "acronym": "MEF",
        "permissions": [PERM_PARAMETRAGE_FISCAL, PERM_SUPERVISION_RECETTES, PERM_DASHBOARD_NATIONAL],
        "description": "Tutelle financière : règles fiscales, redevances/ristournes, suivi des recettes.",
    },
    "tresor": {
        "level": "central",
        "institution": "Trésor Public",
        "acronym": "",
        "permissions": [PERM_READ_ONLY, PERM_RAPPROCHEMENT],
        "description": "Réception des recettes État; comptabilisation; suivi des reversements.",
    },
    "dgd": {
        "level": "central",
        "institution": "Direction Générale des Douanes",
        "acronym": "DGD",
        "permissions": [PERM_CONTROLE_EXPORT, PERM_PROFIL_CONTROLEUR],
        "description": "Contrôle export/import; validation douanière; lutte contre fraude/contrebande.",
    },
    "bfm": {
        "level": "central",
        "institution": "Banque Centrale de Madagascar (Banky Foiben'i Madagasikara)",
        "acronym": "BFM",
        "permissions": [PERM_READ_ONLY, PERM_RAPATRIEMENT_DEVISES],
        "description": "Suivi rapatriement des devises; conformité changes; réserves.",
    },
    "artec": {
        "level": "regulation",
        "institution": "Autorité de Régulation des Technologies de Communication",
        "acronym": "ARTEC",
        "permissions": [],  # Hors SI métier; référencé pour USSD
        "description": "Cadre passerelles USSD / codes courts (si USSD).",
    },
    "police": {
        "level": "controle",
        "institution": "Police Nationale / Sécurité Publique",
        "acronym": "",
        "permissions": [PERM_PROFIL_CONTROLEUR],
        "description": "Contrôles terrain; sécurisation transports; constat d'infractions selon habilitations.",
    },
    "gendarmerie": {
        "level": "controle",
        "institution": "Gendarmerie Nationale",
        "acronym": "",
        "permissions": [PERM_PROFIL_CONTROLEUR],
        "description": "Contrôles terrain et axes; lutte contre trafic; appui judiciaire.",
    },
    "bianco": {
        "level": "controle",
        "institution": "BIANCO (Anti-corruption)",
        "acronym": "BIANCO",
        "permissions": [PERM_AUDIT_LOGS],
        "description": "Lutte anticorruption; exploitation des traces/audits en cas d'enquête.",
    },
    "decentralisation": {
        "level": "central",
        "institution": "Ministère de la Décentralisation / Collectivités",
        "acronym": "",
        "permissions": [PERM_SUPERVISION_TERRITORIALE, PERM_READ_ONLY],
        "description": "Coordination avec régions/communes (recensement, ristournes, pilotage territorial).",
    },
    "region": {
        "level": "territorial",
        "institution": "Région (Gouverneur / Chef de Région)",
        "acronym": "",
        "permissions": [PERM_DASHBOARD_REGIONAL, PERM_READ_ONLY],
        "description": "Pilotage régional; coordination communes; suivi des ristournes régionales.",
    },
    "commune_agent": {
        "level": "territorial",
        "institution": "Commune (Maire / Administration communale)",
        "acronym": "",
        "permissions": [PERM_ADMIN_COMMUNE],
        "description": "Recensement de proximité; validation initiale; gestion comptes Mobile Money communaux; suivi recettes.",
    },
    "fokontany": {
        "level": "communautaire",
        "institution": "Fokontany (Chef Fokontany)",
        "acronym": "",
        "permissions": [PERM_APPUI_FOKONTANY],
        "description": "Attestation/identification locale; appui recensement; médiation terrain.",
    },
    "justice": {
        "level": "judiciaire",
        "institution": "Justice / Parquet (optionnel)",
        "acronym": "",
        "permissions": [PERM_JUSTICE_REQUISITION],
        "description": "Suites judiciaires aux infractions; réquisitions.",
    },
    # Rôles techniques existants (rétrocompatibilité)
    "admin": {
        "level": "central",
        "institution": "Administrateur plateforme",
        "acronym": "",
        "permissions": [
            PERM_READ_ONLY,
            PERM_DASHBOARD_NATIONAL,
            PERM_PILOTAGE_KPI,
            PERM_ADMIN_FILIERE_MINES,
            PERM_ADMIN_FILIERE_OR,
            PERM_ADMIN_FILIERE_BOIS,
            PERM_SUPERVISION_RECETTES,
            PERM_AUDIT_LOGS,
            PERM_SUPERVISION_TERRITORIALE,
            PERM_DASHBOARD_REGIONAL,
            PERM_ADMIN_COMMUNE,
        ],
        "description": "Accès complet à la plateforme (configuration, rôles, territoires, etc.).",
    },
    "dirigeant": {
        "level": "central",
        "institution": "Dirigeant / Pilote",
        "acronym": "",
        "permissions": [
            PERM_DASHBOARD_NATIONAL,
            PERM_DASHBOARD_REGIONAL,
            PERM_SUPERVISION_RECETTES,
            PERM_AUDIT_LOGS,
        ],
        "description": "Pilotage et reporting (rapports, exports, ledger).",
    },
    "controleur": {
        "level": "controle",
        "institution": "Contrôleur terrain",
        "acronym": "",
        "permissions": [PERM_PROFIL_CONTROLEUR],
        "description": "Scan QR, vérification lot/acteur, saisie observations/PV (inspections, violations, pénalités).",
    },
    "acteur": {
        "level": "communautaire",
        "institution": "Acteur de la filière",
        "acronym": "",
        "permissions": [],
        "description": "Opérateur terrain (déclarations, transactions).",
    },
    "orpailleur": {
        "level": "communautaire",
        "institution": "Orpailleur / Collecteur",
        "acronym": "",
        "permissions": [],
        "description": "Acteur filière or.",
    },
    "collecteur": {
        "level": "communautaire",
        "institution": "Collecteur",
        "acronym": "",
        "permissions": [],
        "description": "Acheteur intermediaire, consolidation lots et vente au comptoir.",
    },
    "comptoir_operator": {
        "level": "central",
        "institution": "Comptoir",
        "acronym": "",
        "permissions": [PERM_CONTROLE_EXPORT],
        "description": "Operateur comptoir: reception lots, preparation dossier export.",
    },
    "comptoir_compliance": {
        "level": "central",
        "institution": "Comptoir",
        "acronym": "",
        "permissions": [PERM_CONTROLE_EXPORT, PERM_AUDIT_LOGS],
        "description": "Responsable conformite comptoir: controles documentaires et tracabilite.",
    },
    "comptoir_director": {
        "level": "central",
        "institution": "Comptoir",
        "acronym": "",
        "permissions": [PERM_CONTROLE_EXPORT, PERM_DASHBOARD_NATIONAL, PERM_AUDIT_LOGS],
        "description": "Directeur comptoir: validation finale et supervision.",
    },

}


def get_roles_for_level(level: str) -> list[str]:
    """Retourne les codes de rôles pour un niveau donné."""
    return [code for code, defn in ROLE_DEFINITIONS.items() if defn["level"] == level]


def get_permissions_for_role(role_code: str) -> list[str]:
    """Retourne la liste des permissions pour un rôle."""
    defn = ROLE_DEFINITIONS.get(role_code)
    if not defn:
        return []
    return list(defn.get("permissions", []))


def has_permission(role_codes: list[str], permission: str) -> bool:
    """Vérifie si au moins un des rôles de l'acteur possède la permission."""
    for code in role_codes:
        if permission in get_permissions_for_role(code):
            return True
    return False


def roles_with_permission(permission: str) -> set[str]:
    """Retourne l'ensemble des codes de rôles ayant une permission donnée."""
    return {
        code for code, defn in ROLE_DEFINITIONS.items()
        if permission in defn.get("permissions", [])
    }


def get_referential_for_front() -> list[dict]:
    """Liste pour le frontend : tous les rôles avec level, institution, acronym, description."""
    return [
        {
            "code": code,
            "level": defn["level"],
            "institution": defn["institution"],
            "acronym": defn["acronym"] or None,
            "description": defn["description"],
        }
        for code, defn in ROLE_DEFINITIONS.items()
    ]
