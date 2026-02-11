#!/usr/bin/env python3
"""
Script pour créer un utilisateur admin initial.
Usage: python scripts/create_admin.py
"""

import os
import sys
from datetime import datetime, timezone

# Ajouter la racine de l'API au path (Docker: /app, local: répertoire parent de scripts)
_api_root = os.environ.get("API_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

from app.auth.security import hash_password
from app.db import SessionLocal
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.territory import Commune, District, Region, TerritoryVersion

# Données par défaut pour l'admin
ADMIN_EMAIL = "admin@madavola.mg"
ADMIN_PHONE = "+261340000000"
ADMIN_PASSWORD = "admin123"  # À changer après la première connexion !
ADMIN_NAME = "Administrateur"
ADMIN_SURNAME = "MADAVOLA"


def create_admin_user():
    db = SessionLocal()
    try:
        # Vérifier si un admin existe déjà (en utilisant SQL direct pour éviter les problèmes de relations)
        from sqlalchemy import text
        result = db.execute(
            text("SELECT id FROM actors WHERE email = :email"), {"email": ADMIN_EMAIL}
        ).first()
        if result:
            print(f"[ERREUR] Un utilisateur avec l'email {ADMIN_EMAIL} existe deja (ID: {result[0]})")
            return False

        # Vérifier/créer un territoire par défaut si nécessaire
        # Chercher une région existante (en utilisant SQL direct)
        from sqlalchemy import text
        region_result = db.execute(text("SELECT id, version_id FROM regions LIMIT 1")).first()
        if not region_result:
            print("ATTENTION Aucune region trouvee. Creation d'un territoire par defaut...")
            # Créer une version de territoire par défaut
            now = datetime.now(timezone.utc)
            version_result = db.execute(
                text("""
                    INSERT INTO territory_versions (version_tag, source_filename, checksum_sha256, status, imported_at)
                    VALUES ('default', 'manual', 'default', 'active', :now)
                    RETURNING id
                """),
                {"now": now}
            ).first()
            version_id = version_result[0]

            # Créer une région par défaut
            region_result = db.execute(
                text("""
                    INSERT INTO regions (version_id, code, name, name_normalized)
                    VALUES (:version_id, 'DEFAULT', 'Région par défaut', 'region par defaut')
                    RETURNING id
                """),
                {"version_id": version_id}
            ).first()
            region_id = region_result[0]

            # Créer un district par défaut
            district_result = db.execute(
                text("""
                    INSERT INTO districts (version_id, region_id, code, name, name_normalized)
                    VALUES (:version_id, :region_id, 'DEFAULT', 'District par défaut', 'district par defaut')
                    RETURNING id
                """),
                {"version_id": version_id, "region_id": region_id}
            ).first()
            district_id = district_result[0]

            # Créer une commune par défaut
            commune_result = db.execute(
                text("""
                    INSERT INTO communes (version_id, district_id, code, name, name_normalized)
                    VALUES (:version_id, :district_id, 'DEFAULT', 'Commune par défaut', 'commune par defaut')
                    RETURNING id
                """),
                {"version_id": version_id, "district_id": district_id}
            ).first()
            commune_id = commune_result[0]
        else:
            # Utiliser le premier territoire trouvé
            region_id, version_id = region_result[0], region_result[1]
            district_result = db.execute(
                text("SELECT id FROM districts WHERE region_id = :region_id LIMIT 1"),
                {"region_id": region_id}
            ).first()
            if not district_result:
                print("[ERREUR] Aucun district trouve pour la region")
                return False
            district_id = district_result[0]
            
            commune_result = db.execute(
                text("SELECT id FROM communes WHERE district_id = :district_id LIMIT 1"),
                {"district_id": district_id}
            ).first()
            if not commune_result:
                print("[ERREUR] Aucune commune trouvee pour le district")
                return False
            commune_id = commune_result[0]

        # Créer l'acteur admin (en utilisant SQL direct)
        try:
            password_hash = hash_password(ADMIN_PASSWORD)
        except Exception as e:
            print(f"ATTENTION Erreur lors du hashage du mot de passe: {e}")
            # Utiliser bcrypt directement
            import bcrypt
            password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        now = datetime.now(timezone.utc)
        
        actor_result = db.execute(
            text("""
                INSERT INTO actors (type_personne, nom, prenoms, email, telephone, region_id, district_id, commune_id, territory_version_id, status, created_at)
                VALUES ('personne_physique', :nom, :prenoms, :email, :telephone, :region_id, :district_id, :commune_id, :version_id, 'active', :now)
                RETURNING id
            """),
            {
                "nom": ADMIN_NAME,
                "prenoms": ADMIN_SURNAME,
                "email": ADMIN_EMAIL,
                "telephone": ADMIN_PHONE,
                "region_id": region_id,
                "district_id": district_id,
                "commune_id": commune_id,
                "version_id": version_id,
                "now": now
            }
        ).first()
        actor_id = actor_result[0]

        # Créer l'authentification
        db.execute(
            text("""
                INSERT INTO actor_auth (actor_id, password_hash, is_active)
                VALUES (:actor_id, :password_hash, 1)
            """),
            {"actor_id": actor_id, "password_hash": password_hash}
        )

        # Créer le rôle admin
        db.execute(
            text("""
                INSERT INTO actor_roles (actor_id, role, status, valid_from)
                VALUES (:actor_id, 'admin', 'active', :now)
            """),
            {"actor_id": actor_id, "now": now}
        )

        db.commit()
        print("OK Utilisateur admin cree avec succes !")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Telephone: {ADMIN_PHONE}")
        print(f"   Mot de passe: {ADMIN_PASSWORD}")
        print("   IMPORTANT: Changez le mot de passe apres la premiere connexion !")
        return True

    except Exception as e:
        db.rollback()
        print(f"[ERREUR] Erreur lors de la creation de l'admin: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)
