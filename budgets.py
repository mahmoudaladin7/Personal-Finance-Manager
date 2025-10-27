# budgets.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterable, Tuple
from datetime import date

from storage import read_json, write_json
from transactions import parse_iso_date
from reports import load_user_rows, ReportFilters

@dataclass(frozen=True)
class BudgetItem:

    user_id: str
    month: str
    category: str
    amount: Decimal


def _is_valid_month(label: str) -> bool:
   
    if not isinstance(label, str) or len(label) != 7 or label[4] != "-":
        return False
    y, m = label[:4], label[5:]
    return y.isdigit() and m.isdigit() and 1 <= int(m) <= 12


def parse_budget_amount(txt: str) -> Decimal:
    
    if txt is None:
        raise ValueError("Amount is required.")
    s = txt.strip()
    try:
        d = Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError("Budget amount must be a valid number (e.g., 1200 or 1200.00).")
    if d < 0:
        raise ValueError("Budget amount cannot be negative.")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def load_budgets(path: Path) -> List[Dict[str, Any]]:
   
    return read_json(path)


def save_budgets(path: Path, items: List[Dict[str, Any]]) -> None:
    
    write_json(path, items)


def set_budget(path: Path, user_id: str, month: str, category: str, amount_txt: str) -> BudgetItem:
   
    if not user_id:
        raise ValueError("Missing user id.")
    if not _is_valid_month(month):
        raise ValueError("Month must be 'YYYY-MM' with a valid month 01..12.")
    cat = (category or "").strip()
    if not (1 <= len(cat) <= 40):
        raise ValueError("Category length must be 1..40.")
    amt = parse_budget_amount(amount_txt)

    items = load_budgets(path)
    # upsert
    replaced = False
    for it in items:
        if it.get("user_id") == user_id and it.get("month") == month and it.get("category") == cat:
            it["amount"] = str(amt)
            replaced = True
            break
    if not replaced:
        items.append({"user_id": user_id, "month": month, "category": cat, "amount": str(amt)})

    save_budgets(path, items)
    return BudgetItem(user_id=user_id, month=month, category=cat, amount=amt)


def get_budgets(path: Path, user_id: str, month: Optional[str] = None) -> List[BudgetItem]:
    
    out: List[BudgetItem] = []
    for it in load_budgets(path):
        if it.get("user_id") != user_id:
            continue
        if month and it.get("month") != month:
            continue
        try:
            out.append(BudgetItem(
                user_id=it["user_id"],
                month=it["month"],
                category=it["category"],
                amount=Decimal(it["amount"]),
            ))
        except Exception:
            # skip malformed entries
            continue
    return out


def spend_vs_budget(
    tx_path: Path,
    budgets_path: Path,
    user_id: str,
    month: str,
    *,
    type_filter: Optional[str] = "expense"
) -> List[Tuple[str, Decimal, Decimal, Decimal]]:
   
    if not _is_valid_month(month):
        raise ValueError("Month must be 'YYYY-MM' with a valid month 01..12.")

    year = int(month[:4]); mon = int(month[5:])
    start = date(year, mon, 1)
    # compute end-of-month
    if mon == 12:
        end = date(year + 1, 1, 1).fromordinal(date(year + 1, 1, 1).toordinal() - 1)
    else:
        end = date(year, mon + 1, 1).fromordinal(date(year, mon + 1, 1).toordinal() - 1)

    filters = ReportFilters(start=start, end=end, type=(type_filter or None))
    rows = load_user_rows(tx_path, user_id, filters)

    # aggregate actual by category
    from collections import defaultdict
    actuals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    from decimal import Decimal as D
    for r in rows:
        cat = r.get("category") or ""
        try:
            amt = D(r.get("amount", "0"))
        except Exception:
            continue
        actuals[cat] += amt

    # budgets for the month
    bmap: Dict[str, Decimal] = {b.category: b.amount for b in get_budgets(budgets_path, user_id, month)}

    # union of categories
    cats = sorted(set(actuals.keys()) | set(bmap.keys()))
    results: List[Tuple[str, Decimal, Decimal, Decimal]] = []
    for c in cats:
        a = actuals.get(c, Decimal("0"))
        b = bmap.get(c,  Decimal("0"))
        results.append((c, a, b, b - a))  # delta = budget - actual
    # Sort by biggest overspend first (delta ascending), then by category
    results.sort(key=lambda t: (t[3], t[0]))
    return results
