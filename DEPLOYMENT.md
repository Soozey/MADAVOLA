# Guide de déploiement MADAVOLA

Ce guide explique comment déployer l'application MADAVOLA en production.

## Prérequis

- Docker et Docker Compose installés
- Au moins 4GB de RAM disponible
- Ports 80, 8000, 8080 disponibles (ou configurés différemment)

## Configuration

### 1. Configuration des variables d'environnement

Copiez le fichier `env.example` vers `.env` :

```bash
cp env.example .env
```

Éditez le fichier `.env` et configurez les valeurs suivantes :

#### Variables critiques à modifier :

- `POSTGRES_PASSWORD` : Mot de passe fort pour la base de données
- `JWT_SECRET` : Clé secrète d'au moins 32 caractères pour JWT
- `VITE_API_URL` : URL de l'API (en production, utilisez le domaine réel)

#### Exemple de configuration production :

```env
POSTGRES_PASSWORD=un_mot_de_passe_tres_securise_123!
JWT_SECRET=une_cle_secrete_tres_longue_et_aleatoire_minimum_32_caracteres
VITE_API_URL=https://api.votredomaine.com/api/v1
```

## Déploiement

### Option 1 : Script de déploiement (recommandé)

#### Linux/Mac :
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh prod
```

#### Windows (PowerShell) :
```powershell
.\scripts\deploy.ps1 prod
```

### Option 2 : Docker Compose manuel

```bash
# Construire les images
docker compose -f infra/docker/compose.prod.yml build

# Démarrer les services
docker compose -f infra/docker/compose.prod.yml up -d

# Vérifier les logs
docker compose -f infra/docker/compose.prod.yml logs -f
```

## Vérification

Une fois déployé, vérifiez que tous les services sont en cours d'exécution :

```bash
docker compose -f infra/docker/compose.prod.yml ps
```

Tous les services doivent avoir le statut "Up" et être en bonne santé.

### Tests de santé

- **API** : `curl http://localhost:8000/api/v1/health`
- **Web** : Ouvrir `http://localhost:80` dans un navigateur
- **Nginx** : Ouvrir `http://localhost:8080` dans un navigateur

## Architecture de déploiement

```
┌─────────────┐
│   Nginx     │ (Port 8080) - Reverse proxy
│  (Portail)  │
└──────┬──────┘
       │
       ├───► Web (Port 80) - Application React
       │
       └───► API (Port 8000) - FastAPI
                │
                └───► PostgreSQL/PostGIS (Port 5432)
```

## Gestion des services

### Arrêter les services

```bash
docker compose -f infra/docker/compose.prod.yml down
```

### Redémarrer un service spécifique

```bash
docker compose -f infra/docker/compose.prod.yml restart api
```

### Voir les logs

```bash
# Tous les services
docker compose -f infra/docker/compose.prod.yml logs -f

# Un service spécifique
docker compose -f infra/docker/compose.prod.yml logs -f api
```

### Mettre à jour l'application

```bash
# Reconstruire et redémarrer
docker compose -f infra/docker/compose.prod.yml up -d --build
```

## Sauvegarde de la base de données

### Créer une sauvegarde

```bash
docker compose -f infra/docker/compose.prod.yml exec db pg_dump -U postgres madavola > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurer une sauvegarde

```bash
docker compose -f infra/docker/compose.prod.yml exec -T db psql -U postgres madavola < backup.sql
```

## Dépannage

### Les services ne démarrent pas

1. Vérifiez les logs : `docker compose -f infra/docker/compose.prod.yml logs`
2. Vérifiez que les ports ne sont pas déjà utilisés
3. Vérifiez que le fichier `.env` est correctement configuré

### L'API ne répond pas

1. Vérifiez la connexion à la base de données
2. Vérifiez les variables d'environnement JWT_SECRET
3. Consultez les logs : `docker compose -f infra/docker/compose.prod.yml logs api`

### Le frontend ne se charge pas

1. Vérifiez que l'API est accessible
2. Vérifiez la variable `VITE_API_URL` dans `.env`
3. Reconstruisez l'image web : `docker compose -f infra/docker/compose.prod.yml build web`

## Sécurité en production

⚠️ **Important** : Avant de déployer en production, assurez-vous de :

1. ✅ Changer tous les mots de passe par défaut
2. ✅ Utiliser des secrets forts (JWT_SECRET, POSTGRES_PASSWORD)
3. ✅ Configurer un reverse proxy avec SSL/TLS (HTTPS)
4. ✅ Limiter l'accès aux ports de base de données
5. ✅ Configurer un pare-feu approprié
6. ✅ Mettre en place des sauvegardes régulières
7. ✅ Surveiller les logs pour détecter les anomalies

## Support

Pour toute question ou problème, consultez la documentation dans le dossier `docs/` ou ouvrez une issue.
