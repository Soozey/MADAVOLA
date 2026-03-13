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
PERM_REGISTRE_BIJOUTIER = "registre_bijoutier"
PERM_ODV_DTSPM = "odv_dtspm"
PERM_GUE_EXPORT = "gue_export"
PERM_ANALYSE_CERTIFICATION = "analyse_certification"
PERM_COM_PARAMETRAGE_NATIONAL = "com_parametrage_national"
PERM_COM_INSTRUCTION_DOSSIERS = "com_instruction_dossiers"
PERM_COM_VALIDATION_COLLECTEUR = "com_validation_collecteur"
PERM_COM_SUIVI_AFFILIATIONS = "com_suivi_affiliations"
PERM_COM_SANCTIONS_METIER = "com_sanctions_metier"
PERM_MINES_TERRITORIAL_CONTROL = "mines_territorial_control"
PERM_BGGLM_LAB_ENTRY = "bgglm_lab_entry"
PERM_TRANSPORT_OR = "transport_or"
PERM_EXPORT_OR_WORKFLOW = "export_or_workflow"
PERM_POINCONNAGE_RAFFINERIE = "poinconnage_raffinerie"
PERM_CARD_KARA_MANAGE = "card_kara_manage"
PERM_CARD_COLLECTOR_MANAGE = "card_collector_manage"
PERM_CARD_VALIDATE_COMMUNE = "card_validate_commune"
PERM_CARD_VALIDATE_COM = "card_validate_com"
PERM_PIERRE_DECLARE_LOT = "pierre_declare_lot"
PERM_PIERRE_TRADE = "pierre_trade"
PERM_PIERRE_TRANSFORM = "pierre_transform"
PERM_PIERRE_EXPORT = "pierre_export"
PERM_PIERRE_CONTROL = "pierre_control"
PERM_PIERRE_CATALOG_ADMIN = "pierre_catalog_admin"
PERM_BOIS_DECLARE_LOT = "bois_declare_lot"
PERM_BOIS_TRADE = "bois_trade"
PERM_BOIS_TRANSPORT = "bois_transport"
PERM_BOIS_TRANSFORM = "bois_transform"
PERM_BOIS_EXPORT = "bois_export"
PERM_BOIS_CONTROL = "bois_control"
PERM_BOIS_CATALOG_ADMIN = "bois_catalog_admin"

# Référentiel complet des rôles (code = clé, utilisé dans actor_roles.role)
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
        "permissions": [
            PERM_ADMIN_FILIERE_OR,
            PERM_CONTROLE_EXPORT,
            PERM_ODV_DTSPM,
            PERM_COM_PARAMETRAGE_NATIONAL,
            PERM_COM_INSTRUCTION_DOSSIERS,
            PERM_CARD_VALIDATE_COM,
        ],
        "description": "Chaîne légale de l'or : enregistrement collecteurs, agrément comptoirs, validations avant export.",
    },
    "gue": {
        "level": "central",
        "institution": "Guichet Unique d'Exportation",
        "acronym": "GUE",
        "permissions": [PERM_GUE_EXPORT, PERM_CONTROLE_EXPORT],
        "description": "Guichet de controle export: verification documentaire, recouvrement et delivrance de conformite.",
    },
    "analyse_certification": {
        "level": "central",
        "institution": "Entite d'analyse et certification",
        "acronym": "",
        "permissions": [PERM_ANALYSE_CERTIFICATION, PERM_CONTROLE_EXPORT],
        "description": "Titrage, poinconnage officiel et certification qualite/quantite des lots.",
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
        "permissions": [
            PERM_ADMIN_COMMUNE,
            PERM_CARD_VALIDATE_COMMUNE,
            PERM_CARD_KARA_MANAGE,
            PERM_CARD_COLLECTOR_MANAGE,
        ],
        "description": "Recensement de proximité; validation initiale; gestion comptes Mobile Money communaux; suivi recettes.",
    },
    "commune": {
        "level": "territorial",
        "institution": "Commune (Maire / Administration communale)",
        "acronym": "",
        "permissions": [
            PERM_ADMIN_COMMUNE,
            PERM_CARD_VALIDATE_COMMUNE,
            PERM_CARD_KARA_MANAGE,
            PERM_CARD_COLLECTOR_MANAGE,
        ],
        "description": "Role legacy commune, conserve pour retro-compatibilite RBAC/API/UI.",
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
        "permissions": [PERM_CARD_COLLECTOR_MANAGE],
        "description": "Acheteur intermediaire, consolidation lots et vente au comptoir.",
    },
    "bijoutier": {
        "level": "central",
        "institution": "Bijouterie",
        "acronym": "",
        "permissions": [PERM_REGISTRE_BIJOUTIER, PERM_CARD_COLLECTOR_MANAGE],
        "description": "Operateur bijoutier: registre entrees/sorties, gestion laissez-passer et ventes locales.",
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
    "raffinerie_operator": {
        "level": "central",
        "institution": "Raffinerie",
        "acronym": "",
        "permissions": [PERM_POINCONNAGE_RAFFINERIE],
        "description": "Operateur raffinerie: transformation or brut vers produits raffines.",
    },
    "raffinerie_supervisor": {
        "level": "central",
        "institution": "Raffinerie",
        "acronym": "",
        "permissions": [PERM_AUDIT_LOGS],
        "description": "Supervision des operations et des rendements de transformation.",
    },
    "raffinerie_conformite": {
        "level": "central",
        "institution": "Raffinerie",
        "acronym": "",
        "permissions": [PERM_CONTROLE_EXPORT, PERM_AUDIT_LOGS],
        "description": "Conformite reglementaire de la raffinerie.",
    },
    "centre_test": {
        "level": "central",
        "institution": "Centre agree de test/pesee",
        "acronym": "",
        "permissions": [PERM_CONTROLE_EXPORT],
        "description": "Pesee, test purete et emission de certificat numerique lot.",
    },
    "transporteur_agree": {
        "level": "central",
        "institution": "Transporteur agree",
        "acronym": "",
        "permissions": [PERM_TRANSPORT_OR],
        "description": "Transport des lots avec tracabilite GPS depart/arrivee.",
    },
    "transporteur": {
        "level": "central",
        "institution": "Transporteur",
        "acronym": "",
        "permissions": [PERM_TRANSPORT_OR, PERM_READ_ONLY],
        "description": "Transport des lots OR, scans QR de suivi, sans droit de vente.",
    },
    "com_admin": {
        "level": "central",
        "institution": "Centrale de l'Or de Madagascar",
        "acronym": "COM",
        "permissions": [
            PERM_ADMIN_FILIERE_OR,
            PERM_COM_PARAMETRAGE_NATIONAL,
            PERM_COM_INSTRUCTION_DOSSIERS,
            PERM_COM_VALIDATION_COLLECTEUR,
            PERM_COM_SUIVI_AFFILIATIONS,
            PERM_COM_SANCTIONS_METIER,
            PERM_CARD_VALIDATE_COM,
            PERM_AUDIT_LOGS,
            PERM_CONTROLE_EXPORT,
        ],
        "description": "Parametrage national OR, supervision et sanctions metier COM.",
    },
    "com_agent": {
        "level": "central",
        "institution": "Centrale de l'Or de Madagascar",
        "acronym": "COM",
        "permissions": [
            PERM_COM_INSTRUCTION_DOSSIERS,
            PERM_COM_VALIDATION_COLLECTEUR,
            PERM_COM_SUIVI_AFFILIATIONS,
            PERM_CARD_VALIDATE_COM,
            PERM_CONTROLE_EXPORT,
        ],
        "description": "Instruction dossiers OR et validation cartes collecteurs.",
    },
    "mines_region_agent": {
        "level": "territorial",
        "institution": "Direction regionale des Mines",
        "acronym": "",
        "permissions": [PERM_READ_ONLY, PERM_DASHBOARD_REGIONAL, PERM_MINES_TERRITORIAL_CONTROL],
        "description": "Controle et rapports territoriaux sur la filiere OR.",
    },
    "lab_bgglm": {
        "level": "central",
        "institution": "BGGLM",
        "acronym": "BGGLM",
        "permissions": [PERM_BGGLM_LAB_ENTRY, PERM_ANALYSE_CERTIFICATION, PERM_READ_ONLY],
        "description": "Saisie des analyses, titrages et certificats labo.",
    },
    "douanes_agent": {
        "level": "controle",
        "institution": "Douanes",
        "acronym": "DGD",
        "permissions": [PERM_CONTROLE_EXPORT, PERM_EXPORT_OR_WORKFLOW, PERM_PROFIL_CONTROLEUR],
        "description": "Verification dossier export OR, scellage et PV controle.",
    },
    "gue_or_agent": {
        "level": "central",
        "institution": "GUE OR",
        "acronym": "GUE",
        "permissions": [PERM_GUE_EXPORT, PERM_EXPORT_OR_WORKFLOW, PERM_CONTROLE_EXPORT],
        "description": "Gestion workflow export OR au guichet unique.",
    },
    "raffinerie_agent": {
        "level": "central",
        "institution": "Raffinerie",
        "acronym": "",
        "permissions": [PERM_POINCONNAGE_RAFFINERIE, PERM_CONTROLE_EXPORT],
        "description": "Affinement, poinconnage et serialisation or.",
    },
    "region_agent": {
        "level": "territorial",
        "institution": "Region",
        "acronym": "",
        "permissions": [PERM_READ_ONLY, PERM_DASHBOARD_REGIONAL],
        "description": "Lecture et suivi regional des operations.",
    },
    "district_agent": {
        "level": "territorial",
        "institution": "District",
        "acronym": "",
        "permissions": [PERM_READ_ONLY, PERM_DASHBOARD_REGIONAL],
        "description": "Lecture et suivi district des operations.",
    },
    "pierre_exploitant": {
        "level": "communautaire",
        "institution": "Exploitant pierre",
        "acronym": "",
        "permissions": [PERM_PIERRE_DECLARE_LOT, PERM_PIERRE_TRADE],
        "description": "Declaration des lots pierre et vente locale autorisee.",
    },
    "pierre_collecteur": {
        "level": "communautaire",
        "institution": "Collecteur/Negociant pierre",
        "acronym": "",
        "permissions": [PERM_PIERRE_DECLARE_LOT, PERM_PIERRE_TRADE],
        "description": "Achat local, regroupement et cession des lots pierre.",
    },
    "pierre_lapidaire": {
        "level": "central",
        "institution": "Lapidaire/Transformateur",
        "acronym": "",
        "permissions": [PERM_PIERRE_TRANSFORM, PERM_PIERRE_TRADE],
        "description": "Tri/lavage/taille/polissage et transformation des lots pierre.",
    },
    "pierre_exportateur": {
        "level": "central",
        "institution": "Comptoir/Exportateur pierre",
        "acronym": "",
        "permissions": [PERM_PIERRE_EXPORT, PERM_PIERRE_TRADE, PERM_CONTROLE_EXPORT],
        "description": "Montage dossiers export pierre et transferts finaux.",
    },
    "pierre_controleur_mines": {
        "level": "controle",
        "institution": "Controleur Mines",
        "acronym": "",
        "permissions": [PERM_PIERRE_CONTROL, PERM_PROFIL_CONTROLEUR],
        "description": "Inspection, constats et PV pour la filiere pierre.",
    },
    "pierre_douanes": {
        "level": "controle",
        "institution": "Douanes Pierre",
        "acronym": "",
        "permissions": [PERM_PIERRE_CONTROL, PERM_PIERRE_EXPORT, PERM_CONTROLE_EXPORT],
        "description": "Controle export, scellage et statut exporte des lots pierre.",
    },
    "pierre_commune_agent": {
        "level": "territorial",
        "institution": "Commune Pierre",
        "acronym": "",
        "permissions": [PERM_ADMIN_COMMUNE, PERM_PIERRE_DECLARE_LOT],
        "description": "Enrolement local, frais locaux et suivi territorial pierre.",
    },
    "pierre_admin_central": {
        "level": "central",
        "institution": "Admin central pierre",
        "acronym": "",
        "permissions": [PERM_PIERRE_CATALOG_ADMIN, PERM_PIERRE_EXPORT, PERM_PIERRE_CONTROL, PERM_AUDIT_LOGS],
        "description": "Parametrage central catalogue/regles et supervision filiere pierre.",
    },
    "bois_exploitant": {
        "level": "communautaire",
        "institution": "Exploitant forestier",
        "acronym": "",
        "permissions": [PERM_BOIS_DECLARE_LOT, PERM_BOIS_TRADE],
        "description": "Declaration lots BOIS et cession vers acteurs autorises.",
    },
    "bois_collecteur": {
        "level": "communautaire",
        "institution": "Collecteur bois",
        "acronym": "",
        "permissions": [PERM_BOIS_DECLARE_LOT, PERM_BOIS_TRADE],
        "description": "Achat local, regroupement et vente de lots bois.",
    },
    "bois_transporteur": {
        "level": "central",
        "institution": "Transporteur bois",
        "acronym": "",
        "permissions": [PERM_BOIS_TRANSPORT, PERM_READ_ONLY],
        "description": "Transport national avec laissez-passer et scan QR.",
    },
    "bois_transformateur": {
        "level": "central",
        "institution": "Scieur/Atelier",
        "acronym": "",
        "permissions": [PERM_BOIS_TRANSFORM, PERM_BOIS_TRADE],
        "description": "Transformation grumes vers lots scies et produits.",
    },
    "bois_artisan": {
        "level": "communautaire",
        "institution": "Artisan bois",
        "acronym": "",
        "permissions": [PERM_BOIS_TRANSFORM, PERM_BOIS_TRADE],
        "description": "Fabrication produits finis et ventes autorisees.",
    },
    "bois_exportateur": {
        "level": "central",
        "institution": "Exportateur bois",
        "acronym": "",
        "permissions": [PERM_BOIS_EXPORT, PERM_BOIS_TRADE, PERM_CONTROLE_EXPORT],
        "description": "Montage des dossiers export BOIS et transferts finaux.",
    },
    "bois_forest_admin": {
        "level": "central",
        "institution": "Administration forestiere",
        "acronym": "",
        "permissions": [PERM_ADMIN_FILIERE_BOIS, PERM_BOIS_CONTROL, PERM_BOIS_TRANSPORT],
        "description": "Validation permis, laissez-passer et suivi conformite.",
    },
    "bois_douanes": {
        "level": "controle",
        "institution": "Douanes BOIS",
        "acronym": "",
        "permissions": [PERM_BOIS_CONTROL, PERM_BOIS_EXPORT, PERM_CONTROLE_EXPORT],
        "description": "Controle export BOIS, scelles et statut exporte.",
    },
    "bois_commune_agent": {
        "level": "territorial",
        "institution": "Commune BOIS",
        "acronym": "",
        "permissions": [PERM_ADMIN_COMMUNE, PERM_BOIS_DECLARE_LOT],
        "description": "Enrolement local et suivi frais communaux BOIS.",
    },
    "bois_controleur": {
        "level": "controle",
        "institution": "Controleur BOIS",
        "acronym": "",
        "permissions": [PERM_BOIS_CONTROL, PERM_PROFIL_CONTROLEUR],
        "description": "Controle routier, PV et sanctions metier BOIS.",
    },
    "bois_admin_central": {
        "level": "central",
        "institution": "Admin central BOIS",
        "acronym": "",
        "permissions": [PERM_BOIS_CATALOG_ADMIN, PERM_BOIS_CONTROL, PERM_BOIS_EXPORT, PERM_AUDIT_LOGS],
        "description": "Parametrage essences/regles/checklists et supervision nationale.",
    },
    "banque_centrale": {
        "level": "central",
        "institution": "Banque centrale",
        "acronym": "",
        "permissions": [PERM_RAPATRIEMENT_DEVISES],
        "description": "Validation du rapatriement de devises sur export.",
    },
    "banque_commerciale": {
        "level": "central",
        "institution": "Banque commerciale",
        "acronym": "",
        "permissions": [PERM_RAPATRIEMENT_DEVISES],
        "description": "Transmission des preuves bancaires de rapatriement.",
    },
    "fnp": {
        "level": "central",
        "institution": "Fonds National de Perequation",
        "acronym": "FNP",
        "permissions": [PERM_READ_ONLY],
        "description": "Beneficiaire de 10% de la ristourne miniere.",
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
