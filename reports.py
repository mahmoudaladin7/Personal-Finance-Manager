from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from typing import Iterable, Dict, Any, List, Optional, Tuple
from collections import defaultdict

from pathlib import Path
from storage import read_transactions_csv
from transactions import parse_iso_date

def _parse_amount_str(s: str) -> Decimal:
    try:
        return Decimal(s)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid amount string in csv: {s!r}")
    
# Container for optional CLI filters; default None values mean "no filter".
@dataclass
class ReportFilters:
    start: Optional[date] = None
    end: Optional[date] = None
    payment_method: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None


# Centralized predicate so every report enforces filters consistently.
def _row_matches_filters(row: Dict[str, str],f:ReportFilters)->bool:
    if f.start is not None or f.end is not None:
        try:
            d= parse_iso_date(row.get("date", ""))
        except ValueError:
            return False
        if f.start is not None and d < f.start:
            return False
        if f.end is not None and d > f.end:
            return False
    
    if f.payment_method is not None:
        if row.get("payment_method") != f.payment_method:
            return False
        
    if f.category is not None:
        if row.get("category") != f.category:
            return False
        
    if f.type is not None:
        if row.get("type") != f.type:
            return False
    return True

# Pull every row for the user, then optionally trim via the reusable filter helper.
def load_user_rows(tx_path: Path, user_id: str, filters: Optional[ReportFilters] = None) -> List[Dict[str,str]]:
    rows = read_transactions_csv(tx_path)
    mine = [r for r in rows if r.get("user_id") == user_id]
    if filters is None:
        return mine
    return [r for r in mine if _row_matches_filters(r,filters)]

# Aggregate totals into a friendly dict for the balance summary card.
def balance_summary(rows: Iterable[Dict[str,str]]) -> Dict[str,Decimal]:
    inc = Decimal("0")
    exp = Decimal("0")
    for r in rows:
        try:
            amt = _parse_amount_str(r.get("amount","0"))
        except ValueError:
            continue
        t = r.get("type")
        if t == "income":
            inc+= amt
        elif t == "expense":
            exp+= amt 

    return {"income": inc, "expense": exp, "net":inc - exp}

# Roll up validated rows per category so we can rank top spend/earn buckets.
def totals_by_category(rows: Iterable[Dict[str,str]]) -> List[Tuple[str,Decimal]]:
        agg: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for r in rows:
            cat = r.get("category", "")
            if not cat:
                continue
            try:
                amt = _parse_amount_str(r.get("amount", "0"))
            except ValueError:
                continue
            agg[cat] += amt
 
        return sorted(agg.items(), key=lambda kv: kv[1], reverse=True)

# Format YYYY-MM labels so the CLI can render chronological monthly totals.
def totals_by_month(rows: Iterable[Dict[str,  str]]) -> List[Tuple[str,Decimal]]:
    agg: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for r in rows:
        try:
            d = parse_iso_date(r.get("date", ""))
            month_label = f"{d.year:04d}-{d.month:02d}"
        except ValueError:
            continue
        try:
            amt = _parse_amount_str(r.get("amount", "0"))
        except ValueError:
            continue
        agg[month_label] += amt

    
    return sorted(agg.items(), key=lambda kv: kv[0])

# Shared money formatter so every report prints totals consistently.
def fmt_money(d: Decimal, currency: str, *, places: int = 2) -> str:
     q = Decimal(10) ** -places
     return f"{d.quantize(q, rounding=ROUND_HALF_UP)} {currency}"


# Simple fixed-width console table helper used by every summary view.
def render_console_table(rows: List[Tuple[str, str]], headers: Tuple[str, str], widths=(20, 18)) -> None:
     def clip(s: str, w: int) -> str:
        if len(s) <= w:
            return s
        return s[: w - 1] + "…"

     line_w = widths[0] + widths[1] + 2
     print(clip(headers[0], widths[0]).ljust(widths[0]), clip(headers[1], widths[1]).ljust(widths[1]))
     print("-" * line_w)
     for lab, val in rows:
            print(clip(lab, widths[0]).ljust(widths[0]), clip(val, widths[1]).ljust(widths[1]))
