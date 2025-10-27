from  decimal import Decimal
from pathlib import Path
import sys
from typing import Optional
from datetime import date
from storage import read_json, write_json, append_transactions_csv, read_transactions_csv
from users import register_user, authenticate
from transactions import (
    SUPPORTED_METHODS as TX_SUPPORTED_METHODS,
    create_transaction,
    persist_transaction,
    list_user_transactions,
)
from reports import (
    ReportFilters,
    load_user_rows,
    balance_summary,
    totals_by_category,
    totals_by_month,
    fmt_money,
    render_console_table,
)
from transactions import parse_iso_date
from backups import BackupSpec, create_backup, list_backups, verify_backup, restore_backup

# CLI session state is shared across menus so we always know who is active.
CURRENT_USER: dict | None = None

# Resolve the project structure once; every data touch should go through these.
App_ROOT = Path(__file__).resolve().parent
Data_DIR= App_ROOT / 'data'
BACKUP_DIR = App_ROOT / "backups"
USERS_JSON = Data_DIR / "users.json"
TXNS_CSV = Data_DIR / 'transaction.csv'

SUPPOURTED_TYPES = ("income", "expenses")
SUPPORTED_METHODS = ("Cash", "Debit Card", "Credit Card", "Bank Transfer", "Wallet")


def print_banner()-> None:
    # Lightweight splash to make the CLI feel intentional.
    print("=" * 58)
    print("💰 Personal Finance Manager (Console Edition)")
    print("=" * 58)

def main_menu() -> None:
   global CURRENT_USER 

   # Main navigation loop; stays active until the user exits.
   while True:
        print("\nMain Menu")
        print("[1] Login / Switch user")
        print("[2] Add transaction")
        print("[3] View transactions")
        print("[4] Reports")
        print("[5] Save / Backup")
        print("[0] Exit") 

        choice = input("Select an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            sys.exit(0)
        elif choice == "1":
            
            
            # Nested loop handles register/login/logout without leaving the main menu.
            while True:
                 if CURRENT_USER:
                    print(f"\n👤 Current user: {CURRENT_USER['name']} [{CURRENT_USER['currency']}]")
                 else:
                    print("\n👤 Current user: (none)")
                 print("\nUser Menu")
                 print("[1] Register")
                 print("[2] Login")
                 print("[3] Logout")
                 print("[0] Back")
                 sub = input("Select an option: ").strip()
                 if sub == "0":
                    break
                 elif sub == "1":
                     try:
                         name = input("Choose a username: ")
                         currency = input("Preferred currency (e.g., USD, EUR, SAR): ")
                         pin = input("Choose a PIN (4–12 digits): ")
                         user = register_user(USERS_JSON, name, currency, pin)
                         print(f"✅ User created: {user['user_id']} ({user['name']}, {user['currency']})")
                     except ValueError as e:
                            print(f"⚠️ {e}")
                 elif sub == "2":
                     try:
                        name = input("Username: ")
                        pin = input("PIN: ")
                        user = authenticate(USERS_JSON, name, pin)
                        if user:
                            CURRENT_USER = user
                            print(f"✅ Logged in as {user['name']} ({user['currency']}).")
                        else:
                            print("❌ Invalid username or PIN.")
                     except ValueError as e:
                            print(f"⚠️ {e}")
                 elif sub == "3":
                        if CURRENT_USER is not None:
                            print(f"👋 Logged out: {CURRENT_USER['name']}")
                            CURRENT_USER = None
                        else:
                            print("ℹ️ No user is currently logged in.")
                 else:
                        print("⚠️ Invalid choice. Try again.")
                         
                         
        elif choice == "2":
            if CURRENT_USER is None:
                print("🔒 Please login first (Menu → [1] Login / Switch user).")
                continue
            try:
                print("\nAdd Transaction")
                print("Type options:", ", ".join(("income", "expense")))
                t_type = input("Type: ").strip()

                amt = input("Amount (e.g., 123.45): ").strip()

                cat = input("Category (e.g., Food, Salary, Rent): ").strip()

                d = input("Date (YYYY-MM-DD): ").strip()

                desc = input("Description (optional): ")

                print("Payment methods:", ", ".join(TX_SUPPORTED_METHODS))
                pm = input("Payment method: ").strip()

                tx = create_transaction(
                    CURRENT_USER["user_id"],
                    type=t_type,
                    amount=amt,
                    category=cat,
                    date_str=d,
                    description=desc,
                    payment_method=pm,
        )
                new_id = persist_transaction(TXNS_CSV, tx)
                print(f"✅ Saved transaction {new_id} for user {CURRENT_USER['name']}.")
            except ValueError as e:
                print(f"⚠️ {e}")
        elif choice == "3":
            if CURRENT_USER is None:
                print("🔒 Please login first (Menu → [1] Login / Switch user).")
                continue

            rows = list_user_transactions(TXNS_CSV, CURRENT_USER["user_id"], newest_first=True)
            if not rows:
                print("No transactions yet.")
                continue

    
            headers = ("ID", "Type", "Amount", "Category", "Date", "Method", "Description")
            widths = [10, 8, 12, 14, 12, 14, 40]

            def fmt_row(cols, widths):
                cells = []
                for c, w in zip(cols, widths):
                    s = (c if c is not None else "")
                    if len(s) > w:
                        s = s[: w - 1] + "…"
                    cells.append(s.ljust(w))
                return "  ".join(cells)

            print()
            print(fmt_row(headers, widths))
            print("-" * (sum(widths) + 2 * (len(widths) - 1)))

            for r in rows:
                amt = r.get("amount", "")
                if CURRENT_USER and "currency" in CURRENT_USER:
                    amt = f"{amt} {CURRENT_USER['currency']}"
                else:
                    amt = str(amt)

                line = (
            r.get("transaction_id", ""),
            r.get("type", ""),
            amt,
            r.get("category", ""),
            r.get("date", ""),
            r.get("payment_method", ""),
            r.get("description", "") or "",
        )
                print(fmt_row(line, widths))
        elif choice == "4":
             if CURRENT_USER is None:
                print("🔒 Please login first (Menu → [1] Login / Switch user).")
                continue

             while True:
                print("\nReports")
                print("[1] Balance summary (all time)")
                print("[2] Category totals (with optional filters)")
                print("[3] Monthly totals (with optional filters)")
                print("[4] Filtered listing (show rows)")
                print("[0] Back")

                sub = input("Select an option: ").strip()

                if sub == "0":
                    break

                elif sub == "1":
                    rows = load_user_rows(TXNS_CSV, CURRENT_USER["user_id"])
                    s = balance_summary(rows)
                    data = [
                        ("Total income",  fmt_money(s["income"],  CURRENT_USER["currency"])),
                        ("Total expense", fmt_money(s["expense"], CURRENT_USER["currency"])),
                        ("Net",           fmt_money(s["net"],     CURRENT_USER["currency"])),
                    ]
                    print()
                    render_console_table(data, headers=("Metric", "Amount"))

                elif sub == "2":
                    
                    print("\n(Optional) Enter filters or press Enter to skip.")
                    start_s = input("Start date (YYYY-MM-DD): ").strip()
                    end_s   = input("End date   (YYYY-MM-DD): ").strip()
                    pm      = input("Payment method (exact): ").strip()
                    cat     = input("Category (exact): ").strip()
                    ttype   = input("Type (income/expense): ").strip()

                    def parse_opt_date(s: str) -> Optional[date]:
                        return parse_iso_date(s) if s else None

                    filters = ReportFilters()
                    filters.start = parse_opt_date(start_s)
                    filters.end = parse_opt_date(end_s)
                    filters.payment_method = pm or None
                    filters.category = cat or None
                    filters.type = ttype or None

                    rows = load_user_rows(TXNS_CSV, CURRENT_USER["user_id"], filters)
                    if not rows:
                        print("No matching transactions.")
                        continue

                    agg = totals_by_category(rows)
                    printable = [(cat, fmt_money(total, CURRENT_USER["currency"])) for cat, total in agg]
                    print()
                    render_console_table(printable, headers=("Category", "Total"), widths=(24, 16))

                elif sub == "3":
                    # Monthly totals with optional filters
                    print("\n(Optional) Enter filters or press Enter to skip.")
                    start_s = input("Start date (YYYY-MM-DD): ").strip()
                    end_s   = input("End date   (YYYY-MM-DD): ").strip()
                    pm      = input("Payment method (exact): ").strip()
                    cat     = input("Category (exact): ").strip()
                    ttype   = input("Type (income/expense): ").strip()

                    def parse_opt_date(s: str) -> Optional[date]:
                        return parse_iso_date(s) if s else None

                    filters = ReportFilters()
                    filters.start = parse_opt_date(start_s)
                    filters.end = parse_opt_date(end_s)
                    filters.payment_method = pm or None
                    filters.category = cat or None
                    filters.type = ttype or None

                    rows = load_user_rows(TXNS_CSV, CURRENT_USER["user_id"], filters)
                    if not rows:
                        print("No matching transactions.")
                        continue

                    agg = totals_by_month(rows)  # [('2025-09', Decimal(...)), ...]
                    printable = [(label, fmt_money(total, CURRENT_USER["currency"])) for label, total in agg]
                    print()
                    render_console_table(printable, headers=("Month", "Total"), widths=(10, 16))

                elif sub == "4":
                    print("\n(Optional) Enter filters or press Enter to skip.")
                    start_s = input("Start date (YYYY-MM-DD): ").strip()
                    end_s   = input("End date   (YYYY-MM-DD): ").strip()
                    pm      = input("Payment method (exact): ").strip()
                    cat     = input("Category (exact): ").strip()
                    ttype   = input("Type (income/expense): ").strip()

                    def parse_opt_date(s: str) -> Optional[date]:
                        return parse_iso_date(s) if s else None

                    filters = ReportFilters()
                    filters.start = parse_opt_date(start_s)
                    filters.end = parse_opt_date(end_s)
                    filters.payment_method = pm or None
                    filters.category = cat or None
                    filters.type = ttype or None

                    rows = load_user_rows(TXNS_CSV, CURRENT_USER["user_id"], filters)
                    if not rows:
                        print("No matching transactions.")
                        continue

                    # Reuse the same simple “table” formatter from Lesson 3
                    headers = ("ID", "Type", "Amount", "Category", "Date", "Method", "Description")
                    widths = [10, 8, 12, 14, 12, 14, 40]

                    def fmt_row(cols, widths):
                        cells = []
                        for c, w in zip(cols, widths):
                            s = (c if c is not None else "")
                            if len(s) > w:
                                s = s[: w - 1] + "…"
                            cells.append(s.ljust(w))
                        return "  ".join(cells)

                    print()
                    print(fmt_row(headers, widths))
                    print("-" * (sum(widths) + 2 * (len(widths) - 1)))

                    for r in rows:
                        amt = r.get("amount", "")
                        if CURRENT_USER and "currency" in CURRENT_USER:
                            amt = f"{amt} {CURRENT_USER['currency']}"
                        line = (
                            r.get("transaction_id", ""),
                            r.get("type", ""),
                            amt,
                            r.get("category", ""),
                            r.get("date", ""),
                            r.get("payment_method", ""),
                            r.get("description", "") or "",
                        )
                        print(fmt_row(line, widths))

                else:
                        print("⚠️ Invalid choice. Try again.")
        elif choice == "5":
             while True:
                print("\nBackups")
                print("[1] Make backup now")
                print("[2] List backups")
                print("[3] Verify a backup")
                print("[4] Restore a backup")
                print("[0] Back")
                sub = input("Select an option: ").strip()

                if sub == "0":
                    break

                elif sub == "1":
                    # Create a ZIP backup of users.json and transactions.csv
                    spec = BackupSpec(
                        backup_dir=BACKUP_DIR,
                        files=[USERS_JSON, TXNS_CSV],
                    )
                    try:
                        zip_path = create_backup(spec)
                        print(f"✅ Backup created: {zip_path.name}")
                    except OSError as e:
                        print(f"❌ Backup failed: {e}")

                elif sub == "2":
                    zips = list_backups(BACKUP_DIR)
                    if not zips:
                        print("No backups found.")
                        continue
                    print("\nAvailable backups (newest first):")
                    for i, p in enumerate(zips, 1):
                        print(f"[{i}] {p.name}")

                elif sub == "3":
                    zips = list_backups(BACKUP_DIR)
                    if not zips:
                        print("No backups to verify.")
                        continue
                    for i, p in enumerate(zips, 1):
                        print(f"[{i}] {p.name}")
                    sel = input("Select backup number to verify: ").strip()
                    if not sel.isdigit() or not (1 <= int(sel) <= len(zips)):
                        print("Invalid selection.")
                        continue
                    target = zips[int(sel) - 1]
                    ok, errors = verify_backup(target)
                    if ok:
                        print(f"✅ {target.name} integrity OK.")
                    else:
                        print(f"❌ {target.name} integrity FAILED:")
                        for e in errors:
                            print("  -", e)

                elif sub == "4":
                    zips = list_backups(BACKUP_DIR)
                    if not zips:
                        print("No backups to restore.")
                        continue
                    for i, p in enumerate(zips, 1):
                        print(f"[{i}] {p.name}")
                    sel = input("Select backup number to restore: ").strip()
                    if not sel.isdigit() or not (1 <= int(sel) <= len(zips)):
                        print("Invalid selection.")
                        continue
                    target = zips[int(sel) - 1]
                    print("⚠️ Restoring will overwrite your current data files.")
                    conf = input("Type 'YES' to continue: ").strip()
                    if conf != "YES":
                        print("Restore cancelled.")
                        continue
                    try:
                        restored = restore_backup(target, Data_DIR, overwrite=True)
                        if restored:
                            print("✅ Restored files:")
                            for p in restored:
                                print("  -", p.name)
                        else:
                            print("No data files were restored from this backup.")
                    except FileExistsError as e:
                        print(f"❌ {e}")
                    except OSError as e:
                        print(f"❌ Restore failed: {e}")

                else:
                    print("⚠️ Invalid choice. Try again.")
        else:
            print("⚠️ Invalid choice. Try again.")


if __name__ == "__main__":
    print_banner()
    main_menu()
