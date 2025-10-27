# Personal Finance Manager (Console Edition)

A lightweight, terminal-based companion that lets you register users, authenticate with a PIN, and track personal finance transactions locally with zero external services. All data is stored on disk (JSON/CSV), works offline, and is easy to back up or migrate.

> Current status: Milestone 4 complete (Budgets, Categories, Import/Export, Recurring). Next up: small UX polish and pagination.

## Features
- Interactive console with menus for Users, Transactions, Reports, Backups, Budgets, Categories, Import/Export, and Recurring entries
- Secure user management with PBKDF2 PIN hashing in `users.py`
- JSON-backed users plus CSV transaction history via `storage.py`
- Validated transaction capture (type, amount, category, ISO date, payment method) with auto IDs
- Currency-aware viewer rendering a fixed-width table per user
- Reporting hub: balance summary, category totals, month-over-month, filtered listings, and ASCII bar charts
- Backups: ZIP snapshots with manifest verification and safe restore
- Budgets: per-category monthly budgets, list and compare Actual vs Budget with deltas; budget alerts when posting expenses
- Categories: list, rename, and merge categories across your history
- Import/Export: export your rows to CSV or import from CSV with simple de-duplication
- Recurring: define monthly recurrences and post due entries for a selected month

## Project Status & Roadmap
- [done] Milestone 1: Core CLI, users, JSON/CSV persistence
- [done] Milestone 2: Transactions + history viewer
- [done] Milestone 3: Reports with reusable filters
- [done] Milestone 4: Budgets, Categories, Import/Export, Recurring, ASCII charts
- [planned] Milestone 5: Pagination, minor UX polish, richer exports

## Repository Layout
- `main.py` — CLI entry point and menus
- `users.py` — registration, auth, PBKDF2 hashing
- `storage.py` — JSON/CSV helpers and field schema
- `transactions.py` — validation, model, CRUD helpers
- `reports.py` — filters, aggregations, money formatting, simple tables
- `backups.py` — ZIP backup/verify/restore with manifest
- `budgets.py` — set/list budgets and compute spend vs budget
- `categories.py` — list, rename, merge categories
- `import_export.py` — export to CSV; import with optional mapping + de-dup
- `recurring.py` — define/list/post monthly recurring entries
- `ascii_charts.py` — tiny helpers to draw horizontal bar charts
- `data/` — runtime state (JSON/CSV)
- `backups/` — generated ZIP archives (git-ignored)
- `logs/` — rolling app logs (git-ignored)

## Prerequisites
- Python 3.11+ (standard library only)

## Getting Started
1. (Optional) Create & activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Run the CLI:
   ```powershell
   python main.py
   ```
3. (Optional) Run the bundled sanity checks:
   ```powershell
   python tests_sanity.py
   ```

## CLI Overview
- Users `[1]`: Register, Login, Logout. Requires username, 3-letter currency (e.g., USD), and numeric PIN.
- Add transaction `[2]`: Type = `income`/`expense`; amount; category; ISO date; optional description; payment method in {Cash, Debit Card, Credit Card, Bank Transfer, Wallet}.
  - After saving an expense, if a monthly budget exists for the category, the CLI shows remaining/over-budget for that month.
- View transactions `[3]`: Fixed-width table of your rows, newest first, amount annotated with your currency.
- Reports `[4]`:
  - Balance summary (all time)
  - Category totals (with optional filters)
  - Monthly totals (with optional filters)
  - Filtered listing (shows rows)
  - ASCII chart: totals by category (optionally filtered)
- Save / Backup `[5]`: Create/list/verify/restore ZIP backups of `data/` files.
- Budgets `[6]`: Set or list monthly category budgets and view Budget vs Actual for a month (delta = budget - actual).
- Edit/Delete `[7]`: Edit or delete a transaction by ID.
- Category manager `[8]`: List, rename, or merge categories.
- Import/Export `[9]`: Export your transactions to CSV or import from CSV. Imports de-duplicate by (date, amount, description).
- Recurring `[10]`: Add/update recurrences (1..28 day-of-month), list them, and post due recurrences for a target month.

## Data Files
- Users: `data/users.json`
- Transactions: `data/transaction.csv`
- Budgets: `data/budgets.json`
- Recurrences: `data/recurrences.json`

## Import/Export
- CSV schema is defined by `storage.CSV_FIELDNAMES`:
  `transaction_id,user_id,type,amount,category,date,description,payment_method`
- Export writes your records in this schema, including headers.
- Import accepts a CSV and maps columns optionally via `column_map`. Rows missing critical fields or failing validation are skipped. De-duplication uses `(date, amount, description)` by default.

## Reports & Charts
- Filters: Start/End date, Payment method, Category, and Type are optional. Leave blank to skip.
- Totals render in simple tables; category totals can also render as an ASCII horizontal bar chart.

## Budgets
- Set monthly budgets per category (e.g., Food in 2025-10 = 1200.00).
- View budgets for a month and compare Actual vs Budget with deltas.
- When adding an expense, the CLI warns if you hit or exceed that category’s budget for the month and shows the remaining amount when applicable.

## Recurring
- Define recurring entries (income or expense) with category, amount, payment method, description, and day-of-month (1..28).
- Post due recurrences for a given month; existing identical rows are not duplicated.

## Logging
- All modules share `logutil.get_logger`; logs are written to stderr and `logs/app.log`.
- Control verbosity by setting `LOG_LEVEL` (e.g., `set LOG_LEVEL=DEBUG`).

## Backups
1. Make backup: `[5] -> [1]` creates a ZIP containing `users.json` and `transaction.csv` plus a manifest.
2. List backups: `[5] -> [2]` shows ZIPs in `backups/`.
3. Verify: `[5] -> [3]` validates hashes in the manifest vs file contents.
4. Restore: `[5] -> [4]` restores whitelisted files back into `data/` after confirmation.

## Troubleshooting
- Ensure the working directory is the project root before running `python main.py` so relative data paths resolve.
- Edit or remove files in `data/` for a clean slate.
- Check `logs/app.log` for detailed errors and flow traces.

