# MADAVOLA - Audit + Corrections (RBAC/Auth/Facturation/Karabola/Bois CITES)

Date: 2026-02-26

## 1) Audit rapide de l'existant (avant correction)

- RBAC:
  - Referentiel roles/permissions deja present (`/rbac/roles`, `/rbac/permissions`).
  - Matrice complete deja exportee: `docs/rbac_roles_matrix_2026-02-26.csv`, `docs/rbac_roles_matrix_2026-02-26.json`, `exports/rbac_roles_matrix_2026-02-26.xlsx`.
- Auth:
  - Flux login/signup deja present, avec role choisi a l'inscription cote web/mobile.
  - Session role/filiere derivee depuis `/auth/me`.
- Facturation:
  - Base invoice/receipt deja existante, mais structure facture incomplète (taxes/trace/hash/recu lie facture).
- Karabola:
  - Flux riche deja present dans `or-compliance` + verification publique `/verify/card/{card_ref}`.
  - Endpoints demandes (`GET /karabola`, verify, link user) absents comme alias explicites.
- Bois/CITES:
  - Workflow BOIS deja present (essences, transport, transformations, approvals).
  - Classification legale CITES/LAF/NDF/non-exportable non unifiee sur les lots.

## 2) Corrections implementees

### 2.1 Facturation + recus (critique)

- Extension du modele `invoices`:
  - filiere, region, origine, lots references, quantites/unites, subtotal HT, taxes detaillees, TTC,
  - hash facture, hash precedent, signature interne, payload de trace,
  - recu lie (`receipt_number`, `receipt_document_id`), immutabilite (`is_immutable`).
- Generation automatique facture enrichie + recu lie facture au paiement valide:
  - Numerotation facture: `FAC-[ANNEE]-[FILIERE]-[REGION]-[ID]`
  - Numerotation recu: `REC-[ANNEE]-[ID]`
  - Hash SHA256 + signature HMAC.
- Couvre maintenant:
  - flux `transactions` (webhook paiement/finalisation),
  - flux `trades` (cash declared + confirmation transfer).
- Exposition API complete des champs facture:
  - `/invoices`, `/invoices/{id}`, `/verify/invoice/{ref}`.

### 2.2 Karabola (validation complete)

- Ajout des aliases API demandes:
  - `GET /api/v1/karabola`
  - `POST /api/v1/karabola/verify`
  - `POST /api/v1/karabola/link-user`
- Les endpoints historiques restent actifs (`/or-compliance/*`, `/verify/card/*`), donc pas de rupture.

### 2.3 Bois CITES + classification

- Extension du modele `lots`:
  - `wood_classification`: `LEGAL_EXPORTABLE | LEGAL_NON_EXPORTABLE | ILLEGAL | A_DETRUIRE`
  - `cites_laf_status`, `cites_ndf_status`, `cites_international_status`
  - champs destruction (statut, dates, preuves).
- Classification automatique a la creation BOIS (selon essence/CITES/export).
- Endpoint de mise a jour metier:
  - `PATCH /api/v1/lots/{id}/wood-classification`
- Blocages export BOIS renforces:
  - bloque si lot `ILLEGAL`/`A_DETRUIRE`/`LEGAL_NON_EXPORTABLE`,
  - exige LAF/NDF/validation internationale `approved` pour lots CITES,
  - conserve le verrou essence protegee avec logique d'approval existante.

### 2.4 Front reconnecte (visibilite)

- `InvoicesPage`:
  - affiche HT/Taxes/TTC, origine, hash, statut,
  - verification facture,
  - telechargement recu lie a la facture.
- `VerifyInvoicePage`:
  - affiche hash, hash precedent, signature, recu, champs CITES/filiere.
- `LotsPage` + `LotDetailPage`:
  - affichent classification BOIS et statuts LAF/NDF/international.
- `LotDetailPage`:
  - branchement UI sur `PATCH /lots/{id}/wood-classification`.

## 3) Schema de numerotation et trace

- Facture: `FAC-[ANNEE]-[FILIERE]-[REGION]-[ID]`
- Recu: `REC-[ANNEE]-[ID]`
- Lot: deja en place `LOT-[REGION]-[PERMIS]-[ANNEE]-[ID]`
- Trace:
  - hash precedent + hash courant (SHA256),
  - payload canonique signe (HMAC),
  - QR lot/facture conservant identifiants et trace courte.

## 4) Modules corriges/non connectes

- Corriges/reconnectes:
  - facture enrichie exposee API + front,
  - recu lie facture expose,
  - endpoint BOIS classification branche cote front,
  - aliases Karabola exposes.
- Contrat API/UI:
  - `python scripts/api_ui_contract_audit.py --mode both` => `PASS` (aucun endpoint user-facing non couvert).
