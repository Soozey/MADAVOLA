# Optimisations DB et Performance

## Index ajoutés (Migration 0016)

### Actors
- `ix_actors_commune_id` : Filtrage RBAC par commune
- `ix_actors_status` : Filtrage par statut
- `ix_actors_region_id`, `ix_actors_district_id` : Jointures territoriales

### Actor Roles (critique pour RBAC)
- `ix_actor_roles_actor_id_status` : Vérifications RBAC fréquentes
- `ix_actor_roles_role` : Filtrage par rôle

### Inventory Ledger
- `ix_inventory_ledger_actor_id` : Filtrage par acteur
- `ix_inventory_ledger_lot_id` : Filtrage par lot
- `ix_inventory_ledger_created_at` : Filtrage temporel
- `ix_inventory_ledger_movement_type` : Filtrage par type
- `ix_inventory_ledger_actor_created` : Composite pour reports

### Trade Transactions
- `ix_trade_transactions_seller_actor_id`, `ix_trade_transactions_buyer_actor_id` : Filtrage par acteur
- `ix_trade_transactions_status` : Filtrage par statut
- `ix_trade_transactions_created_at` : Filtrage temporel
- `ix_trade_transactions_seller_created` : Composite pour reports

### Documents
- `ix_documents_owner_actor_id` : Filtrage RBAC
- `ix_documents_related_entity` : Filtrage par entité liée
- `ix_documents_doc_type` : Filtrage par type

### Autres tables
- Lots, Payments, Exports, Audit logs : Index sur colonnes fréquemment filtrées

## Optimisations de requêtes

### Endpoint `/me`
- Les territoires sont chargés séparément (4 requêtes) mais les tables sont petites
- Les rôles sont déjà chargés via relationship
- **Amélioration future** : Utiliser `joinedload` ou `selectinload` pour eager loading

### Reports
- Utilisation de `func.sum()` avec filtres indexés
- Jointures optimisées avec index sur `commune_id`

### Ledger
- Agrégations avec `GROUP BY` sur colonnes indexées
- Filtres temporels utilisent index `created_at`

## Recommandations futures

1. **Pagination** : Ajouter pagination sur toutes les listes (limite par défaut 100)
2. **Cache** : Considérer Redis pour :
   - Territoire (rarement modifié)
   - Config système
   - Rôles actifs (TTL court)
3. **Eager loading** : Utiliser `joinedload` pour éviter N+1 dans :
   - `/me` endpoint
   - Listes avec relations
4. **Query optimization** : Analyser avec `EXPLAIN ANALYZE` sur données réelles
