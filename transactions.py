from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterable, Tuple
from datetime import date

from storage import read_transactions_csv, append_transactions_csv
from logutil import get_logger
from typing import Callable
import csv

LOGGER = get_logger(__name__)

SUPPORTED_TYPES = ("income", "expense")
SUPPORTED_METHODS = ("Cash", "Debit Card", "Credit Card", "Bank Transfer", "Wallet")

@dataclass
class NewTransaction:
     user_id: str
     type: str
     amount: Decimal
     category: str
     date: date
     description: str
     payment_method: str


def parse_money(txt: str, *, max_digits: int = 12, scale: int = 2) -> Decimal:
      if txt is None:
        raise ValueError("Amount is required.")
      s = txt.strip()
      if not s:
        raise ValueError("Amount is required.")
      if s.startswith(("+", "-")):
        raise ValueError("Do not use +/-; choose type = income/expense instead.")

      try:
        d = Decimal(s)
      except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid number (e.g., 12.50).")

      if d < 0:
        raise ValueError("Amount cannot be negative. Use type='expense' for outflows.")

      digits_only = s.replace(".", "")
      if not digits_only.isdigit():
        raise ValueError("Use digits and '.' only, e.g., 1234.56")
      if len(digits_only) > max_digits:
        raise ValueError(f"Amount has too many digits (>{max_digits}).")
      
      q = Decimal(10) ** -scale  
      return d.quantize(q, rounding=ROUND_HALF_UP)

def validate_type(t: str) -> str:
    if t is None:
        raise ValueError("Type is required.")
    v = t.strip().lower()
    if v not in SUPPORTED_TYPES:
        raise ValueError(f"Type must be one of {SUPPORTED_TYPES}.")
    return v

def validate_payment_method(m: str) -> str:
    if m is None:
        raise ValueError("Payment method is required.")
    v = m.strip()
    if v not in SUPPORTED_METHODS:
        raise ValueError(f"Payment method must be one of {SUPPORTED_METHODS}.")
    return v


def validate_category(cat: str, *, min_len: int = 1, max_len: int = 40) -> str:
       if cat is None:
        raise ValueError("Category is required.")
       v = cat.strip()
       if not (min_len <= len(v) <= max_len):
        raise ValueError(f"Category length must be {min_len}..{max_len} characters.")
       return v


def parse_iso_date(d: str) -> date:
    if d is None:
        raise ValueError("Date is required.")
    ds = d.strip()
    try:
        return date.fromisoformat(ds)
    except ValueError:
        raise ValueError("Date must be in ISO format YYYY-MM-DD.")
    
def next_transaction_id(tx_path: Path) -> str:
     rows = read_transactions_csv(tx_path)
     max_num = 0
     for r in rows:
        tid = r.get("transaction_id", "")
        if tid.startswith("T") and tid[1:].isdigit():
            max_num = max(max_num, int(tid[1:]))
     return f"T{(max_num + 1):06d}"


def persist_transaction(tx_path: Path, tx: NewTransaction, *, tx_id: Optional[str] = None) -> str:
     tid = tx_id or next_transaction_id(tx_path)
     append_transactions_csv(tx_path, [{
        "transaction_id": tid,
        "user_id": tx.user_id,
        "type": tx.type,
        "amount": str(tx.amount),              
        "category": tx.category,
        "date": tx.date.isoformat(),         
        "description": tx.description,
        "payment_method": tx.payment_method,
    }])
     LOGGER.info("Persisted transaction %s for user %s", tid, tx.user_id)
     return tid

def create_transaction(
    user_id: str,
    *,
    type: str,
    amount: str,
    category: str,
    date_str: str,
    description: str,
    payment_method: str
) -> NewTransaction:
    if not user_id:
        raise ValueError("Missing user id (are you logged in?).")

    v_type = validate_type(type)
    v_amount = parse_money(amount)
    v_cat = validate_category(category)
    v_date = parse_iso_date(date_str)
    v_desc = (description or "").strip()
    v_method = validate_payment_method(payment_method)
    LOGGER.debug(
        "Create TX: user=%s type=%s amount=%s category=%s date=%s method=%s",
        user_id,
        type,
        amount,
        category,
        date_str,
        payment_method,
    )

    return NewTransaction(
        user_id=user_id,
        type=v_type,
        amount=v_amount,
        category=v_cat,
        date=v_date,
        description=v_desc,
        payment_method=v_method,
    )


def list_user_transactions(tx_path: Path, user_id: str, *, newest_first: bool = True) -> List[Dict[str, Any]]:
    rows = read_transactions_csv(tx_path)
    mine = [r for r in rows if r.get("user_id") == user_id]
    mine.sort(key=lambda r: (r.get("date", ""), r.get("transaction_id", "")), reverse=newest_first)
    return mine




def _rewrite_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
  
    from storage import CSV_FIELDNAMES
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def get_transaction_by_id(tx_path: Path, tid: str) -> Dict[str, str] | None:

    rows = read_transactions_csv(tx_path)
    for r in rows:
        if r.get("transaction_id") == tid:
            return r
    return None

def edit_transaction(
    tx_path: Path,
    tid: str,
    updater: Callable[[Dict[str, str]], Dict[str, str] | None]
) -> bool:

    rows = read_transactions_csv(tx_path)
    changed = False
    for i, r in enumerate(rows):
        if r.get("transaction_id") == tid:
            new_row = updater(dict(r))
            if new_row is None:
                return False
            rows[i] = new_row
            changed = True
            break
    if changed:
        _rewrite_csv(tx_path, rows)
    return changed

def delete_transaction(tx_path: Path, tid: str) -> bool:

    rows = read_transactions_csv(tx_path)
    new_rows = [r for r in rows if r.get("transaction_id") != tid]
    if len(new_rows) == len(rows):
        return False
    _rewrite_csv(tx_path, new_rows)
    return True