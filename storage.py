from __future__ import annotations
import json
import csv
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Dict, Any, List

def read_json(path:Path) -> list[dict]:

    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    return json.loads(text)

def write_json(path:Path , data:list[dict]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2),encoding="utf-8")
    tmp.replace(path)

CSV_FIELDNAMES = [
    "transaction_id","user_id","type","amount","category","date","description","payment_method"
]

def append_transactions_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
     file_exists = path.exists()
     with path.open(mode="a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            _validated = {}
            for k in CSV_FIELDNAMES:
                if k not in row:
                    raise ValueError(f"Missing required field: {k}")
                v = row[k]
                if k == "amount":
                    # Convert Decimal -> string; leave strings as-is
                    if isinstance(v, Decimal):
                        v = str(v)
                    elif not isinstance(v, str):
                        v = str(v)
                _validated[k] = v
            writer.writerow(_validated)

def read_transactions_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)