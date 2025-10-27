from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date

from storage import read_json, write_json
from transactions import create_transaction, persist_transaction
from reports import ReportFilters, load_user_rows



def _file(path: Path) -> Path:
    return path

def load_recurrences(path: Path) -> List[Dict[str, Any]]:
    return read_json(path)

def save_recurrences(path: Path, items: List[Dict[str, Any]]) -> None:
    write_json(path, items)

def add_recurrence(
    path: Path,
    user_id: str,
    *,
    category: str,
    amount: str,
    type: str,
    payment_method: str,
    description: str,
    day_of_month: int
) -> Dict[str, Any]:
 
    if not (1 <= int(day_of_month) <= 28):
        raise ValueError("day_of_month must be 1..28.")
    items = load_recurrences(path)
    # Upsert by (user_id, category, description)
    replaced = False
    updated_item: Dict[str, Any] | None = None
    for it in items:
        if it["user_id"]==user_id and it["category"]==category and it.get("description","")==description:
            it.update({
                "amount": amount, "type": type, "payment_method": payment_method,
                "day_of_month": int(day_of_month)
            })
            replaced = True
            updated_item = it
            break
    if not replaced:
        new_item = {
            "user_id": user_id,
            "category": category,
            "amount": amount,
            "type": type,
            "payment_method": payment_method,
            "description": description,
            "day_of_month": int(day_of_month),
        }
        items.append(new_item)
        updated_item = new_item
    save_recurrences(path, items)
    if updated_item is None:
        raise RuntimeError("Failed to persist recurrence.")
    return updated_item

def list_recurrences(path: Path, user_id: str) -> List[Dict[str, Any]]:
    return [r for r in load_recurrences(path) if r.get("user_id")==user_id]

def post_due_recurrences(
    tx_path: Path,
    recurrences_path: Path,
    user_id: str,
    month: str
) -> Tuple[int, int]:
  
    from transactions import parse_iso_date
    y, m = int(month[:4]), int(month[5:])
    posted, present = 0, 0

    items = list_recurrences(recurrences_path, user_id)

    # Build quick lookup of existing (date, amount, desc, category, type)
    from storage import read_transactions_csv
    rows = read_transactions_csv(tx_path)
    have = set(
        (r["date"], r["amount"], r.get("description",""), r.get("category",""), r.get("type",""))
        for r in rows if r.get("user_id")==user_id
    )

    for r in items:
        run_date = date(y, m, int(r["day_of_month"]))
        dstr = run_date.isoformat()
        key = (dstr, str(Decimal(r["amount"])), r.get("description",""), r["category"], r["type"])
        if key in have:
            present += 1
            continue

        tx = create_transaction(
            user_id,
            type=r["type"],
            amount=r["amount"],
            category=r["category"],
            date_str=dstr,
            description=r.get("description",""),
            payment_method=r["payment_method"],
        )
        persist_transaction(tx_path, tx)
        posted += 1
        have.add(key)

    return posted, present
