from datetime import datetime, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, RefreshToken


def _create_actor(db_session, status="active"):
    actor = Actor(
        type_personne="physique",
        nom="Test",
        prenoms="User",
        telephone="0340000000",
        email="test@example.com",
        status=status,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(
        ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1)
    )
    db_session.commit()
    return actor


def test_login_and_me(client, db_session):
    actor = _create_actor(db_session)
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test@example.com", "password": "secret"},
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == actor.id
    assert "roles" in me.json()


def test_refresh_and_logout(client, db_session):
    _create_actor(db_session)
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "test@example.com", "password": "secret"},
    )
    tokens = response.json()

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]})
    assert logout.status_code == 200

    stored = db_session.query(RefreshToken).filter_by(actor_id=1).all()
    assert any(t.revoked_at is not None for t in stored)
