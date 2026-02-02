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
- type_personne, nom, prenoms, cin, nif, stat, rccm
- telephone (unique), email (unique)
- region_id (FK regions), district_id (FK districts), commune_id (FK communes), fokontany_id (FK fokontany)
- territory_version_id (FK territory_versions), signup_geo_point_id (FK geo_points)
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

### geo_points
- id (PK)
- lat, lon, accuracy_m
- captured_at, source, device_id
- actor_id (FK actors, nullable)

### payment_providers
- id (PK)
- code (unique), name, enabled
- config_json

### payment_requests
- id (PK)
- provider_id (FK payment_providers)
- payer_actor_id (FK actors), payee_actor_id (FK actors)
- fee_id (FK fees), transaction_id (FK trade_transactions)
- amount, currency, status, external_ref (unique), idempotency_key
- created_at

### payments
- id (PK)
- payment_request_id (FK payment_requests)
- status, operator_ref, confirmed_at

### webhook_inbox
- id (PK)
- provider_id (FK payment_providers)
- external_ref (unique per provider)
- received_at, payload_hash, status

### fees
- id (PK)
- fee_type, actor_id (FK actors), commune_id (FK communes)
- amount, currency, status, created_at, paid_at

### audit_logs
- id (PK)
- actor_id (FK actors, nullable)
- action, entity_type, entity_id
- justification, meta_json, created_at

### trade_transactions
- id (PK)
- seller_actor_id (FK actors), buyer_actor_id (FK actors)
- status, total_amount, currency, created_at

### trade_transaction_items
- id (PK), transaction_id (FK trade_transactions)
- lot_id (nullable), quantity, unit_price, line_amount

### invoices
- id (PK)
- invoice_number (unique)
- transaction_id (FK trade_transactions)
- seller_actor_id (FK actors), buyer_actor_id (FK actors)
- issue_date, total_amount, status

### documents
- id (PK)
- doc_type, owner_actor_id (FK actors)
- related_entity_type, related_entity_id
- storage_path, original_filename, sha256
- created_at

### lots
- id (PK)
- filiere, product_type, unit, quantity
- declared_at, declared_by_actor_id (FK actors)
- current_owner_actor_id (FK actors)
- status, declare_geo_point_id (FK geo_points)
- parent_lot_id (FK lots, nullable)

### lot_links
- id (PK)
- parent_lot_id (FK lots), child_lot_id (FK lots)
- relation_type, quantity_from_child

### inventory_ledger
- id (PK)
- actor_id (FK actors), lot_id (FK lots)
- movement_type, quantity_delta
- ref_event_type, ref_event_id, created_at
