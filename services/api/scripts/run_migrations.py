#!/usr/bin/env python3
"""Script pour exécuter les migrations Alembic"""
import sys
sys.path.insert(0, "/app")

from alembic.config import Config
from alembic import command

if __name__ == "__main__":
    alembic_cfg = Config("/app/alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations exécutées avec succès !")
