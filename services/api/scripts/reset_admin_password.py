#!/usr/bin/env python3
"""
Réinitialise le mot de passe de l'admin (admin@madavola.mg) à admin123.
À utiliser si la connexion affiche "Identifiant ou mot de passe incorrect".
Usage (dans le conteneur): python scripts/reset_admin_password.py
"""

import os
import sys

_api_root = os.environ.get("API_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

from sqlalchemy import text

from app.auth.security import hash_password, verify_password
from app.db import SessionLocal

ADMIN_EMAIL = "admin@madavola.mg"
NEW_PASSWORD = "admin123"


def reset_admin_password():
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT a.id, a.email, aa.password_hash FROM actors a JOIN actor_auth aa ON aa.actor_id = a.id WHERE a.email = :email"),
            {"email": ADMIN_EMAIL},
        ).first()
        if not row:
            print(f"[ERREUR] Aucun utilisateur avec l'email {ADMIN_EMAIL} trouve. Creez d'abord l'admin avec create_admin.py")
            return False
        actor_id, email, old_hash = row
        new_hash = hash_password(NEW_PASSWORD)
        db.execute(
            text("UPDATE actor_auth SET password_hash = :hash WHERE actor_id = :actor_id"),
            {"hash": new_hash, "actor_id": actor_id},
        )
        db.commit()
        if verify_password(NEW_PASSWORD, new_hash):
            print("OK Mot de passe admin reinitialise avec succes.")
            print(f"   Email: {ADMIN_EMAIL}")
            print(f"   Nouveau mot de passe: {NEW_PASSWORD}")
            return True
        print("ATTENTION Le hash a ete mis a jour mais la verification a echoue. Reessayez la connexion.")
        return True
    except Exception as e:
        db.rollback()
        msg = str(e).encode("ascii", errors="replace").decode("ascii")
        print(f"[ERREUR] {msg}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = reset_admin_password()
    sys.exit(0 if success else 1)
