# MADAVOLA - Delta Filiere PIERRE

## 1) Existant observe (rapide)
- API FastAPI avec modules `lots`, `transactions`, `exports`, `inspections`, `violations`, `penalties`.
- BDD relationnelle avec `lots`, `inventory_ledger`, paiements, audit.
- UI web avec ecrans lots/transactions/exports/controle.
- RBAC deja en place via `actor_roles`.

## 2) Delta implemente dans cette passe
- Lot et workflow PIERRE:
  - extension lot: `sous_filiere`, `product_catalog_id`, `attributes_json`.
  - validation catalogue/attributs/units pour creation lot PIERRE.
- Catalogue produits PIERRE dynamique:
  - endpoints `/catalog/products` (CRUD admin + GET).
  - table `product_catalog`.
- Autorisations PIERRE:
  - endpoints `/actors/{id}/authorizations`.
  - table `actor_authorizations`.
  - blocage operations si autorisation expiree (`trades` + `exports` linking).
- Workflow vente PIERRE:
  - `/trades`, `/trades/{id}/pay`, `/trades/{id}/confirm`.
  - ecritures ledger OUT/IN garanties.
- Workflow export PIERRE:
  - `/exports/{id}/submit`, `/exports/{id}/validate` (mines/douanes), scelles.
  - lot exporte => transfert bloque.
- Notifications expiration:
  - `/notifications` + `/notifications/run-expiry-reminders`.
- UI web:
  - `LotsPage` avec formulaire dynamique PIERRE (sous-filiere + produit catalogue + attributs requis).
  - roles menu et labels PIERRE.
- Migration SQL:
  - `services/api/migrations/sql/0022_pierre_workflow.sql`.

## 3) TODO LEGAL / configurable
- Taxe/frais PIERRE: table `fee_policies` ajoutee (parametrable, pas de hardcode).
- References juridiques a completer dans `fee_policies.legal_reference` (`TODO LEGAL`).

## 4) Gaps restants (non termines dans cette passe)
- Offline mobile draft+sync et politique de conflit.
- Ecrans web/mobile dedies au catalogue admin, transformation avancee, dossier export avance (colis/scelles visuels), statistiques avancees PDF/Excel.
- Tests E2E mobile offline.
