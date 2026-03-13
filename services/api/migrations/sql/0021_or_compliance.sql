-- OR Compliance Extension (L2023-007 / D2024-1345)
-- Idempotent migration script for PostgreSQL

CREATE TABLE IF NOT EXISTS or_tariff_configs (
  id SERIAL PRIMARY KEY,
  card_type VARCHAR(40) NOT NULL,
  commune_id INTEGER REFERENCES communes(id),
  amount NUMERIC(14,2) NOT NULL,
  min_amount NUMERIC(14,2),
  max_amount NUMERIC(14,2),
  effective_from TIMESTAMPTZ NOT NULL,
  effective_to TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  configured_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kara_bolamena_cards (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER NOT NULL REFERENCES actors(id),
  commune_id INTEGER NOT NULL REFERENCES communes(id),
  unique_identifier VARCHAR(80) NOT NULL UNIQUE,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  nationality VARCHAR(30) NOT NULL DEFAULT 'mg',
  cin VARCHAR(50) NOT NULL,
  residence_verified BOOLEAN NOT NULL DEFAULT FALSE,
  tax_compliant BOOLEAN NOT NULL DEFAULT FALSE,
  zone_allowed BOOLEAN NOT NULL DEFAULT TRUE,
  public_order_clear BOOLEAN NOT NULL DEFAULT TRUE,
  issued_by_actor_id INTEGER REFERENCES actors(id),
  issued_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  renewed_from_card_id INTEGER REFERENCES kara_bolamena_cards(id),
  fee_id INTEGER REFERENCES fees(id),
  carnet_mode VARCHAR(20) NOT NULL DEFAULT 'electronic',
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kara_production_logs (
  id SERIAL PRIMARY KEY,
  card_id INTEGER NOT NULL REFERENCES kara_bolamena_cards(id),
  log_date DATE NOT NULL,
  zone_name VARCHAR(120) NOT NULL,
  quantity_gram NUMERIC(14,4) NOT NULL,
  notes TEXT,
  submitted_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_cards (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER NOT NULL REFERENCES actors(id),
  issuing_commune_id INTEGER NOT NULL REFERENCES communes(id),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  issued_by_actor_id INTEGER REFERENCES actors(id),
  issued_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  renewed_from_card_id INTEGER REFERENCES collector_cards(id),
  fee_id INTEGER REFERENCES fees(id),
  affiliation_deadline_at TIMESTAMPTZ,
  affiliation_submitted_at TIMESTAMPTZ,
  laissez_passer_blocked_reason VARCHAR(120),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_card_documents (
  id SERIAL PRIMARY KEY,
  collector_card_id INTEGER NOT NULL REFERENCES collector_cards(id),
  doc_type VARCHAR(60) NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  status VARCHAR(20) NOT NULL DEFAULT 'missing',
  document_id INTEGER REFERENCES documents(id),
  verified_by_actor_id INTEGER REFERENCES actors(id),
  verified_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_affiliation_agreements (
  id SERIAL PRIMARY KEY,
  collector_card_id INTEGER NOT NULL REFERENCES collector_cards(id),
  affiliate_actor_id INTEGER NOT NULL REFERENCES actors(id),
  affiliate_type VARCHAR(30) NOT NULL,
  agreement_ref VARCHAR(120) NOT NULL,
  signed_at TIMESTAMPTZ NOT NULL,
  communicated_to_com_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'submitted',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_registers (
  id SERIAL PRIMARY KEY,
  collector_card_id INTEGER NOT NULL REFERENCES collector_cards(id),
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  register_payload_json TEXT NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_semiannual_reports (
  id SERIAL PRIMARY KEY,
  collector_card_id INTEGER NOT NULL REFERENCES collector_cards(id),
  period_label VARCHAR(20) NOT NULL,
  report_payload_json TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'submitted',
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comptoir_licenses (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER NOT NULL REFERENCES actors(id),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  issued_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  dtspm_status VARCHAR(20) NOT NULL DEFAULT 'ok',
  fx_repatriation_status VARCHAR(20) NOT NULL DEFAULT 'ok',
  access_sig_oc_suspended BOOLEAN NOT NULL DEFAULT FALSE,
  cahier_des_charges_ref VARCHAR(120),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collector_card_fee_splits (
  id SERIAL PRIMARY KEY,
  fee_id INTEGER NOT NULL REFERENCES fees(id),
  beneficiary_type VARCHAR(30) NOT NULL,
  beneficiary_ref VARCHAR(80) NOT NULL,
  ratio_percent NUMERIC(8,4) NOT NULL,
  amount NUMERIC(14,2) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'allocated',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_notifications (
  id SERIAL PRIMARY KEY,
  entity_type VARCHAR(40) NOT NULL,
  entity_id INTEGER NOT NULL,
  actor_id INTEGER NOT NULL REFERENCES actors(id),
  channel VARCHAR(20) NOT NULL DEFAULT 'in_app',
  days_before INTEGER NOT NULL,
  message VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'sent',
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
