from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from storage import read_transactions_csv
from transactions import _rewrite_csv

CATEGORIES_JSON = "categories.json"  # optional file if you want to persist a list

def list_categories(tx_path: Path, user_id: str) -> List[str]:

    rows = read_transactions_csv(tx_path)
    s = {r.get("category","") for r in rows if r.get("user_id")==user_id and r.get("category")}
    return sorted(s, key=str.lower)

def rename_category(tx_path: Path, user_id: str, old: str, new: str) -> int:

    rows = read_transactions_csv(tx_path)
    changed = 0
    for r in rows:
        if r.get("user_id")==user_id and r.get("category")==old:
            r["category"] = new
            changed += 1
    if changed:
        _rewrite_csv(tx_path, rows)
    return changed

def merge_categories(tx_path: Path, user_id: str, sources: List[str], target: str) -> int:

    rows = read_transactions_csv(tx_path)
    src = set(sources)
    changed = 0
    for r in rows:
        if r.get("user_id")==user_id and r.get("category") in src:
            r["category"] = target
            changed += 1
    if changed:
        _rewrite_csv(tx_path, rows)
    return changed
