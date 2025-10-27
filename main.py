from  decimal import Decimal
from pathlib import Path
import sys
from typing import Optional
from datetime import date
from categories import list_categories, merge_categories, rename_category
from storage import read_json, write_json, append_transactions_csv, read_transactions_csv
from users import register_user, authenticate
from transactions import (
    SUPPORTED_METHODS as TX_SUPPORTED_METHODS,
    create_transaction,
    delete_transaction,
    edit_transaction,
    get_transaction_by_id,
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
from logutil import get_logger
from budgets import set_budget, get_budgets, spend_vs_budget



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

LOGGER = get_logger("pfm", app_root=App_ROOT)
BUDGETS_JSON = Data_DIR / "budgets.json"
RECURRENCES_JSON = Data_DIR / "recurrences.json"

def current_currency() -> str:
    if CURRENT_USER and "currency" in CURRENT_USER:
        return CURRENT_USER["currency"]
    return ""

def print_banner()-> None:
    # Lightweight splash to make the CLI feel intentional.
    print("=" * 58)
    print("💰 Personal Finance Manager (Console Edition)")
    print("=" * 58)
    LOGGER.info("Application started")

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
        print("[6] Budgets")
        print("[7] Edit/Delete transactions")
        print("[8] Category manager")
        print("[9] Import/Export")
        print("[10] Recurring transactions")
        print("[0] Exit") 

        choice = input("Select an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            sys.exit(0)
        elif choice == "1":
            
            
            # Nested loop handles register/login/logout without leaving the main menu.
            while True:
                 if CURRENT_USER:
                    print(f"\n👤 Current user: {CURRENT_USER['name']} [{current_currency()}]")
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
                if tx.type == "expense":
                    month_label = f"{tx.date.year:04d}-{tx.date.month:02d}"
                    rows = spend_vs_budget(TXNS_CSV, BUDGETS_JSON, CURRENT_USER["user_id"], month_label, type_filter="expense")
                    # find this category
                    for cat, actual, budget, delta in rows:
                        if cat == tx.category:
                            if budget > 0 and delta < 0:
                                # over by abs(delta)
                                over = (-delta).quantize(Decimal("0.01"))
                                print(f"🚨 Over budget for {cat} in {month_label} by {over} {current_currency()}.")
                            elif budget > 0 and delta <= Decimal("0.00"):
                                print(f"⚠️ You have reached your {cat} budget for {month_label}.")
                            elif budget > 0:
                                remaining = delta.quantize(Decimal("0.01"))
                                print(f"ℹ️ Remaining {cat} budget for {month_label}: {remaining} {current_currency()}.")
                            break
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
                    amt = f"{amt} {current_currency()}"
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
                print("[5] ASCII chart: Totals by category (optionally filtered)")

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
                            amt = f"{amt} {current_currency()}"
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

                elif sub == "5":
                    print("\n(Optional) Enter filters or press Enter to skip.")
                    start_s = input("Start date (YYYY-MM-DD): ").strip()
                    end_s   = input("End date   (YYYY-MM-DD): ").strip()
                    pm      = input("Payment method (exact): ").strip()
                    cat     = input("Category (exact): ").strip()
                    ttype   = input("Type (income/expense): ").strip()

                    def parse_opts_date(s):
                        from transactions import parse_iso_date
                        return parse_iso_date(s) if s else None

                    filters = ReportFilters(
                        start=parse_opts_date(start_s),
                        end=parse_opts_date(end_s),
                        payment_method=(pm or None),
                        category=(cat or None),
                        type=(ttype or None),
                    )

                    rows = load_user_rows(TXNS_CSV, CURRENT_USER["user_id"], filters)
                    if not rows:
                        print("No matching transactions.")
                        continue

                    # Build (category, total) pairs with Decimal
                    from collections import defaultdict
                    agg = defaultdict(lambda: Decimal("0"))
                    for r in rows:
                        try:
                            amt = Decimal(r.get("amount","0"))
                        except Exception:
                            continue
                        agg[r.get("category","")] += amt

                    # Render bars
                    from ascii_charts import hbar_chart
                    pairs = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
                    for line in hbar_chart(pairs, width=40):
                        print(line)
        

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
        elif choice == "6":
            if CURRENT_USER is None:
                print("🔒 Please login first (Menu → [1] Login / Switch user).")
                continue
            while True:
                print("\nBudgets")
                print("[1] Set/Update monthly category budget")
                print("[2] List budgets for a month")
                print("[3] Budget vs Actual (by month)")
                print("[0] Back")
                sub = input("Select an option: ").strip()

                if sub == "0":
                    break

                elif sub == "1":
                    month = input("Month (YYYY-MM): ").strip()
                    category = input("Category: ").strip()
                    amount = input("Budget amount (e.g., 1200 or 1200.00): ").strip()
                    try:
                        b = set_budget(BUDGETS_JSON, CURRENT_USER["user_id"], month, category, amount)
                        print(f"✅ Budget set: {b.category} {b.month} = {b.amount} {current_currency()}")
                    except ValueError as e:
                        print(f"⚠️ {e}")

                elif sub == "2":
                    month = input("Month (YYYY-MM): ").strip()
                    items = get_budgets(BUDGETS_JSON, CURRENT_USER["user_id"], month or None)
                    if not items:
                        print("No budgets found.")
                        continue
                    # simple table
                    headers = ("Category", "Budget")
                    widths = (20, 16)
                    def format_row(label, value): return f"{label.ljust(widths[0])}  {value.ljust(widths[1])}"
                    print(format_row(*headers)); print("-" * (sum(widths) + 2))
                    for it in sorted(items, key=lambda x: x.category.lower()):
                        print(format_row(it.category, f"{it.amount} {current_currency()}"))

                elif sub == "3":
                    month = input("Month (YYYY-MM): ").strip()
                    try:
                        rows = spend_vs_budget(TXNS_CSV, BUDGETS_JSON, CURRENT_USER["user_id"], month, type_filter="expense")
                    except ValueError as e:
                        print(f"⚠️ {e}")
                        continue
                    if not rows:
                        print("No budgets or transactions for this month.")
                        continue
                    # Render table: Category | Actual | Budget | Delta (budget-actual)
                    headers = ("Category", "Actual", "Budget", "Delta")
                    widths = (18, 14, 14, 14)
                    def clip(s, w): return s if len(s) <= w else s[:w-1] + "…"
                    def fmt_money_budget(val): 
                        from decimal import Decimal as D
                        q = D("0.01")
                        currency = current_currency()
                        suffix = f" {currency}" if currency else ""
                        return f"{val.quantize(q)}{suffix}"
                    print(f"\nBudget vs Actual for {month}")
                    print(clip(headers[0], widths[0]).ljust(widths[0]),
                        clip(headers[1], widths[1]).ljust(widths[1]),
                        clip(headers[2], widths[2]).ljust(widths[2]),
                        clip(headers[3], widths[3]).ljust(widths[3]))
                    print("-" * (sum(widths) + 3*2))
                    for cat, actual, budget, delta in rows:
                        print(clip(cat, widths[0]).ljust(widths[0]),
                            clip(fmt_money_budget(actual), widths[1]).ljust(widths[1]),
                            clip(fmt_money_budget(budget), widths[2]).ljust(widths[2]),
                            clip(fmt_money_budget(delta), widths[3]).ljust(widths[3]))
                else:
                    print("⚠️ Invalid choice. Try again.")
        elif choice == "7":
            if CURRENT_USER is None:
                print("🔒 Please login first.")
                continue

            print("\nEdit/Delete")
            print("[1] Edit by ID")
            print("[2] Delete by ID")
            print("[0] Back")
            sub = input("Select: ").strip()

            if sub == "1":
                tid = input("Transaction ID (e.g., T000001): ").strip()
                row = get_transaction_by_id(TXNS_CSV, tid)
                if not row or row.get("user_id") != CURRENT_USER["user_id"]:
                    print("Not found or not your transaction.")
                else:
                    print("Leave a field blank to keep current value.")
                    t_type = input(f"Type [{row['type']}]: ").strip() or row["type"]
                    amt    = input(f"Amount [{row['amount']}]: ").strip() or row["amount"]
                    cat    = input(f"Category [{row['category']}]: ").strip() or row["category"]
                    dstr   = input(f"Date [{row['date']}]: ").strip() or row["date"]
                    desc   = input(f"Description [{row['description']}]: ").strip() or row["description"]
                    pm     = input(f"Payment method [{row['payment_method']}]: ").strip() or row["payment_method"]

                    try:
                        # Re-validate using the same logic
                        tx = create_transaction(
                            CURRENT_USER["user_id"],
                            type=t_type,
                            amount=amt,
                            category=cat,
                            date_str=dstr,
                            description=desc,
                            payment_method=pm,
                        )
                        def updater(old):
                            return {
                                "transaction_id": old["transaction_id"],
                                "user_id": tx.user_id,
                                "type": tx.type,
                                "amount": str(tx.amount),
                                "category": tx.category,
                                "date": tx.date.isoformat(),
                                "description": tx.description,
                                "payment_method": tx.payment_method,
                            }
                        ok = edit_transaction(TXNS_CSV, tid, updater)
                        print("✅ Updated." if ok else "Nothing changed.")
                    except ValueError as e:
                        print(f"⚠️ {e}")

            elif sub == "2":
                tid = input("Transaction ID (e.g., T000001): ").strip()
                # Optional: ensure it's the user's
                row = get_transaction_by_id(TXNS_CSV, tid)
                if not row or row.get("user_id") != CURRENT_USER["user_id"]:
                    print("Not found or not your transaction.")
                else:
                    conf = input(f"Type YES to delete {tid}: ").strip()
                    if conf == "YES":
                        print("✅ Deleted." if delete_transaction(TXNS_CSV, tid) else "Nothing deleted.")
                    else:
                        print("Cancelled.")
        elif choice == "8":
            if CURRENT_USER is None:
                print("🔒 Please login first.")
                continue
            print("\nCategories")
            print("[1] List my categories")
            print("[2] Rename a category")
            print("[3] Merge categories")
            print("[0] Back")
            sub = input("Select: ").strip()

            if sub == "1":
                cats = list_categories(TXNS_CSV, CURRENT_USER["user_id"])
                if not cats: print("No categories yet.")
                else:
                    print("Your categories:")
                    for c in cats: print(" -", c)

            elif sub == "2":
                old = input("Old category: ").strip()
                new = input("New category: ").strip()
                n = rename_category(TXNS_CSV, CURRENT_USER["user_id"], old, new)
                print(f"✅ Renamed {n} row(s).")

            elif sub == "3":
                sources = input("Comma-separated categories to merge: ").strip()
                target = input("Target category: ").strip()
                src_list = [s.strip() for s in sources.split(",") if s.strip()]
                n = merge_categories(TXNS_CSV, CURRENT_USER["user_id"], src_list, target)
                print(f"✅ Merged {n} row(s).")
        elif choice == "9":
            if CURRENT_USER is None:
                print("🔒 Please login first.")
                continue
            print("\nImport/Export")
            print("[1] Export my transactions to CSV")
            print("[2] Import transactions from CSV")
            print("[0] Back")
            sub = input("Select: ").strip()

            if sub == "1":
                outp = input("Destination CSV filename (e.g., my_export.csv): ").strip()
                from import_export import export_user_transactions
                n = export_user_transactions(TXNS_CSV, CURRENT_USER["user_id"], App_ROOT / outp)
                print(f"✅ Exported {n} row(s) to {outp}")

            elif sub == "2":
                inp = input("Source CSV filename (in project folder): ").strip()
                from import_export import import_transactions
                added, skipped = import_transactions(TXNS_CSV, CURRENT_USER["user_id"], App_ROOT / inp)
                print(f"✅ Imported {added} row(s). Skipped {skipped}.")
        elif choice == "10":
            if CURRENT_USER is None:
                print("🔒 Please login first.")
                continue
            print("\nRecurring")
            print("[1] Add/Update recurrence")
            print("[2] List my recurrences")
            print("[3] Post due recurrences for a month")
            print("[0] Back")
            sub = input("Select: ").strip()

            from recurring import add_recurrence, list_recurrences, post_due_recurrences

            if sub == "1":
                cat  = input("Category: ").strip()
                amt  = input("Amount (e.g., 2500.00): ").strip()
                t    = input("Type (income/expense): ").strip()
                pm   = input("Payment method: ").strip()
                desc = input("Description (optional): ").strip()
                dom  = int(input("Day of month (1..28): ").strip())
                try:
                    add_recurrence(RECURRENCES_JSON, CURRENT_USER["user_id"],
                                category=cat, amount=amt, type=t, payment_method=pm, description=desc, day_of_month=dom)
                    print("✅ Recurrence saved.")
                except ValueError as e:
                    print(f"⚠️ {e}")

            elif sub == "2":
                items = list_recurrences(RECURRENCES_JSON, CURRENT_USER["user_id"])
                if not items: print("No recurrences.")
                else:
                    for i in items:
                        print(f"- {i['type']} {i['amount']} {CURRENT_USER['currency']} | {i['category']} on day {i['day_of_month']} via {i['payment_method']} | {i.get('description','')}")
            elif sub == "3":
                month = input("Month (YYYY-MM): ").strip()
                posted, present = post_due_recurrences(TXNS_CSV, RECURRENCES_JSON, CURRENT_USER["user_id"], month)
                print(f"✅ Posted {posted} new. Already present: {present}.")

        else:
            print("⚠️ Invalid choice. Try again.")


if __name__ == "__main__":
    print_banner()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting…")
        LOGGER.warning("Interrupted by user (Ctrl+C)")
    except Exception as e:
        print("\nUnexpected error. See logs/app.log for details.")
        LOGGER.exception("Fatal error: %s", e)
        sys.exit(1)
