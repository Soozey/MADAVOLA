# MADAVOLA RBAC Front-Back Audit (Phase A/B/C)

Date: 2026-02-23  
Scope: API FastAPI + DB PostgreSQL + Front Web/Mobile + RBAC workflows.

## A1) Cartographie RBAC executee

### Filières trouvées en BDD
- Source `actor_filieres`: `OR`, `PIERRE`, `BOIS`
- Source `lots.filiere`: vide sur cette DB de demo (aucun lot persisté)

### Rôles trouvés
- Source runtime permissions: `ROLE_DEFINITIONS` (68 rôles)
- Source BDD d’assignation (`actor_roles`): rôles effectivement attribués aux acteurs
- Ajout structure metadata BDD: table `rbac_role_catalog`
  - colonnes: `code`, `label`, `description`, `category`, `filiere_scope_csv`, `tags_csv`, `is_active`, `display_order`
  - état: seed effectué (68 lignes)

### Endpoints RBAC/API vérifiés (OpenAPI)
- `GET /api/v1/rbac/filieres`
- `GET /api/v1/rbac/roles`
- `GET /api/v1/rbac/permissions`
- `GET /api/v1/rbac/roles-with-permission`

## A2) API existe mais UI ne consomme pas

### Avant correction
- `/rbac/permissions`: peu/pas consommé côté sélecteur.
- `/rbac/filieres`: absent (donc filières hardcodées dans le sélecteur rôle).

### Après correction
- `/rbac/filieres`: consommé dans `RoleSelectPage`.
- `/rbac/roles`: consommé avec filtres `filiere/search/category/active_only/for_current_actor`.
- `/rbac/permissions`: consommé pour aperçu permissions du rôle sélectionné.
- Mobile: `/rbac/roles` consommé avec filtres cohérents.

## A3) UI consomme mais back non branché

### Corrections
- Ajout endpoint `GET /rbac/filieres`.
- Extension schéma `GET /rbac/roles` (category/order/tags/is_active).
- Filtrage backend `include_common` + `for_current_actor`.

## A4) Bug “ça ne s’ouvre pas”

### Reproduction et cause
- Sélecteur rôle dense (mur de cartes), clic peu lisible, état sélection peu perceptible.
- Dans certains cas UX, l’utilisateur pensait cliquer sans changement.

### Correctifs
- Passage à une liste compacte (mobile first) + bouton `Choisir`.
- Ligne entière cliquable + clavier (`Enter`/`Space`) + focus.
- États robustes: loading skeleton, error + retry, empty state.
- Header sticky avec filière/recherche/filtres.

## B) Refonte UX/UI `select-role` (web + mobile)

## Web
- Étape filière par chips.
- Recherche texte.
- Filtre catégorie.
- Toggle `Afficher roles transversaux` (par défaut OFF pour éviter surcharge).
- Groupement par catégorie avec sections repliables et compteurs.
- Liste compacte (mobile first) au lieu d’une grille massive.

## Mobile
- Rôles dynamiques par filière (`include_common=false` + `for_current_actor=true`).
- Recherche + catégorie dans l’onglet Acteurs.
- Liste groupée et sélection explicite d’un rôle.

## C) Garanties “tout est branché”

### Tests backend
- `tests/test_rbac_roles_endpoint.py`
  - filtre filière (`include_common=false`)
  - filtre par utilisateur (`for_current_actor=true`)

### Tests front
- `src/pages/__tests__/RoleSelectPage.dom.test.tsx`
  - recherche + catégorie + sélection + navigation
- `src/__tests__/appNavigation.dom.test.tsx`
  - parcours rôle -> filière -> home
- `src/utils/__tests__/rbacOptions.test.ts`

### E2E workflow API
- `services/api/scripts/e2e_cli.py` passe (OR/PIERRE/BOIS, ledger strict, export freeze).

## Endpoints user-facing couverts UI (RBAC & sélection)
- Web:
  - `GET /rbac/filieres`
  - `GET /rbac/roles`
  - `GET /rbac/permissions`
- Mobile:
  - `GET /rbac/roles`

## Migrations / DB
- Ajout migration: `services/api/alembic/versions/0021_rbac_role_catalog.py`
- Compat startup: seed auto si table vide (sans casser les environnements sans Alembic actif).

