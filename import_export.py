from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List, Iterable, Tuple, Optional
from decimal import Decimal
import csv

from transactions import (
    create_transaction, persist_transaction, list_user_transactions
)

def export_user_transactions(tx_path: Path, user_id: str, dest_csv: Path) -> int:
   
    rows = list_user_transactions(tx_path, user_id, newest_first=False)
    if not rows:
        # still write header
        from storage import CSV_FIELDNAMES
        with dest_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            w.writeheader()
        return 0

    from storage import CSV_FIELDNAMES
    with dest_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)

def import_transactions(
    tx_path: Path,
    user_id: str,
    source_csv: Path,
    *,
    column_map: Dict[str, str] | None = None,
    dedupe_key: Tuple[str, ...] = ("date", "amount", "description"),
) -> Tuple[int, int]:
   
    # Build set of existing dedupe keys for the user
    existing = set()
    from storage import read_transactions_csv
    for r in read_transactions_csv(tx_path):
        if r.get("user_id") == user_id:
            key = tuple(r.get(k, "") for k in dedupe_key)
            existing.add(key)

    added, skipped = 0, 0
    with source_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for src in reader:
            row = { (column_map.get(k, k) if column_map else k): v for k, v in src.items() }
            # Ensure required fields exist
            try:
                tx = create_transaction(
                    user_id,
                    type=row.get("type","expense"),
                    amount=row["amount"],
                    category=row.get("category","Uncategorized"),
                    date_str=row["date"],
                    description=row.get("description",""),
                    payment_method=row.get("payment_method","Cash"),
                )
            except Exception:
                skipped += 1
                continue

            key = (tx.date.isoformat(), str(tx.amount), tx.description)
            if key in existing:
                skipped += 1
                continue

            persist_transaction(tx_path, tx)
            existing.add(key)
            added += 1

    return added, skipped
