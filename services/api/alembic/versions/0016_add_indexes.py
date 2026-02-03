from alembic import op

revision = "0016_add_indexes"
down_revision = "0015_admin_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Actors indexes
    op.create_index("ix_actors_commune_id", "actors", ["commune_id"])
    op.create_index("ix_actors_status", "actors", ["status"])
    op.create_index("ix_actors_region_id", "actors", ["region_id"])
    op.create_index("ix_actors_district_id", "actors", ["district_id"])
    
    # Actor roles indexes (critical for RBAC checks)
    op.create_index("ix_actor_roles_actor_id_status", "actor_roles", ["actor_id", "status"])
    op.create_index("ix_actor_roles_role", "actor_roles", ["role"])
    
    # Inventory ledger indexes (used in reports and queries)
    op.create_index("ix_inventory_ledger_actor_id", "inventory_ledger", ["actor_id"])
    op.create_index("ix_inventory_ledger_lot_id", "inventory_ledger", ["lot_id"])
    op.create_index("ix_inventory_ledger_created_at", "inventory_ledger", ["created_at"])
    op.create_index("ix_inventory_ledger_movement_type", "inventory_ledger", ["movement_type"])
    op.create_index("ix_inventory_ledger_actor_created", "inventory_ledger", ["actor_id", "created_at"])
    
    # Trade transactions indexes
    op.create_index("ix_trade_transactions_seller_actor_id", "trade_transactions", ["seller_actor_id"])
    op.create_index("ix_trade_transactions_buyer_actor_id", "trade_transactions", ["buyer_actor_id"])
    op.create_index("ix_trade_transactions_status", "trade_transactions", ["status"])
    op.create_index("ix_trade_transactions_created_at", "trade_transactions", ["created_at"])
    op.create_index("ix_trade_transactions_seller_created", "trade_transactions", ["seller_actor_id", "created_at"])
    
    # Documents indexes
    op.create_index("ix_documents_owner_actor_id", "documents", ["owner_actor_id"])
    op.create_index("ix_documents_related_entity", "documents", ["related_entity_type", "related_entity_id"])
    op.create_index("ix_documents_doc_type", "documents", ["doc_type"])
    
    # Lots indexes
    op.create_index("ix_lots_current_owner_actor_id", "lots", ["current_owner_actor_id"])
    op.create_index("ix_lots_declared_by_actor_id", "lots", ["declared_by_actor_id"])
    op.create_index("ix_lots_status", "lots", ["status"])
    
    # Payments indexes
    op.create_index("ix_payment_requests_payer_actor_id", "payment_requests", ["payer_actor_id"])
    op.create_index("ix_payment_requests_status", "payment_requests", ["status"])
    op.create_index("ix_payment_requests_external_ref", "payment_requests", ["external_ref"])
    
    # Refresh tokens indexes
    op.create_index("ix_refresh_tokens_actor_id", "refresh_tokens", ["actor_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    
    # Export dossiers indexes
    op.create_index("ix_export_dossiers_created_by_actor_id", "export_dossiers", ["created_by_actor_id"])
    op.create_index("ix_export_dossiers_status", "export_dossiers", ["status"])
    op.create_index("ix_export_dossiers_created_at", "export_dossiers", ["created_at"])
    
    # Audit logs indexes
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", "audit_logs")
    op.drop_index("ix_audit_logs_entity", "audit_logs")
    op.drop_index("ix_audit_logs_actor_id", "audit_logs")
    op.drop_index("ix_export_dossiers_created_at", "export_dossiers")
    op.drop_index("ix_export_dossiers_status", "export_dossiers")
    op.drop_index("ix_export_dossiers_created_by_actor_id", "export_dossiers")
    op.drop_index("ix_refresh_tokens_expires_at", "refresh_tokens")
    op.drop_index("ix_refresh_tokens_actor_id", "refresh_tokens")
    op.drop_index("ix_payment_requests_external_ref", "payment_requests")
    op.drop_index("ix_payment_requests_status", "payment_requests")
    op.drop_index("ix_payment_requests_payer_actor_id", "payment_requests")
    op.drop_index("ix_lots_status", "lots")
    op.drop_index("ix_lots_declared_by_actor_id", "lots")
    op.drop_index("ix_lots_current_owner_actor_id", "lots")
    op.drop_index("ix_documents_doc_type", "documents")
    op.drop_index("ix_documents_related_entity", "documents")
    op.drop_index("ix_documents_owner_actor_id", "documents")
    op.drop_index("ix_trade_transactions_seller_created", "trade_transactions")
    op.drop_index("ix_trade_transactions_created_at", "trade_transactions")
    op.drop_index("ix_trade_transactions_status", "trade_transactions")
    op.drop_index("ix_trade_transactions_buyer_actor_id", "trade_transactions")
    op.drop_index("ix_trade_transactions_seller_actor_id", "trade_transactions")
    op.drop_index("ix_inventory_ledger_actor_created", "inventory_ledger")
    op.drop_index("ix_inventory_ledger_movement_type", "inventory_ledger")
    op.drop_index("ix_inventory_ledger_created_at", "inventory_ledger")
    op.drop_index("ix_inventory_ledger_lot_id", "inventory_ledger")
    op.drop_index("ix_inventory_ledger_actor_id", "inventory_ledger")
    op.drop_index("ix_actor_roles_role", "actor_roles")
    op.drop_index("ix_actor_roles_actor_id_status", "actor_roles")
    op.drop_index("ix_actors_district_id", "actors")
    op.drop_index("ix_actors_region_id", "actors")
    op.drop_index("ix_actors_status", "actors")
    op.drop_index("ix_actors_commune_id", "actors")
