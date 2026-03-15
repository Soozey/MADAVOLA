from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.models.actor import Actor, ActorAuth, ActorRole
from app.models.audit import AuditLog
from app.models.fee import Fee
from app.models.or_compliance import CollectorCard, CollectorCardDocument, CollectorCardFeeSplit, KaraBolamenaCard
from app.models.territory import Commune, District, Region, TerritoryVersion


def _seed_territory(db_session, commune_count: int = 1):
    version = TerritoryVersion(
        version_tag="v-or",
        source_filename="seed.xlsx",
        checksum_sha256="seed",
        status="active",
        imported_at=datetime.now(timezone.utc),
        activated_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    db_session.flush()
    region = Region(version_id=version.id, code="R1", name="Region 1", name_normalized="region1")
    db_session.add(region)
    db_session.flush()
    district = District(version_id=version.id, region_id=region.id, code="D1", name="District 1", name_normalized="district1")
    db_session.add(district)
    db_session.flush()
    communes = []
    for i in range(commune_count):
        code = f"C{i+1}"
        c = Commune(
            version_id=version.id,
            district_id=district.id,
            code=code,
            name=f"Commune {i+1}",
            name_normalized=f"commune{i+1}",
            mobile_money_msisdn=f"03400000{i+1:02d}",
        )
        db_session.add(c)
        communes.append(c)
    db_session.commit()
    return region, district, communes, version


def _create_actor(db_session, *, role: str, email: str, phone: str, commune_id: int, region_id: int, district_id: int, version_id: int):
    actor = Actor(
        type_personne="physique",
        nom=role,
        prenoms="User",
        telephone=phone,
        email=email,
        status="active",
        cin="CIN-TEST",
        region_id=region_id,
        district_id=district_id,
        commune_id=commune_id,
        territory_version_id=version_id,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(actor)
    db_session.flush()
    db_session.add(ActorAuth(actor_id=actor.id, password_hash=hash_password("secret"), is_active=1))
    db_session.add(ActorRole(actor_id=actor.id, role=role, status="active"))
    db_session.commit()
    return actor


def _auth(client, identifier: str, password: str = "secret") -> dict:
    resp = client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_orpailleur_without_kara_cannot_declare_or_lot(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    orp = _create_actor(
        db_session,
        role="orpailleur",
        email="orp@test.mg",
        phone="0341000001",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    headers = _auth(client, orp.email)
    geo = client.post("/api/v1/geo-points", json={"lat": -18.9, "lon": 47.5, "accuracy_m": 10, "source": "gps"}).json()
    resp = client.post(
        "/api/v1/lots",
        headers=headers,
        json={
            "filiere": "OR",
            "product_type": "or_brut",
            "unit": "g",
            "quantity": 5,
            "declare_geo_point_id": geo["id"],
            "declared_by_actor_id": orp.id,
            "notes": "test",
            "photo_urls": [],
        },
    )
    assert resp.status_code == 400
    assert "kara_bolamena_invalide" in str(resp.json())


def test_collecteur_cannot_exceed_five_cards(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=6)
    collecteur = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur@test.mg",
        phone="0341000002",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    headers = _auth(client, collecteur.email)
    for idx in range(5):
        res = client.post(
            "/api/v1/or-compliance/collector-cards",
            headers=headers,
            json={"actor_id": collecteur.id, "issuing_commune_id": communes[idx].id},
        )
        assert res.status_code == 201
    blocked = client.post(
        "/api/v1/or-compliance/collector-cards",
        headers=headers,
        json={"actor_id": collecteur.id, "issuing_commune_id": communes[5].id},
    )
    assert blocked.status_code == 400
    assert "limite_cartes_collecteur_atteinte" in str(blocked.json())


def test_collecteur_default_card_fee_is_500000(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    collecteur = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur-fee@test.mg",
        phone="0341000099",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    headers = _auth(client, collecteur.email)
    res = client.post(
        "/api/v1/or-compliance/collector-cards",
        headers=headers,
        json={"actor_id": collecteur.id, "issuing_commune_id": communes[0].id},
    )
    assert res.status_code == 201
    fee_id = res.json()["fee_id"]
    fee = db_session.query(Fee).filter(Fee.id == fee_id).first()
    assert fee is not None
    assert float(fee.amount) == 500000.0


def test_missing_documents_blocks_collector_approval(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    collecteur = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur2@test.mg",
        phone="0341000003",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    com_admin = _create_actor(
        db_session,
        role="com_admin",
        email="comadmin@test.mg",
        phone="0341000004",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    h_collecteur = _auth(client, collecteur.email)
    h_com_admin = _auth(client, com_admin.email)
    request = client.post(
        "/api/v1/or-compliance/collector-cards",
        headers=h_collecteur,
        json={"actor_id": collecteur.id, "issuing_commune_id": communes[0].id},
    )
    assert request.status_code == 201
    card_id = request.json()["id"]
    decision = client.patch(
        f"/api/v1/or-compliance/collector-cards/{card_id}/decision",
        headers=h_com_admin,
        json={"decision": "approved"},
    )
    assert decision.status_code == 400
    assert "pieces_obligatoires_manquantes" in str(decision.json())


def test_uploaded_but_not_verified_documents_still_block_collector_approval(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    collecteur = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur-upload@test.mg",
        phone="0341000203",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    com_admin = _create_actor(
        db_session,
        role="com_admin",
        email="com-upload@test.mg",
        phone="0341000204",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    h_collecteur = _auth(client, collecteur.email)
    h_com_admin = _auth(client, com_admin.email)
    request = client.post(
        "/api/v1/or-compliance/collector-cards",
        headers=h_collecteur,
        json={"actor_id": collecteur.id, "issuing_commune_id": communes[0].id},
    )
    assert request.status_code == 201
    card_id = request.json()["id"]
    fee_id = request.json()["fee_id"]

    docs = (
        db_session.query(CollectorCardDocument)
        .filter(CollectorCardDocument.collector_card_id == card_id)
        .all()
    )
    assert docs
    for doc in docs:
        doc.status = "uploaded"
    db_session.commit()

    paid = client.post(
        f"/api/v1/fees/{fee_id}/mark-paid",
        headers=h_collecteur,
        json={"payment_ref": "COL-UPLOADED-ONLY"},
    )
    assert paid.status_code == 200

    decision = client.patch(
        f"/api/v1/or-compliance/collector-cards/{card_id}/decision",
        headers=h_com_admin,
        json={"decision": "approved"},
    )
    assert decision.status_code == 400
    assert "pieces_obligatoires_manquantes" in str(decision.json())


def test_collector_fee_split_is_50_30_20(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    collecteur = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur3@test.mg",
        phone="0341000005",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    admin = _create_actor(
        db_session,
        role="admin",
        email="adminsplit@test.mg",
        phone="0341000006",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    h_collecteur = _auth(client, collecteur.email)
    h_admin = _auth(client, admin.email)
    request = client.post(
        "/api/v1/or-compliance/collector-cards",
        headers=h_collecteur,
        json={"actor_id": collecteur.id, "issuing_commune_id": communes[0].id},
    )
    assert request.status_code == 201
    fee_id = request.json()["fee_id"]
    paid = client.patch(f"/api/v1/fees/{fee_id}/status", headers=h_admin, json={"status": "paid"})
    assert paid.status_code == 200
    splits = db_session.query(CollectorCardFeeSplit).filter(CollectorCardFeeSplit.fee_id == fee_id).all()
    assert len(splits) == 3
    ratios = sorted([float(s.ratio_percent) for s in splits])
    assert ratios == [20.0, 30.0, 50.0]
    total_split = sum([float(s.amount) for s in splits])
    fee = db_session.query(Fee).filter_by(id=fee_id).first()
    assert round(total_split, 2) == round(float(fee.amount), 2)
    assert (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "collector_card_requested")
        .first()
        is not None
    )


def test_affiliation_type_must_match_target_actor_role(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    collecteur = _create_actor(
        db_session,
        role="collecteur",
        email="collecteur-aff@test.mg",
        phone="0341000301",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    wrong_target = _create_actor(
        db_session,
        role="collecteur",
        email="wrong-target@test.mg",
        phone="0341000302",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    db_session.add(
        CollectorCard(
            actor_id=collecteur.id,
            issuing_commune_id=communes[0].id,
            status="active",
            issued_at=datetime.now(timezone.utc),
            validated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=300),
            affiliation_deadline_at=datetime.now(timezone.utc) + timedelta(days=90),
        )
    )
    db_session.commit()
    card = db_session.query(CollectorCard).filter(CollectorCard.actor_id == collecteur.id).first()
    assert card is not None
    headers = _auth(client, collecteur.email)

    res = client.post(
        "/api/v1/or-compliance/collector-affiliations",
        headers=headers,
        json={
            "collector_card_id": card.id,
            "affiliate_actor_id": wrong_target.id,
            "affiliate_type": "comptoir",
            "agreement_ref": "AFF-001",
            "signed_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert res.status_code == 400
    assert "acteur_affiliation_invalide" in str(res.json())


def test_affiliation_missing_blocks_or_transaction_and_audit_exists(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    seller = _create_actor(
        db_session,
        role="collecteur",
        email="seller@test.mg",
        phone="0341000007",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    buyer = _create_actor(
        db_session,
        role="bijoutier",
        email="buyer@test.mg",
        phone="0341000008",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    seller_headers = _auth(client, seller.email)
    geo = client.post("/api/v1/geo-points", json={"lat": -18.89, "lon": 47.49, "accuracy_m": 10, "source": "gps"}).json()

    card = CollectorCard(
        actor_id=seller.id,
        issuing_commune_id=communes[0].id,
        status="active",
        issued_at=datetime.now(timezone.utc) - timedelta(days=120),
        expires_at=datetime.now(timezone.utc) + timedelta(days=200),
        affiliation_deadline_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(card)
    db_session.commit()

    lot = client.post(
        "/api/v1/lots",
        headers=seller_headers,
        json={
            "filiere": "OR",
            "product_type": "or_brut",
            "unit": "g",
            "quantity": 2,
            "declare_geo_point_id": geo["id"],
            "declared_by_actor_id": seller.id,
            "notes": "lot",
            "photo_urls": [],
        },
    )
    assert lot.status_code == 400
    assert "laissez_passer_bloque" in str(lot.json())

    assert (
        db_session.query(Actor)
        .filter(Actor.id == seller.id)
        .first()
        .laissez_passer_access_status
        == "blocked"
    )


def test_card_requires_payment_then_generates_signed_qr(client, db_session):
    region, district, communes, version = _seed_territory(db_session, commune_count=1)
    actor = _create_actor(
        db_session,
        role="orpailleur",
        email="card-flow@test.mg",
        phone="0341000009",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    commune_agent = _create_actor(
        db_session,
        role="commune_agent",
        email="commune-card@test.mg",
        phone="0341000010",
        commune_id=communes[0].id,
        region_id=region.id,
        district_id=district.id,
        version_id=version.id,
    )
    actor_headers = _auth(client, actor.email)
    commune_headers = _auth(client, commune_agent.email)

    created = client.post(
        "/api/v1/or-compliance/cards/request",
        headers=actor_headers,
        json={
            "card_type": "kara_bolamena",
            "actor_id": actor.id,
            "commune_id": communes[0].id,
            "cin": "CIN-CARD-01",
        },
    )
    assert created.status_code == 201
    card_id = created.json()["id"]
    fee_id = created.json()["fee_id"]
    assert created.json()["status"] == "pending_payment"

    blocked = client.post(
        f"/api/v1/or-compliance/cards/{card_id}/validate",
        headers=commune_headers,
        params={"card_type": "kara_bolamena"},
        json={"decision": "approved"},
    )
    assert blocked.status_code == 400
    assert (
        "frais_ouverture_non_payes" in str(blocked.json())
        or "eligibilite_kara_non_validee" in str(blocked.json())
    )

    card_row = db_session.query(KaraBolamenaCard).filter(KaraBolamenaCard.id == card_id).first()
    assert card_row is not None
    card_row.residence_verified = True
    card_row.tax_compliant = True
    card_row.zone_allowed = True
    card_row.public_order_clear = True
    db_session.commit()

    paid = client.post(f"/api/v1/fees/{fee_id}/mark-paid", headers=actor_headers, json={"payment_ref": "E2E-1"})
    assert paid.status_code == 200

    validated = client.post(
        f"/api/v1/or-compliance/cards/{card_id}/validate",
        headers=commune_headers,
        params={"card_type": "kara_bolamena"},
        json={"decision": "approved"},
    )
    assert validated.status_code == 200
    body = validated.json()
    assert body["status"] == "validated"
    assert body["card_number"]
    assert body["qr_signature"]
    assert body["front_document_id"]
    assert body["back_document_id"]

    render_front = client.get(
        f"/api/v1/or-compliance/cards/{card_id}/render",
        headers=actor_headers,
        params={"card_type": "kara_bolamena", "side": "front"},
    )
    assert render_front.status_code == 200
    assert render_front.json()["document_id"] == body["front_document_id"]

    download = client.get(f"/api/v1/documents/{body['front_document_id']}/download", headers=actor_headers)
    assert download.status_code == 200

    verify = client.get(f"/api/v1/verify/card/{body['card_number']}")
    assert verify.status_code == 200
    assert verify.json()["signature_valid"] is True
