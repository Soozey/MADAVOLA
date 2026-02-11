# MADAVOLA

Plateforme de gestion de transactions pour la filière agricole à Madagascar.

## 🚀 Démarrage rapide (développement)

### Prérequis
- Node.js 20+
- Python 3.12+
- Docker et Docker Compose
- pnpm (optionnel, sinon utiliser `npm`)

### Installation

1. **Installer les dépendances frontend** :
   ```bash
   cd apps/web
   npm install
   ```
   (À la racine : `pnpm install` si pnpm est installé, sinon `npm install` dans chaque app.)

2. **Lancer l'infrastructure de développement** :
   ```bash
   docker compose -f infra/docker/compose.yml up -d --build
   ```

3. **Vérifier que l'API fonctionne** :
   ```bash
   curl http://localhost:8000/api/v1/health
   ```
   (En dev, le frontend utilise le proxy Vite : pas besoin de copier `.env` si l'API tourne via Docker avec les variables du `compose`.)

4. **Lancer le frontend en mode développement** :
   ```bash
   cd apps/web
   npm run dev
   ```

5. **Accéder à l'application** :
   - Frontend : http://localhost:3000
   - API : http://localhost:8000
   - Documentation API : http://localhost:8000/docs

### Lancer sans Docker (API et front sur la machine)

Vous pouvez n’utiliser Docker que pour la base de données, et lancer l’API et le front en local.

1. **Démarrer uniquement la base** :
   ```bash
   docker compose -f infra/docker/compose.dev-db-only.yml up -d
   ```

2. **Créer un fichier `.env` dans `services/api`** (uvicorn charge le `.env` depuis ce dossier) :
   ```bash
   cd services/api
   cp env.example.local .env
   ```
   Contenu : `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/madavola` et `JWT_SECRET=change_me_jwt_secret_key_min_32_chars_dev`.

3. **Migrations et admin** (depuis `services/api`) :
   ```bash
   cd services/api
   pip install -r requirements.txt
   alembic upgrade head
   python scripts/create_admin.py
   ```

4. **Lancer l’API en local** :
   Depuis la racine : `.\scripts\run-local.ps1` (Windows) ou `./scripts/run-local.sh` (Linux/Mac). Sinon : `cd services/api` puis `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.

5. **Lancer le frontend** (autre terminal) :
   ```bash
   cd apps/web
   npm run dev
   ```

6. Ouvrir http://localhost:3000 et se connecter avec le compte administrateur créé via `python scripts/create_admin.py`.

**Si la page affiche « Identifiant ou mot de passe incorrect »** : le compte admin n’existe pas ou le mot de passe a été changé. Réinitialisez-le :
- **Avec Docker** (API lancée via `compose.yml`) : à la racine du projet :  
  `docker compose -f infra/docker/compose.yml exec api python scripts/reset_admin_password.py`  
  Puis reconnectez-vous avec le compte administrateur de votre environnement.
- **Sans Docker** (API en local) : depuis `services/api`, avec un `.env` dont le `DATABASE_URL` correspond à votre PostgreSQL :  
  `python scripts/reset_admin_password.py`  
  Si l’admin n’existe pas encore : `python scripts/create_admin.py`.

Plus tard, vous pourrez tout dockeriser avec `docker compose -f infra/docker/compose.yml up -d`.

### Pour présenter le projet

1. Démarrer l'API et la base : `docker compose -f infra/docker/compose.yml up -d --build`
2. Créer un compte admin si besoin : `cd services/api && python scripts/create_admin.py` (avec les variables d'environnement du compose)
3. Lancer le frontend : `cd apps/web && npm install && npm run dev`
4. Ouvrir http://localhost:3000 — se connecter, parcourir Tableau de bord, Acteurs, Lots, Transactions, Ma carte (QR), Vue nationale/régionale selon les rôles.
5. Optionnel : lancer web-admin pour l'attribution des rôles : `cd apps/web-admin && npm install && npm run dev` (autre port si configuré).

## 📦 Déploiement en production

Consultez le guide complet dans [DEPLOYMENT.md](./DEPLOYMENT.md).

### Déploiement rapide

1. **Configurer les variables d'environnement** :
   ```bash
   cp env.example .env
   # Éditer .env avec vos valeurs (JWT_SECRET, POSTGRES_PASSWORD, VITE_API_URL en prod)
   ```
   En développement, le frontend utilise par défaut le proxy (`/api/v1`). Pour la prod, définir `VITE_API_URL` sur l’URL réelle de l’API.

2. **Déployer** :
   ```bash
   # Linux/Mac
   ./scripts/deploy.sh prod
   
   # Windows
   .\scripts\deploy.ps1 prod
   ```

## 🏗️ Architecture

```
MADAVOLA/
├── apps/
│   ├── web/          # Application React (frontend utilisateur)
│   ├── web-admin/    # Application React (frontend admin)
│   └── mobile/       # Application mobile (à venir)
├── services/
│   └── api/          # API FastAPI (backend)
├── infra/
│   └── docker/       # Configurations Docker
├── docs/             # Documentation
└── scripts/          # Scripts de déploiement
```

## 📚 Documentation

- [Guide de déploiement](./DEPLOYMENT.md)
- [Documentation API](./docs/API_GUIDE.md)
- [Schéma de base de données](./docs/db_schema.md)
- [Spécification OpenAPI](./docs/openapi.v1.yaml)

## 🛠️ Technologies

- **Frontend** : React, TypeScript, Vite, TanStack Query
- **Backend** : FastAPI, Python, SQLAlchemy, Alembic
- **Base de données** : PostgreSQL avec PostGIS
- **Déploiement** : Docker, Docker Compose, Nginx

## 📝 Licence

MIT. Voir le fichier [LICENSE](./LICENSE) pour le texte complet.
