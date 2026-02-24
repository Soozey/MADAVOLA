# MADAVOLA - Checklist Passage Live (Demo)
Date audit: **2026-02-24 17:39:57 +03:00**

## 1) Preflight technique
- [x] API up: `http://localhost:8000` (root OK, docs exposed)
- [x] Web up: `http://localhost:3000`
- [x] Mobile web up: `http://localhost:5175`
- [x] Contrat API↔UI bidirectionnel: `npm run check:api-ui` => PASS (`missing_in_openapi=0`, `uncovered_user_ops=0`)
- [x] Build web: `npm run build --workspace apps/web` => PASS
- [x] Build mobile: `npm run build --workspace apps/mobile` => PASS
- [x] Tests unit/smoke web: `npm run test --workspace apps/web` => PASS
- [x] Tests unit/smoke mobile: `npm run test --workspace apps/mobile` => PASS
- [x] Tests E2E Playwright web mobile viewport: `npm run test:e2e --workspace @madavola/web` => PASS

## 2) Vérification écran par écran (admin)
Compte vérifié: `kariboservices@gmail.com`

Parcours validé: `Login -> Select role -> Select filiere -> Home`

- [x] `Acteurs` (`/actors`) visible et chargé
- [x] `Lots` (`/lots`) visible et chargé
- [x] `Transactions` (`/transactions`) visible et chargé
- [x] `Dossiers export` (`/exports`) visible et chargé
- [x] `Documents` (`/documents`) visible et chargé
- [x] `Ma carte` (`/ma-carte`) visible et chargée
- [x] `Demandes de cartes OR / queue commune` (`/or-compliance`) visible et chargée

## 3) Vérification API des modules critiques (auth admin)
Résultat via appel direct API avec token admin:

- [x] `GET /api/v1/actors?page=1&page_size=5` => 200
- [x] `GET /api/v1/lots?page=1&page_size=5` => 200
- [x] `GET /api/v1/transactions?page=1&page_size=5` => 200
- [x] `GET /api/v1/exports` => 200
- [x] `GET /api/v1/documents` => 200
- [x] `GET /api/v1/or-compliance/cards/my` => 200
- [x] `GET /api/v1/or-compliance/cards/commune-queue?status=pending` => 200

## 4) Points de contrôle démo (métier)
- [x] Sélection rôle/filière persistée en session (web)
- [x] Changement rôle/filière disponible depuis le layout
- [x] Endpoints user-facing audités et couverts côté UI (pas d’endpoint “fantôme” détecté)
- [x] Territoires chargés (région/district/commune/fokontany) et exploitables dans formulaires

## 5) GO / NO-GO
**GO DEMO** si:
- les 3 services répondent (8000/3000/5175),
- login admin fonctionne,
- le parcours écran par écran ci-dessus passe sans erreur réseau/token.

## 6) Commandes de relance rapide
```powershell
# API
cd services/api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Web
cd ../../
npm run dev --workspace @madavola/web -- --host 0.0.0.0 --port 3000

# Mobile web
npm run dev --workspace @madavola/mobile -- --host 0.0.0.0 --port 5175
```

