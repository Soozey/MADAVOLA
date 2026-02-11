#!/usr/bin/env python3
"""
Script pour corriger l'utilisateur admin.
"""

import sys
sys.path.insert(0, "/app")

from datetime import datetime, timezone
from sqlalchemy import text
from app.db import SessionLocal
import bcrypt

ADMIN_EMAIL = "admin@madavola.mg"
ADMIN_PASSWORD = "admin123"

def fix_admin():
    db = SessionLocal()
    try:
        # Supprimer l'utilisateur existant
        db.execute(text("DELETE FROM actor_roles WHERE actor_id IN (SELECT id FROM actors WHERE email = :email)"), {"email": ADMIN_EMAIL})
        db.execute(text("DELETE FROM actor_auth WHERE actor_id IN (SELECT id FROM actors WHERE email = :email)"), {"email": ADMIN_EMAIL})
        db.execute(text("DELETE FROM actors WHERE email = :email"), {"email": ADMIN_EMAIL})
        db.commit()
        print("✅ Ancien utilisateur supprimé")
        
        # Récupérer les IDs de territoire
        result = db.execute(text("SELECT id, version_id FROM regions LIMIT 1")).first()
        if not result:
            print("❌ Aucune région trouvée")
            return False
        
        region_id, version_id = result[0], result[1]
        district_id = db.execute(text("SELECT id FROM districts WHERE region_id = :region_id LIMIT 1"), {"region_id": region_id}).scalar_one()
        commune_id = db.execute(text("SELECT id FROM communes WHERE district_id = :district_id LIMIT 1"), {"district_id": district_id}).scalar_one()
        
        # Créer l'acteur
        actor_id = db.execute(
            text("""
                INSERT INTO actors (type_personne, nom, prenoms, email, telephone, region_id, district_id, commune_id, territory_version_id, status, created_at)
                VALUES ('personne_physique', 'Administrateur', 'MADAVOLA', :email, '+261340000000', :region_id, :district_id, :commune_id, :version_id, 'active', :now)
                RETURNING id
            """),
            {"email": ADMIN_EMAIL, "region_id": region_id, "district_id": district_id, "commune_id": commune_id, "version_id": version_id, "now": datetime.now(timezone.utc)}
        ).scalar_one()
        
        # Créer le hash avec bcrypt directement (format compatible avec passlib)
        password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Passlib ajoute un préfixe $2b$ ou $2a$, mais bcrypt génère déjà $2b$
        # On doit utiliser le format passlib: $2b$ + reste
        # Le hash bcrypt est déjà au bon format
        
        db.execute(
            text("INSERT INTO actor_auth (actor_id, password_hash, is_active) VALUES (:actor_id, :password_hash, 1)"),
            {"actor_id": actor_id, "password_hash": password_hash}
        )
        
        db.execute(
            text("INSERT INTO actor_roles (actor_id, role, status, valid_from) VALUES (:actor_id, 'admin', 'active', :now)"),
            {"actor_id": actor_id, "now": datetime.now(timezone.utc)}
        )
        
        db.commit()
        print("✅ Utilisateur admin créé avec succès !")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Mot de passe: {ADMIN_PASSWORD}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_admin()
    sys.exit(0 if success else 1)
