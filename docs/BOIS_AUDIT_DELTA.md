# MADAVOLA - Audit rapide filiere BOIS et delta implemente

## Existant detecte avant cette passe
- Filiere BOIS presente seulement comme valeur de selection UI (`OR/PIERRE/BOIS`) sans workflow metier complet.
- Moteur lot/QR/ledger deja existant (create, split, consolidate, transfer).
- Workflow export generique deja en place (dossier, checklist, validation, scellage).
- RBAC existant large (roles historiques + OR + PIERRE), mais roles BOIS metier manquants.
- Aucun catalogue essences dedie, aucun workflow transport BOIS dedie, aucune exception export essence protegee.

## Gaps identifies
- Pas de table `EssenceCatalog` ni policies BOIS parametrees.
- Pas de contraintes BOIS a la creation de lot (essence/forme/unites/docs/checklist).
- Pas de workflow transport BOIS (record multi-lots + scan verification).
- Pas de transformation BOIS inputs->outputs dediee.
- Pas de workflow approbation d'exception export BOIS.
- RBAC BOIS incomplet.

## Delta implemente
- Modeles/tables BOIS:
  - `essence_catalog`
  - `rule_policies`
  - `checklist_policies`
  - `transport_records`, `transport_record_items`
  - `workflow_approvals`
  - `transformation_events`, `transformation_links`
  - extension `lots`: `wood_essence_id`, `wood_form`, `volume_m3`
- Endpoints:
  - `/catalog/essences` GET/POST/PUT/DELETE
  - `/transports` POST
  - `/transports/{id}/scan_verify` POST
  - `/transformations` POST
  - `/approvals` POST/GET
  - `/approvals/{id}/decide` POST
- Blocages/regles BOIS:
  - lot BOIS: essence+forme+unites + autorisation BOIS active + role autorise
  - checklist documents parametree via `checklist_policies`
  - trade BOIS: RBAC de chemin vendeur->acheteur + autorisation active
  - export BOIS: categorie `A_protegee` + `export_autorise=false` => bloque sauf approval exceptionnel
- UI web:
  - Lot BOIS (essence + forme + volume)
  - pages `Transports` et `Transformations`
- Migration SQL: `0023_bois_workflow.sql`
- Tests acceptance BOIS: `test_bois_workflow.py`

## TODO LEGAL
- Renseigner `reference_texte` + version juridique precise dans `rule_policies`, `checklist_policies`, `workflow_approvals`.
- Completer la table des documents requis par categorie/operation (parametrage initial).
- Completer mobile offline draft/sync pour ecrans BOIS terrain.
