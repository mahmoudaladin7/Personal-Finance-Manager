# Personal Finance Manager (Console Edition)

A lightweight, terminal-based companion that lets you register users, authenticate with a PIN, and store personal finance transactions locally without any external dependencies. Data stays on disk in JSON/CSV files, so it works completely offline and is easy to back up.

> Project status: Milestone 3 (reporting hub + filters) is now in place; advanced exports and automations are up next.

## Features
- Interactive console menu for logging in, switching users, and exiting safely
- Secure user management with PBKDF2 PIN hashing and validation helpers in `users.py`
- JSON-backed user storage plus CSV transaction history via `storage.py`
- Validated transaction capture (type, amount, category, ISO date, payment method) with auto-generated IDs
- Currency-aware transaction viewer that renders a fixed-width table per user
- Reporting hub with balance summaries, category totals, month-over-month trends, and filtered listings
- Demo data seeding plus backup helpers so you can explore the workflow quickly

## Project Status & Roadmap
- [done] Milestone 1: Core CLI shell, user registration/authentication, JSON/CSV persistence helpers
- [done] Milestone 2: Transaction capture workflow + basic history viewer (sorted, currency aware)
- [done] Milestone 3: Reporting hub with reusable filters + monthly/category summaries
- [planned] Milestone 4: Advanced exports, pagination, and automated backups

## Repository Layout
- `main.py` - CLI entry point, menus, and demo backup routine
- `users.py` - validation, registration, and authentication logic
- `storage.py` - JSON/CSV utilities shared by the app
- `transactions.py` - validation helpers, dataclass model, persistence utilities
- `data/` - runtime state (`users.json`, `transaction.csv`)
- `backups/` - safe place to write exports or snapshots (git-ignored)

## Prerequisites
- Python 3.11+ (only standard library modules are used)

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

## Usage Tips
- **Register**: Choose a username (letters/digits/_/-) plus a 3-letter currency code and a numeric PIN (4-12 digits). Records are stored in `data/users.json`.
- **Login**: Authenticate with username + PIN. Successful logins populate `CURRENT_USER` and display currency info.
- **Add transaction** (`[2]`): Once logged in, supply type (`income`/`expense`), amount (validated `Decimal`), category, ISO date, optional description, and one of the supported payment methods. Entries are validated via `transactions.create_transaction` before being saved with auto-incremented IDs.
- **View transactions** (`[3]`): Lists the current user's history in a fixed-width table, sorted newest-first and annotated with the user's currency.
- **Backup demo data** (`[5]`): Populates `users.json` with a demo account (if empty) and appends a sample transaction to `data/transaction.csv`.
- **Reports** (`[4]`): Jump into summaries (balance, category, monthly) or print a filtered listing. Leave any filter input blank to skip that constraint.

## Reports & Filters
- **Balance summary** totals lifetime income, expenses, and net using the current user's rows.
- **Category totals** and **Monthly totals** accept optional filters (start/end date, payment method, category, and type). Leave inputs blank to skip a filter.
- **Filtered listing** reuses the same filters but prints the matching rows in a fixed-width table so you can audit exact entries.
- All reports share a helper in `reports.py`, so parsing/validation logic stays consistent across features.

Demo credentials (added by the backup step): `Demo / 1234` (USD).

## Data & Backups
- Users: `data/users.json` (list of dicts; hashed PINs under `auth`)
- Transactions: `data/transaction.csv` (CSV headers defined in `storage.py`)
- Backups: `backups/` is git-ignored so local exports stay private

## Roadmap Ideas
1. Paginated transaction viewer with filters (date range, category, payment method)
2. Visual dashboards (sparklines/ASCII charts) and richer CSV/Excel export options
3. Automated backup/restore commands and better error handling
4. Optional data import/export (JSON ? CSV) for interoperability

## Troubleshooting
- Delete or edit `data/users.json` / `transaction.csv` if you want a clean slate.
- Ensure the working directory is the project root before running `python main.py` so relative data paths resolve correctly.
