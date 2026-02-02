## Schéma DB v1 (extrait)

### territory_versions
- id (PK)
- version_tag (unique)
- source_filename
- checksum_sha256
- status (importing|active|failed|archived)
- imported_at
- activated_at

### regions
- id (PK), version_id (FK territory_versions)
- code, name, name_normalized
- unique(version_id, code)
- unique(version_id, name_normalized)

### districts
- id (PK), version_id (FK territory_versions), region_id (FK regions)
- code, name, name_normalized
- unique(version_id, region_id, code)
- unique(version_id, region_id, name_normalized)

### communes
- id (PK), version_id (FK territory_versions), district_id (FK districts)
- code, name, name_normalized
- mobile_money_msisdn, latitude, longitude
- unique(version_id, district_id, code)
- unique(version_id, district_id, name_normalized)

### fokontany
- id (PK), version_id (FK territory_versions), commune_id (FK communes)
- code (nullable), name, name_normalized
- unique(version_id, commune_id, code)
- unique(version_id, commune_id, name_normalized)

### actors
- id (PK)
- type_personne, nom, prenoms
- telephone (unique), email (unique)
- status, created_at

### actor_roles
- id (PK), actor_id (FK actors)
- role, status, valid_from, valid_to

### actor_auth
- id (PK), actor_id (FK actors, unique)
- password_hash, is_active

### refresh_tokens
- id (PK), actor_id (FK actors)
- token_id (unique), expires_at, revoked_at
