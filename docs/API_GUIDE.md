# Guide API MADAVOLA

## Authentification

### Login
```bash
POST /api/v1/auth/login
{
  "identifier": "email@example.com" ou "0340000000",
  "password": "secret"
}
```

Réponse:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

### Utilisation du token
Ajouter dans les headers:
```
Authorization: Bearer <access_token>
```

### Refresh token
```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "..."
}
```

### Profil utilisateur
```bash
GET /api/v1/auth/me
Authorization: Bearer <token>
```

Retourne le profil complet avec territoire et rôles.

## Workflows principaux

### 1. Inscription acteur
1. Créer GeoPoint: `POST /api/v1/geo-points`
2. Inscription: `POST /api/v1/actors` (avec geo_point_id)
3. Paiement frais ouverture (si requis)
4. Activation par admin/commune

### 2. Déclaration lot
1. Créer GeoPoint: `POST /api/v1/geo-points`
2. Déclarer lot: `POST /api/v1/lots`
3. Ledger mis à jour automatiquement

### 3. Transaction et paiement
1. Créer transaction: `POST /api/v1/transactions`
2. Initier paiement: `POST /api/v1/transactions/{id}/initiate-payment`
3. Webhook confirme le paiement
4. Facture générée automatiquement

### 4. Transfert lot
1. Créer payment request
2. Transférer: `POST /api/v1/lots/{id}/transfer`
3. Ledger mis à jour (sortie pour vendeur, entrée pour acheteur)

## Pagination

Toutes les listes supportent la pagination:
```
GET /api/v1/lots?page=1&page_size=50
GET /api/v1/transactions?page=2&page_size=100
```

Réponse:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

## Codes d'erreur

- `400`: Bad Request (données invalides)
- `401`: Unauthorized (token manquant/invalide)
- `403`: Forbidden (permissions insuffisantes)
- `404`: Not Found (ressource introuvable)
- `409`: Conflict (conflit de données)
- `422`: Unprocessable Entity (validation échouée)

Format d'erreur:
```json
{
  "detail": {
    "message": "code_erreur",
    "details": {...}
  }
}
```

## RBAC

### Rôles
- `admin`: Accès complet
- `dirigeant`: Accès complet (sauf config système)
- `commune_agent`: Accès limité à sa commune
- `controleur`: Peut créer inspections
- `acteur`: Utilisateur standard (orpailleur, négociant, etc.)

### Scopes territoriaux
- Admin/Dirigeant: Tous les territoires
- Commune agent: Uniquement sa commune
- Acteur: Uniquement ses propres ressources

## Validation

### Téléphone
Format: `03XXXXXXXX` (10 chiffres, commence par 03)

### Email
Format standard RFC 5322

### Coordonnées GPS
- Latitude: [-90, 90]
- Longitude: [-180, 180]

### Quantités
- Doivent être positives
- Précision: 4 décimales

## Webhooks paiements

### Endpoint
```
POST /api/v1/payments/webhook/{provider_code}
```

### Sécurité
- Signature vérifiée (si configurée)
- IP allowlist (si configurée)
- Idempotence via `external_ref`

### Payload
```json
{
  "external_ref": "unique_ref",
  "status": "success" | "failed",
  "operator_ref": "OP123"
}
```

## Audit

Toutes les actions sensibles sont loggées:
- Création/modification acteurs
- Création/modification lots
- Transactions
- Paiements
- Exports
- Inspections

Consultation: `GET /api/v1/audit`
