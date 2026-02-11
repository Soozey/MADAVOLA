# MADAVOLA – Guide pour la présentation

## Avant la démo

### 1. Installer les dépendances
```bash
cd apps/web
npm install
```
(Si vous utilisez pnpm à la racine : `pnpm install`.)

### 2. Démarrer l’API et la base
```bash
docker compose -f infra/docker/compose.yml up -d --build
```
Attendre que les services soient « Up ». Vérifier : `curl http://localhost:8000/api/v1/health`

### 3. Créer un compte admin (si premier lancement)
Depuis la racine du projet, avec les variables du compose (ou un `.env`) :
```bash
cd services/api
python scripts/create_admin.py
```
(Adapter l’email/mot de passe si le script le demande.)

### 4. Lancer le frontend
```bash
cd apps/web
npm run dev
```
Ouvrir **http://localhost:3000**.

---

## Pendant la démo

1. **Connexion** – Login avec le compte admin (ou un acteur créé).
2. **Tableau de bord** – Bandeau de bienvenue, processus métier, liens rapides selon le rôle.
3. **Rôles** – Menu adapté (Vue nationale, Vue régionale, Ma carte, Acteurs, Lots, Transactions, etc.).
4. **Acteurs** – Liste, création (inscription acteur), détail, empty state expliqué.
5. **Lots** – Liste, déclaration de lot, détail.
6. **Transactions** – Liste, création de transaction, détail.
7. **Ma carte (QR)** – Carte orpailleur/collecteur avec QR code ; scan → page de vérification (sans login).
8. **Vue nationale / régionale** – Dashboards selon habilitations.
9. **Rapports, Audit, Contrôles** – Selon les droits du rôle.

---

## En cas de problème

- **API injoignable** : vérifier que Docker tourne et que le compose est bien démarré (`docker compose -f infra/docker/compose.yml ps`).
- **Erreur de build** : `cd apps/web && npm install && npm run build`.
- **Port 3000 occupé** : modifier le port dans `apps/web/vite.config.ts` (server.port).

---

## Résumé technique

- **Frontend** : React, TypeScript, Vite, TanStack Query — `apps/web`
- **Backend** : FastAPI — `services/api`
- **Base** : PostgreSQL + PostGIS (Docker)
- **Rôles** : 19 autorités (PR, PM, MMRS, COM, etc.) + admin, dirigeant, commune_agent, acteur, orpailleur, contrôleur
- **QR** : Carte acteur avec QR → vérification publique `/verify/actor/:id`
