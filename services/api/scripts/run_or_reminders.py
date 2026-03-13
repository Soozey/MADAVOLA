#!/usr/bin/env python3
from app.db import SessionLocal
from app.or_compliance.reminders import run_expiry_reminders


def main() -> None:
    db = SessionLocal()
    try:
        created = run_expiry_reminders(db, [30, 7, 1], actor_id=1)
        print(f"OR reminder notifications created: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
