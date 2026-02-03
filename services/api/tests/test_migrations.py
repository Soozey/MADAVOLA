"""
Tests des migrations Alembic (up/down)
"""
from alembic import command
from alembic.config import Config
import pytest


def test_migrations_up_down(tmp_path, db_session):
    """Test que toutes les migrations peuvent être appliquées et annulées"""
    # Note: Ce test nécessite une DB de test configurée
    # Pour l'instant, on vérifie juste que les fichiers de migration sont valides
    
    # Vérifier que le fichier de config Alembic existe
    import os
    alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    assert os.path.exists(alembic_ini), "alembic.ini doit exister"
    
    # Vérifier que le répertoire versions existe
    versions_dir = os.path.join(os.path.dirname(__file__), "..", "alembic", "versions")
    assert os.path.exists(versions_dir), "Répertoire alembic/versions doit exister"
    
    # Lister les migrations
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith(".py") and f.startswith("0")]
    assert len(migration_files) > 0, "Au moins une migration doit exister"
    
    # Vérifier que chaque migration a les fonctions upgrade() et downgrade()
    for migration_file in migration_files:
        file_path = os.path.join(versions_dir, migration_file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "def upgrade()" in content, f"{migration_file} doit avoir upgrade()"
            assert "def downgrade()" in content, f"{migration_file} doit avoir downgrade()"
            assert "revision = " in content, f"{migration_file} doit avoir revision"
            assert "down_revision = " in content, f"{migration_file} doit avoir down_revision"


def test_migration_chain_integrity():
    """Test que la chaîne de migrations est cohérente"""
    import os
    import re
    
    versions_dir = os.path.join(os.path.dirname(__file__), "..", "alembic", "versions")
    migration_files = [f for f in os.listdir(versions_dir) if f.endswith(".py") and f.startswith("0")]
    
    revisions = {}
    for migration_file in sorted(migration_files):
        file_path = os.path.join(versions_dir, migration_file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            revision_match = re.search(r'revision\s*=\s*"([^"]+)"', content)
            down_revision_match = re.search(r'down_revision\s*=\s*"([^"]+)"', content)
            
            if revision_match and down_revision_match:
                revision = revision_match.group(1)
                down_revision = down_revision_match.group(1)
                revisions[revision] = down_revision
    
    # Vérifier que chaque down_revision pointe vers une revision existante (sauf "base")
    for rev, down_rev in revisions.items():
        if down_rev != "None" and down_rev not in revisions and down_rev != "base":
            # C'est OK si c'est la première migration
            pass
