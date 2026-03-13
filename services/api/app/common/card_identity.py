import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _uuid7_like() -> str:
    # Python 3.14+ exposes uuid.uuid7. Fallback keeps compatibility.
    try:
        import uuid

        if hasattr(uuid, "uuid7"):
            return str(uuid.uuid7())
    except Exception:
        pass
    return str(uuid4())


def build_prefixed_uid(prefix: str) -> str:
    return f"{prefix}{_uuid7_like()}"


def build_card_number(
    *,
    filiere: str,
    commune_code: str,
    seq: int,
    now: datetime | None = None,
) -> str:
    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    yy = ts.strftime("%y")
    clean_filiere = (filiere or "OR").upper().strip()
    clean_commune = (commune_code or "NA").upper().strip()
    return f"MDV-{clean_filiere}-{clean_commune}-{yy}-{seq:06d}"


def build_invoice_number(
    seq: int,
    filiere: str = "OR",
    region_code: str | None = None,
    now: datetime | None = None,
) -> str:
    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    year = ts.strftime("%Y")
    filiere_token = (filiere or "OR").upper().strip() or "OR"
    region_token = (region_code or "NA").upper().strip() or "NA"
    return f"FAC-{year}-{filiere_token}-{region_token}-{seq:08d}"


def build_receipt_number(seq: int, now: datetime | None = None) -> str:
    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    year = ts.strftime("%Y")
    return f"REC-{year}-{seq:08d}"


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sign_hmac_sha256(secret: str, value: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_hmac_sha256(secret: str, value: str, signature: str | None) -> bool:
    if not signature:
        return False
    expected = sign_hmac_sha256(secret, value)
    return hmac.compare_digest(expected, signature)
