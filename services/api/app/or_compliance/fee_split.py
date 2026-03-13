from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.fee import Fee
from app.models.or_compliance import CollectorCardFeeSplit
from app.models.territory import Commune, District, Region


def allocate_collector_card_fee_split(db: Session, fee: Fee) -> None:
    if fee.fee_type != "collector_card_right" or fee.status != "paid":
        return
    existing = db.query(CollectorCardFeeSplit).filter(CollectorCardFeeSplit.fee_id == fee.id).first()
    if existing:
        return

    commune = db.query(Commune).filter_by(id=fee.commune_id).first()
    district = db.query(District).filter_by(id=commune.district_id).first() if commune else None
    region = db.query(Region).filter_by(id=district.region_id).first() if district else None
    total = Decimal(str(fee.amount))
    splits = [
        ("commune", commune.code if commune else str(fee.commune_id), Decimal("50")),
        ("region", region.code if region else "unknown", Decimal("30")),
        ("com", "COM", Decimal("20")),
    ]
    for beneficiary_type, beneficiary_ref, ratio in splits:
        amount = (total * ratio) / Decimal("100")
        db.add(
            CollectorCardFeeSplit(
                fee_id=fee.id,
                beneficiary_type=beneficiary_type,
                beneficiary_ref=beneficiary_ref,
                ratio_percent=ratio,
                amount=amount,
                status="allocated",
            )
        )
