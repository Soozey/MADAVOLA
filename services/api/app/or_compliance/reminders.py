from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.audit.logger import write_audit
from app.models.or_compliance import ComplianceNotification, CollectorCard, ComptoirLicense, KaraBolamenaCard


def run_expiry_reminders(db: Session, thresholds: list[int], actor_id: int) -> int:
    now = datetime.now(timezone.utc)
    created = 0

    def process(entity_type: str, entity_id: int, owner_actor_id: int, expires_at: datetime | None) -> None:
        nonlocal created
        if not expires_at:
            return
        delta_days = (expires_at.date() - now.date()).days
        if delta_days not in thresholds:
            return
        existing = (
            db.query(ComplianceNotification)
            .filter(
                ComplianceNotification.entity_type == entity_type,
                ComplianceNotification.entity_id == entity_id,
                ComplianceNotification.actor_id == owner_actor_id,
                ComplianceNotification.days_before == delta_days,
            )
            .first()
        )
        if existing:
            return
        message = f"{entity_type} expire dans {delta_days} jour(s)"
        db.add(
            ComplianceNotification(
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=owner_actor_id,
                channel="in_app",
                days_before=delta_days,
                message=message,
                status="sent",
            )
        )
        write_audit(
            db,
            actor_id=actor_id,
            action="compliance_reminder_sent",
            entity_type=entity_type,
            entity_id=str(entity_id),
            meta={"days_before": delta_days},
        )
        created += 1

    for card in db.query(KaraBolamenaCard).filter(KaraBolamenaCard.status.in_(["active", "validated"])).all():
        process("kara_card", card.id, card.actor_id, card.expires_at)

    for card in db.query(CollectorCard).filter(CollectorCard.status.in_(["active", "validated"])).all():
        process("collector_card", card.id, card.actor_id, card.expires_at)

    for license_row in db.query(ComptoirLicense).filter(ComptoirLicense.status == "active").all():
        process("comptoir_license", license_row.id, license_row.actor_id, license_row.expires_at)

    db.commit()
    return created
