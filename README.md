# Personal Finance Manager (Console Edition)

A lightweight, terminal-based companion that lets you register users, authenticate with a PIN, and store personal finance transactions locally without any external dependencies. Data stays on disk in JSON/CSV files, so it works completely offline and is easy to back up.

> Project status: Milestone 2 (transaction capture + history viewing) is now in place; reports and advanced analytics are up next.

## Features
- Interactive console menu for logging in, switching users, and exiting safely
- Secure user management with PBKDF2 PIN hashing and validation helpers in `users.py`
- JSON-backed user storage plus CSV transaction history via `storage.py`
- Validated transaction capture (type, amount, category, ISO date, payment method) with auto-generated IDs
- Currency-aware transaction viewer that renders a fixed-width table per user
- Demo data seeding and backup helpers so you can explore the workflow quickly

## Project Status & Roadmap
- [done] Milestone 1: Core CLI shell, user registration/authentication, JSON/CSV persistence helpers
- [done] Milestone 2: Transaction capture workflow + basic history viewer (sorted, currency aware)
- [planned] Milestone 3: Enhanced browsing (filters, pagination, exports)
- [planned] Milestone 4: Reports (per-user summaries, income vs expense charts) and automated backups

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
- **Reports** (`[4]`): Placeholder for upcoming analytics; contribute ideas in the Roadmap section.

Demo credentials (added by the backup step): `Demo / 1234` (USD).

## Data & Backups
- Users: `data/users.json` (list of dicts; hashed PINs under `auth`)
- Transactions: `data/transaction.csv` (CSV headers defined in `storage.py`)
- Backups: `backups/` is git-ignored so local exports stay private

## Roadmap Ideas
1. Paginated transaction viewer with filters (date range, category, payment method)
2. Summary reports (per-user balance, income vs expenses, export to CSV)
3. Automated backup/restore commands and better error handling
4. Optional data import/export (JSON ? CSV) for interoperability

## Troubleshooting
- Delete or edit `data/users.json` / `transaction.csv` if you want a clean slate.
- Ensure the working directory is the project root before running `python main.py` so relative data paths resolve correctly.
