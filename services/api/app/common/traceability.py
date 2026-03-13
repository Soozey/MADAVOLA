import json
import re
from datetime import datetime, timezone
from hashlib import sha256


def _sanitize_token(value: str | None, fallback: str, max_len: int = 20) -> str:
    raw = (value or "").strip().upper()
    cleaned = re.sub(r"[^A-Z0-9]", "", raw)
    if not cleaned:
        cleaned = fallback
    return cleaned[:max_len]


def build_lot_number(*, region_code: str | None, permit_ref: str | None, lot_id: int, now: datetime | None = None) -> str:
    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    region = _sanitize_token(region_code, "NA", max_len=10)
    permit = _sanitize_token(permit_ref, "NOREF", max_len=20)
    return f"LOT-{region}-{permit}-{ts.year}-{lot_id:08d}"


def build_traceability_id(*, lot_number: str, origin_ref: str, lot_id: int, now: datetime | None = None) -> str:
    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    digest = sha256(f"{lot_number}|{origin_ref}|{lot_id}|{ts.isoformat()}".encode("utf-8")).hexdigest()[:10].upper()
    return f"TRC-{ts.year}-{lot_id:08d}-{digest}"


def canonical_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def compute_chain_hash(payload: dict) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()

