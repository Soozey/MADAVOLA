# MADAVOLA - Multi-roles + Inscription/Validation (2026-02-26)

## Audit initial (avant correction)
- Le workflow inscription existait deja: creation acteur en `pending`, validation par `admin|dirigeant|commune_agent`.
- Le selecteur de role existait, mais etait force vers un role derive meme en multi-role (impossible de rester sur l'ecran choix role).
- Aucun mecanisme backend n'imposait le changement de mot de passe au 1er login.
- Aucun seed global n'existait pour creer automatiquement un compte par role + comptes territoriaux.

## Corrections appliquees
- Ajout d'un flag de securite mot de passe sur `actor_auth`:
  - `must_change_password`
  - `password_changed_at`
  - `last_login_at`
- Ajout endpoint API: `POST /api/v1/auth/change-password`.
- Blocage backend si mot de passe obligatoire non change:
  - toutes routes protegees bloquees
  - exceptions autorisees: `/auth/me`, `/auth/change-password`, `/auth/logout`, `/auth/refresh`
- `POST /api/v1/auth/login` renvoie maintenant `must_change_password`.
- `GET /api/v1/auth/me` expose `must_change_password`.
- Workflow notifications inscription/validation renforce dans `actors/router.py`.
- Web:
  - nouvelle page `/change-password`
  - redirection login dynamique:
    - multi-role -> `/select-role`
    - mot de passe obligatoire -> `/change-password`
  - correction SessionGuard/SessionContext pour vrai parcours multi-role.
- Mobile:
  - nouvel etat `change_password`
  - changement mot de passe obligatoire avant acces dashboard
  - correction selection multi-role (plus de fallback catalogue global)

## Seed comptes demo
- Script idempotent ajoute: `services/api/scripts/seed_demo_accounts.py`
- Couvre:
  - 1 compte par role RBAC
  - comptes territoriaux region/district/commune
  - compte admin multi-role pour demo (`admin@madavola.mg`)
- Mot de passe par defaut: `admin123`
- Changement mot de passe force au premier login pour tous les comptes demo.

## Exports comptes
- CSV: `services/api/exports/demo_accounts_2026-02-26.csv`
- Copie telechargeable facile:
  - `C:\Users\Laptop\Downloads\demo_accounts_2026-02-26.csv`
  - `C:\Users\Laptop\Downloads\madavola_demo_accounts_2026-02-26.xlsx`

## Verification executee
- Alembic local: `alembic upgrade head` OK jusqu'a `0029_actor_auth_password_rotation_flags`.
- Tests API cibles: 6 passes
  - `tests/test_auth.py`
  - `tests/test_auth_password_rotation.py`
  - `tests/test_signup_flow.py`
- Build web: OK
- Build mobile: OK
- Verification login comptes seedes: 72/72 OK (password `admin123`, flag changement mot de passe = true)
