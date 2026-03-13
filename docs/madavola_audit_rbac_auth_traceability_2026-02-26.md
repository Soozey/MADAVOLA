# MADAVOLA Audit + Corrections (2026-02-26)

## 1) Audit roles (RBAC)

- Source technique complete: `services/api/app/auth/roles_config.py`
- Endpoint role catalog: `GET /api/v1/rbac/roles`
- Total roles detectes: **69**
- Matrice complete (code, libelle, description, permissions, type utilisateur):
  - `docs/rbac_roles_matrix_2026-02-26.csv`
  - `docs/rbac_roles_matrix_2026-02-26.json`
  - `exports/rbac_roles_matrix_2026-02-26.xlsx`

### Repartition actuelle

- `TRANSVERSAL`: 26
- `AGENT_ETAT`: 19
- `USAGER`: 15
- `OPERATEUR_PRIVE`: 9

### Incoherences observees

- Des comptes admin voyaient tout le catalogue au login (trop de roles, confusion UX).
- Certains roles "Administration" restent trop generiques cote libelle pour des profils terrain.
- Multiplicite de roles metier avancee exposee a des profils qui n'en ont pas besoin (si mauvais flux de selection).

## 2) Schema RBAC simplifie (UX + metier)

### Regles de simplification appliquees

- Le flux post-login n'impose plus la selection manuelle des roles.
- `GET /rbac/roles?for_current_actor=true` retourne par defaut les roles **effectivement attribues** a l'acteur (meme pour admin).
- Exception maintenue (compatibilite): `include_admin_catalog=true` pour forcer le catalogue complet admin.

### Ciblage terrain recommande

- Orpailleur: `orpailleur` (pas de roles institutionnels/export avance)
- Collecteur local: `collecteur` (plus eventuellement `bijoutier` si cas metier)
- Petits exploitants PIERRE: `pierre_exploitant` (optionnel `pierre_collecteur`)
- Petits exploitants BOIS: `bois_exploitant` / `bois_collecteur` / `bois_artisan` selon activite

## 3) Nouveau flow auth (web + mobile)

### Logique cible implementee

1. Ecran d'entree: `Se connecter` / `S'inscrire`
2. Inscription: choix du role **une seule fois** + creation acteur
3. Connexion: email/telephone + mot de passe
4. API `/auth/me` renvoie roles actifs + `primary_role` + `filieres`
5. Front deduit automatiquement `selectedRole` + `selectedFiliere`
6. Redirection directe vers `/home` (pas de page "Choisir votre role" imposee)
7. Pages `/select-role` et `/select-filiere` conservees en fallback manuel

### Fichiers corriges

- Web:
  - `apps/web/src/contexts/SessionContext.tsx`
  - `apps/web/src/components/SessionGuard.tsx`
  - `apps/web/src/pages/LoginPage.tsx`
  - `apps/web/src/pages/SignupPage.tsx`
  - `apps/web/src/App.tsx`
  - `apps/web/src/utils/sessionDefaults.ts`
- Mobile:
  - `apps/mobile/src/App.tsx`
- API:
  - `services/api/app/auth/schemas.py`
  - `services/api/app/auth/router.py`
  - `services/api/app/rbac/router.py`

## 4) Numerotation structuree lot + tracabilite

### Implante

- `lot_number` auto:
  - Format: `LOT-[REGION]-[PERMIS]-[ANNEE]-[ID]`
- `traceability_id` auto, unique, non modifie ensuite
- `origin_reference` auto:
  - OR: priorite carte Karabola/collecteur validee
  - Sinon: permis d'autorisation actif
- Champs persists:
  - `lot_number`
  - `traceability_id`
  - `origin_reference`
  - `previous_block_hash`
  - `current_block_hash`
  - `trace_payload_json`

### Fichiers

- `services/api/app/common/traceability.py`
- `services/api/app/models/lot.py`
- `services/api/app/lots/router.py`
- `services/api/app/lots/schemas.py`
- `services/api/alembic/versions/0026_lot_traceability_chain.py`

## 5) QR + hash chain (blockchain leger)

### Implante

- SHA256 pour chaque "bloc" lot (event create/transfer/split/consolidate)
- Chaines:
  - `previous_block_hash` -> `current_block_hash`
- QR lot enrichi contient:
  - `lot_id`
  - `origin`
  - historique transactionnel compact
  - `prev_hash`
  - `hash`
- Endpoint verification lot enrichi avec trace/historique:
  - `GET /api/v1/verify/lot/{id}`

### Fichiers

- `services/api/app/lots/router.py`
- `services/api/app/verify/schemas.py`
- `services/api/app/verify/router.py`
- `apps/web/src/pages/VerifyLotPage.tsx`
- `apps/web/src/pages/LotsPage.tsx`

## 6) Verification carte Karabola (front/back/API/DB)

### Controle effectue

- Backend OR compliance present et branche (demande, paiement, validation, signatures QR).
- Verification publique carte active (`/verify/card/{ref}`) avec validation de signature HMAC.
- Front web branche:
  - `apps/web/src/pages/MaCartePage.tsx`
  - `apps/web/src/pages/OrCompliancePage.tsx`
- Modeles DB presents:
  - `kara_bolamena_cards`, `collector_cards`, documents associes, signatures QR.

### Validation technique

- Tests backend OR compliance: **6/6 OK**
  - `services/api/tests/test_or_compliance.py`

## 7) Modifs non visibles front (branchements)

### Controle de couverture API <-> UI

- Script execute: `python scripts/api_ui_contract_audit.py --mode both`
- Resultat:
  - `missing_in_openapi=0`
  - `uncovered_user_ops=0`
- Rapport:
  - `docs/api-ui-contract-report.md`

### Corrections de branchement appliquees

- Session auto-role/filiere branchee sur `/auth/me`
- Redirection login vers `/home`
- Affichage des nouvelles infos de trace dans pages lot/verification
