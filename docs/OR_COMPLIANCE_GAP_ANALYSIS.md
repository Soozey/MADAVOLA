# MADAVOLA OR Compliance Gap Analysis (L2023-007 / D2024-1345)

## Existing vs Required

### RBAC
- Existing: `com`, `commune_agent`, `orpailleur`, `collecteur`, `bijoutier`, `comptoir_*`, `transporteur_agree`, `dgd`, `gue`.
- Missing before update: `com_admin`, `com_agent`, `mines_region_agent`, `lab_bgglm`, `douanes_agent`, `gue_or_agent`, `raffinerie_agent`, `transporteur`, `region_agent`, `district_agent`.
- Added now: roles above + OR card/compliance permissions.

### OR Workflows
- Existing: lot OR, transaction OR chain checks, exports checklist, transport, transformation, test certificates.
- Missing before update: Kara-bolamena card lifecycle, collector card lifecycle (pieces + max 5 communes), affiliation deadline blocking, comptoir license state machine, renewal reminders.
- Added now: Kara and collector card entities/endpoints, compliance reminders endpoint, affiliation blocking hooks.

### Data Model
- Existing: `actors`, `actor_roles`, `lots`, `transactions`, `fees`, `payment_requests`, `documents`, `audit_logs`, OR extension tables (`gold_ops`).
- Missing before update: card tables, tariff tables, affiliation/report tables, reminder notifications, fee split table 50/30/20.
- Added now:
  - `or_tariff_configs`
  - `kara_bolamena_cards`
  - `kara_production_logs`
  - `collector_cards`
  - `collector_card_documents`
  - `collector_affiliation_agreements`
  - `collector_registers`
  - `collector_semiannual_reports`
  - `comptoir_licenses`
  - `collector_card_fee_splits`
  - `compliance_notifications`

### UI
- Existing: login, dashboards, actors/lots/transactions/exports.
- Missing before update: dedicated OR compliance screens for cards/tariffs/reminders.
- Added now:
  - `OrCompliancePage` route `/or-compliance`
  - API hooks for card/tariff/reminder/licensing operations.

### Jobs / Background
- Existing: none for expiry reminders.
- Added now: reminder runner endpoint (`POST /api/v1/or-compliance/reminders/run`) and persistence table `compliance_notifications`.

### Controls and Audit
- Existing: audit on lots/transactions/payments/core flows.
- Missing before update: OR card validity blocking and affiliation-based laissez-passer blocking.
- Added now:
  - OR lot declaration blocked if missing valid Kara/collector card (role dependent).
  - OR transaction blocked if seller/buyer non-compliant.
  - Collector affiliation lateness updates `laissez_passer_access_status`.
  - Collector card payment split 50/30/20 on fee payment.
  - Reminder send events audited.
