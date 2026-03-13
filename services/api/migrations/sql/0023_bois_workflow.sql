-- BOIS Workflow Extension (idempotent)

CREATE TABLE IF NOT EXISTS essence_catalog (
  id SERIAL PRIMARY KEY,
  code_essence VARCHAR(40) NOT NULL UNIQUE,
  nom VARCHAR(150) NOT NULL,
  categorie VARCHAR(30) NOT NULL,
  export_autorise INTEGER NOT NULL DEFAULT 1,
  requires_cites INTEGER NOT NULL DEFAULT 0,
  rules_json TEXT NOT NULL DEFAULT '{}',
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE lots ADD COLUMN IF NOT EXISTS wood_essence_id INTEGER REFERENCES essence_catalog(id);
ALTER TABLE lots ADD COLUMN IF NOT EXISTS wood_form VARCHAR(40);
ALTER TABLE lots ADD COLUMN IF NOT EXISTS volume_m3 NUMERIC(14,4);

CREATE TABLE IF NOT EXISTS rule_policies (
  id SERIAL PRIMARY KEY,
  filiere VARCHAR(20) NOT NULL,
  operation VARCHAR(40) NOT NULL,
  category VARCHAR(40),
  code VARCHAR(80) NOT NULL UNIQUE,
  params_json TEXT NOT NULL DEFAULT '{}',
  reference_texte VARCHAR(255),
  legal_todo VARCHAR(255),
  effective_from TIMESTAMPTZ NOT NULL,
  effective_to TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checklist_policies (
  id SERIAL PRIMARY KEY,
  filiere VARCHAR(20) NOT NULL,
  operation VARCHAR(40) NOT NULL,
  category VARCHAR(40),
  required_doc_types_json TEXT NOT NULL DEFAULT '[]',
  reference_texte VARCHAR(255),
  legal_todo VARCHAR(255),
  effective_from TIMESTAMPTZ NOT NULL,
  effective_to TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transport_records (
  id SERIAL PRIMARY KEY,
  filiere VARCHAR(20) NOT NULL DEFAULT 'BOIS',
  transporter_actor_id INTEGER NOT NULL REFERENCES actors(id),
  origin VARCHAR(255) NOT NULL,
  destination VARCHAR(255) NOT NULL,
  vehicle_ref VARCHAR(120),
  depart_at TIMESTAMPTZ NOT NULL,
  arrivee_estimee_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'planned',
  qr_code VARCHAR(255) UNIQUE,
  notes TEXT,
  created_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transport_record_items (
  id SERIAL PRIMARY KEY,
  transport_record_id INTEGER NOT NULL REFERENCES transport_records(id),
  lot_id INTEGER NOT NULL REFERENCES lots(id),
  quantity NUMERIC(14,4) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_approvals (
  id SERIAL PRIMARY KEY,
  filiere VARCHAR(20) NOT NULL,
  workflow_type VARCHAR(50) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  decision_notes TEXT,
  reference_texte VARCHAR(255),
  legal_todo VARCHAR(255),
  requested_by_actor_id INTEGER NOT NULL REFERENCES actors(id),
  decided_by_actor_id INTEGER REFERENCES actors(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  decided_at TIMESTAMPTZ
);

-- TODO LEGAL: aligner reference_texte pour chaque policy/checklist selon textes bois applicables.
