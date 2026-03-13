# Audit Branching API ? UI

## Resume
- Endpoints API detectes (OpenAPI): **143**
- Endpoints API normalises: **143**
- Endpoints consommes par Front (web+mobile): **144**
- Endpoints API sans usage Front: **0**

## API endpoints ? UI screens
| Method | Endpoint | Statut | Evidence UI |
|---|---|---|---|
| `GET` | `/actors` | **OK** | mobile:/actors; web:/actors |
| `POST` | `/actors` | **OK** | mobile:/actors; web:/actors |
| `GET` | `/actors/{}` | **OK** | web:/actors/${actorId} |
| `GET` | `/actors/{}/authorizations` | **OK** | web:/actors/${actorId}/authorizations |
| `POST` | `/actors/{}/authorizations` | **OK** | web:/actors/${actorId}/authorizations |
| `GET` | `/actors/{}/roles` | **OK** | web:/actors/${actorId}/roles |
| `PATCH` | `/actors/{}/status` | **OK** | web:/actors/${actorId}/status |
| `GET` | `/admin/actors/{}/roles` | **OK** | web:/admin/actors/${actorId}/roles |
| `POST` | `/admin/actors/{}/roles` | **OK** | web:/admin/actors/${actorId}/roles |
| `GET` | `/admin/config` | **OK** | web:/admin/config |
| `POST` | `/admin/config` | **OK** | web:/admin/config |
| `DELETE` | `/admin/config/{}` | **OK** | web:/admin/config/${configId} |
| `GET` | `/admin/config/{}` | **OK** | web:/admin/config/${configId} |
| `PATCH` | `/admin/config/{}` | **OK** | web:/admin/config/${configId} |
| `DELETE` | `/admin/roles/{}` | **OK** | web:/admin/roles/${roleId} |
| `PATCH` | `/admin/roles/{}` | **OK** | web:/admin/roles/${roleId} |
| `GET` | `/approvals` | **OK** | web:/approvals |
| `POST` | `/approvals` | **OK** | web:/approvals |
| `POST` | `/approvals/{}/decide` | **OK** | web:/approvals/${approvalId}/decide |
| `GET` | `/audit` | **OK** | web:/audit |
| `GET` | `/audit/stock-coherence` | **OK** | web:/audit/stock-coherence |
| `POST` | `/auth/login` | **OK** | mobile:/auth/login; web:/auth/login |
| `POST` | `/auth/logout` | **OK** | web:/auth/logout |
| `GET` | `/auth/me` | **OK** | mobile:/auth/me; web:/auth/me |
| `POST` | `/auth/refresh` | **OK** | web:/auth/refresh |
| `GET` | `/catalog/essences` | **OK** | mobile:/catalog/essences; web:/catalog/essences |
| `POST` | `/catalog/essences` | **OK** | web:/catalog/essences |
| `DELETE` | `/catalog/essences/{}` | **OK** | web:/catalog/essences/${essenceId} |
| `PUT` | `/catalog/essences/{}` | **OK** | web:/catalog/essences/${essenceId} |
| `GET` | `/catalog/products` | **OK** | mobile:/catalog/products; web:/catalog/products |
| `POST` | `/catalog/products` | **OK** | web:/catalog/products |
| `DELETE` | `/catalog/products/{}` | **OK** | web:/catalog/products/${productId} |
| `PUT` | `/catalog/products/{}` | **OK** | web:/catalog/products/${productId} |
| `GET` | `/dashboards/commune` | **OK** | web:/dashboards/commune |
| `GET` | `/dashboards/national` | **OK** | web:/dashboards/national |
| `GET` | `/dashboards/regional` | **OK** | web:/dashboards/regional |
| `GET` | `/documents` | **OK** | web:/documents |
| `POST` | `/documents` | **OK** | web:/documents |
| `GET` | `/documents/{}` | **OK** | web:/documents/${documentId} |
| `GET` | `/exports` | **OK** | web:/exports |
| `POST` | `/exports` | **OK** | mobile:/exports; web:/exports |
| `GET` | `/exports/{}` | **OK** | web:/exports/${exportId} |
| `POST` | `/exports/{}/lots` | **OK** | mobile:/exports/${Number(exportForm.export_id)}/lots; web:/exports/${exportId}/lots |
| `PATCH` | `/exports/{}/status` | **OK** | web:/exports/${exportId}/status |
| `POST` | `/exports/{}/submit` | **OK** | mobile:/exports/${Number(exportForm.export_id)}/submit; web:/exports/${exportId}/submit |
| `POST` | `/exports/{}/validate` | **OK** | mobile:/exports/${Number(exportForm.export_id)}/validate; web:/exports/${exportId}/validate |
| `GET` | `/fees` | **OK** | web:/fees |
| `POST` | `/fees` | **OK** | web:/fees |
| `GET` | `/fees/{}` | **OK** | web:/fees/${feeId} |
| `POST` | `/fees/{}/initiate-payment` | **OK** | web:/fees/${feeId}/initiate-payment |
| `PATCH` | `/fees/{}/status` | **OK** | web:/fees/${feeId}/status |
| `POST` | `/geo-points` | **OK** | mobile:/geo-points; web:/geo-points |
| `GET` | `/geo-points/{}` | **OK** | web:/geo-points/${geoPointId} |
| `GET` | `/health` | **OK** | web:/health |
| `GET` | `/inspections` | **OK** | web:/inspections |
| `POST` | `/inspections` | **OK** | web:/inspections |
| `GET` | `/invoices` | **OK** | web:/invoices |
| `GET` | `/invoices/{}` | **OK** | web:/invoices/${invoiceId} |
| `GET` | `/ledger` | **OK** | web:/ledger |
| `GET` | `/ledger/balance` | **OK** | web:/ledger/balance |
| `GET` | `/lots` | **OK** | mobile:/lots; web:/lots |
| `POST` | `/lots` | **OK** | mobile:/lots; web:/lots |
| `POST` | `/lots/consolidate` | **OK** | web:/lots/consolidate |
| `GET` | `/lots/{}` | **OK** | web:/lots/${lotId} |
| `POST` | `/lots/{}/split` | **OK** | web:/lots/${lotId}/split |
| `POST` | `/lots/{}/transfer` | **OK** | web:/lots/${lotId}/transfer |
| `GET` | `/notifications` | **OK** | mobile:/notifications; web:/notifications |
| `POST` | `/notifications/run-expiry-reminders` | **OK** | mobile:/notifications/run-expiry-reminders?thresholds=30,7,1; web:/notifications/run-expiry-reminders?thresholds=${encodeURIComponent(thresholds)} |
| `POST` | `/or-compliance/collector-affiliations` | **OK** | web:/or-compliance/collector-affiliations |
| `GET` | `/or-compliance/collector-cards` | **OK** | web:/or-compliance/collector-cards |
| `POST` | `/or-compliance/collector-cards` | **OK** | web:/or-compliance/collector-cards |
| `PATCH` | `/or-compliance/collector-cards/{}/decision` | **OK** | web:/or-compliance/collector-cards/${cardId}/decision |
| `POST` | `/or-compliance/collector-cards/{}/documents` | **OK** | web:/or-compliance/collector-cards/${cardId}/documents |
| `POST` | `/or-compliance/collector-cards/{}/semiannual-reports` | **OK** | web:/or-compliance/collector-cards/${cardId}/semiannual-reports?period_label=${encodeURIComponent(data.period_label)}&report_payload_json=${encodeURIComponent(data.report_payload_json)} |
| `POST` | `/or-compliance/collector-cards/{}/verify-document` | **OK** | web:/or-compliance/collector-cards/${cardId}/verify-document |
| `POST` | `/or-compliance/comptoir-licenses` | **OK** | web:/or-compliance/comptoir-licenses |
| `PATCH` | `/or-compliance/comptoir-licenses/{}` | **OK** | web:/or-compliance/comptoir-licenses/${licenseId} |
| `GET` | `/or-compliance/kara-cards` | **OK** | web:/or-compliance/kara-cards |
| `POST` | `/or-compliance/kara-cards` | **OK** | web:/or-compliance/kara-cards |
| `PATCH` | `/or-compliance/kara-cards/{}/decision` | **OK** | web:/or-compliance/kara-cards/${cardId}/decision |
| `POST` | `/or-compliance/kara-production-logs` | **OK** | web:/or-compliance/kara-production-logs |
| `GET` | `/or-compliance/notifications` | **OK** | web:/or-compliance/notifications |
| `POST` | `/or-compliance/reminders/run` | **OK** | web:/or-compliance/reminders/run?thresholds=${encodeURIComponent(thresholds)} |
| `GET` | `/or-compliance/tariffs` | **OK** | web:/or-compliance/tariffs |
| `POST` | `/or-compliance/tariffs` | **OK** | web:/or-compliance/tariffs |
| `POST` | `/or/export-validations` | **OK** | web:/or/export-validations |
| `GET` | `/or/exports/{}/checklist` | **OK** | web:/or/exports/${exportId}/checklist |
| `POST` | `/or/exports/{}/checklist/verify` | **OK** | web:/or/exports/${exportId}/checklist/verify |
| `POST` | `/or/forex-repatriations` | **OK** | web:/or/forex-repatriations |
| `POST` | `/or/legal-versions` | **OK** | web:/or/legal-versions |
| `GET` | `/or/legal-versions/active` | **OK** | web:/or/legal-versions/active |
| `POST` | `/or/test-certificates` | **OK** | web:/or/test-certificates |
| `POST` | `/or/transformation-events` | **OK** | web:/or/transformation-events |
| `POST` | `/or/transformation-facilities` | **OK** | web:/or/transformation-facilities |
| `POST` | `/or/transport-events` | **OK** | web:/or/transport-events |
| `PATCH` | `/or/transport-events/{}/arrival` | **OK** | web:/or/transport-events/${eventId}/arrival |
| `GET` | `/payment-providers` | **OK** | web:/payment-providers |
| `POST` | `/payment-providers` | **OK** | web:/payment-providers |
| `PATCH` | `/payment-providers/{}` | **OK** | web:/payment-providers/${providerId} |
| `GET` | `/payments` | **OK** | web:/payments |
| `POST` | `/payments/initiate` | **OK** | web:/payments/initiate |
| `GET` | `/payments/status/{}` | **OK** | web:/payments/status/${encodeURIComponent(externalRef)} |
| `POST` | `/payments/webhooks/{}` | **OK** | web:/payments/webhooks/${providerCode} |
| `GET` | `/payments/{}` | **OK** | web:/payments/${paymentId} |
| `GET` | `/penalties` | **OK** | web:/penalties |
| `POST` | `/penalties` | **OK** | web:/penalties |
| `GET` | `/rbac/filieres` | **OK** | web:/rbac/filieres |
| `GET` | `/rbac/permissions` | **OK** | web:/rbac/permissions |
| `GET` | `/rbac/roles` | **OK** | mobile:/rbac/roles; web:/rbac/roles |
| `GET` | `/rbac/roles-with-permission` | **OK** | web:/rbac/roles-with-permission |
| `GET` | `/ready` | **OK** | web:/ready |
| `GET` | `/reports/actor` | **OK** | web:/reports/actor |
| `GET` | `/reports/commune` | **OK** | web:/reports/commune |
| `GET` | `/reports/national` | **OK** | web:/reports/national |
| `GET` | `/roles/referential` | **OK** | web:/roles/referential |
| `GET` | `/taxes` | **OK** | web:/taxes |
| `GET` | `/taxes/dtspm/breakdown` | **OK** | web:/taxes/dtspm/breakdown |
| `POST` | `/taxes/events` | **OK** | web:/taxes/events |
| `PATCH` | `/taxes/{}/status` | **OK** | web:/taxes/${taxId}/status |
| `GET` | `/territories/active` | **OK** | web:/territories/active |
| `GET` | `/territories/communes` | **OK** | web:/territories/communes |
| `GET` | `/territories/districts` | **OK** | web:/territories/districts |
| `GET` | `/territories/fokontany` | **OK** | web:/territories/fokontany |
| `POST` | `/territories/import` | **OK** | web:/territories/import?version_tag=${encodeURIComponent(versionTag)} |
| `GET` | `/territories/regions` | **OK** | web:/territories/regions |
| `GET` | `/territories/versions` | **OK** | web:/territories/versions |
| `GET` | `/territories/versions/{}` | **OK** | web:/territories/versions/${encodeURIComponent(versionTag)} |
| `POST` | `/trades` | **OK** | mobile:/trades; web:/trades |
| `POST` | `/trades/{}/confirm` | **OK** | mobile:/trades/${Number(tradeForm.trade_id)}/confirm; web:/trades/${tradeId}/confirm |
| `POST` | `/trades/{}/pay` | **OK** | mobile:/trades/${Number(tradeForm.trade_id)}/pay; web:/trades/${tradeId}/pay |
| `GET` | `/transactions` | **OK** | web:/transactions |
| `POST` | `/transactions` | **OK** | web:/transactions |
| `GET` | `/transactions/{}` | **OK** | web:/transactions/${transactionId} |
| `POST` | `/transactions/{}/initiate-payment` | **OK** | web:/transactions/${transactionId}/initiate-payment |
| `GET` | `/transactions/{}/payments` | **OK** | web:/transactions/${transactionId}/payments |
| `POST` | `/transformations` | **OK** | mobile:/transformations; web:/transformations |
| `POST` | `/transports` | **OK** | mobile:/transports; web:/transports |
| `POST` | `/transports/{}/scan_verify` | **OK** | mobile:/transports/${Number(transportForm.transport_id)}/scan_verify; web:/transports/${transportId}/scan_verify |
| `GET` | `/verify/actor/{}` | **OK** | web:/verify/actor/${actorId} |
| `GET` | `/verify/invoice/{}` | **OK** | mobile:/verify/invoice/${encodeURIComponent(verifyValue)}; web:/verify/invoice/${invoiceRef} |
| `GET` | `/verify/lot/{}` | **OK** | web:/verify/lot/${lotId} |
| `GET` | `/violations` | **OK** | web:/violations |
| `POST` | `/violations` | **OK** | web:/violations |

## Top 10 incoherences detectees
