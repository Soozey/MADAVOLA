-- PIERRE Workflow Extension (idempotent)
-- Adds sous-filiere/catalogue/authorizations/export controls/transformation/fee policy

CREATE TABLE IF NOT EXISTS product_catalog (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  nom VARCHAR(150) NOT NULL,
  famille VARCHAR(60) NOT NULL DEFAULT 'PIERRE',
  filiere VARCHAR(20) NOT NULL DEFAULT 'PIERRE',
  sous_filiere VARCHAR(30) NOT NULL,
  allowed_units_json TEXT NOT NULL DEFAULT '[]',
  required_attributes_json TEXT NOT NULL DEFAULT '[]',
  export_restricted INTEGER NOT NULL DEFAULT 0,
  export_rules_json TEXT NOT NULL DEFAULT '{}',
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE lots ADD COLUMN IF NOT EXISTS sous_filiere VARCHAR(30);
ALTER TABLE lots ADD COLUMN IF NOT EXISTS product_catalog_id INTEGER REFERENCES product_catalog(id);
ALTER TABLE lots ADD COLUMN IF NOT EXISTS attributes_json TEXT;

CREATE TABLE IF NOT EXISTS actor_authorizations (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER NOT NULL REFERENCES actors(id),
  filiere VARCHAR(20) NOT NULL DEFAULT 'PIERRE',
  authorization_type VARCHAR(40) NOT NULL,
  numero VARCHAR(120) NOT NULL UNIQUE,
  issued_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_actor_authorizations_actor_filiere_status
  ON actor_authorizations(actor_id, filiere, status);

CREATE TABLE IF NOT EXISTS fee_policies (
  id SERIAL PRIMARY KEY,
  code VARCHAR(80) NOT NULL UNIQUE,
  filiere VARCHAR(20) NOT NULL DEFAULT 'PIERRE',
  sous_filiere VARCHAR(30),
  commune_id INTEGER REFERENCES communes(id),
  role_code VARCHAR(60),
  fee_type VARCHAR(50) NOT NULL,
  amount NUMERIC(14,2) NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'MGA',
  legal_reference VARCHAR(255),
  legal_todo VARCHAR(255),
  effective_from TIMESTAMPTZ NOT NULL,
  effective_to TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS export_colis (
  id SERIAL PRIMARY KEY,
  export_dossier_id INTEGER NOT NULL REFERENCES export_dossiers(id),
  package_code VARCHAR(80) NOT NULL UNIQUE,
  gross_weight NUMERIC(14,4) NOT NULL,
  net_weight NUMERIC(14,4) NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS export_seals (
  id SERIAL PRIMARY KEY,
  export_dossier_id INTEGER NOT NULL REFERENCES export_dossiers(id),
  seal_number VARCHAR(120) NOT NULL UNIQUE,
  pv_document_id INTEGER REFERENCES documents(id),
  sealed_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  sealed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status VARCHAR(20) NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS export_validation_steps (
  id SERIAL PRIMARY KEY,
  export_dossier_id INTEGER NOT NULL REFERENCES export_dossiers(id),
  step_code VARCHAR(50) NOT NULL,
  validator_actor_id INTEGER NOT NULL REFERENCES actors(id),
  decision VARCHAR(20) NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pierre_transformation_events (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER NOT NULL REFERENCES actors(id),
  operation_type VARCHAR(40) NOT NULL,
  sous_filiere VARCHAR(30) NOT NULL,
  loss_ratio NUMERIC(10,6) NOT NULL DEFAULT 0,
  notes TEXT,
  document_id INTEGER REFERENCES documents(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pierre_transformation_links (
  id SERIAL PRIMARY KEY,
  transformation_event_id INTEGER NOT NULL REFERENCES pierre_transformation_events(id),
  lot_id INTEGER NOT NULL REFERENCES lots(id),
  link_type VARCHAR(10) NOT NULL,
  quantity NUMERIC(14,4) NOT NULL
);

-- Optional doc types for pierre controls/certification.
-- TODO LEGAL: map exact legal references when final text is validated.
