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
- Backup center with ZIP snapshots, manifest-based verification, and selective restore tools
- Demo data seeding plus helper scripts so you can explore the workflow quickly

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
- `reports.py` - reporting filters, aggregations, and shared console formatting
- `backups.py` - ZIP backup helpers with SHA-256 manifests plus list/verify/restore utilities
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
3. (Optional) Run the bundled sanity checks:
   ```powershell
   python tests_sanity.py
   ```

## Usage Tips
- **Register**: Choose a username (letters/digits/_/-) plus a 3-letter currency code and a numeric PIN (4-12 digits). Records are stored in `data/users.json`.
- **Login**: Authenticate with username + PIN. Successful logins populate `CURRENT_USER` and display currency info.
- **Add transaction** (`[2]`): Once logged in, supply type (`income`/`expense`), amount (validated `Decimal`), category, ISO date, optional description, and one of the supported payment methods. Entries are validated via `transactions.create_transaction` before being saved with auto-incremented IDs.
- **View transactions** (`[3]`): Lists the current user's history in a fixed-width table, sorted newest-first and annotated with the user's currency.
- **Reports** (`[4]`): Jump into summaries (balance, category, monthly) or print a filtered listing. Leave any filter input blank to skip that constraint.
- **Save / Backup** (`[5]`): Opens the backup center so you can create a new ZIP snapshot, list existing backups, verify their manifests, or restore data safely.

## Reports & Filters
- **Balance summary** totals lifetime income, expenses, and net using the current user's rows.
- **Category totals** and **Monthly totals** accept optional filters (start/end date, payment method, category, and type). Leave inputs blank to skip a filter.
- **Filtered listing** reuses the same filters but prints the matching rows in a fixed-width table so you can audit exact entries.
- All reports share a helper in `reports.py`, so parsing/validation logic stays consistent across features.

Demo credentials (added by the backup step): `Demo / 1234` (USD).

## Logging
- Logging is configured through `logutil.get_logger`; all modules share the same formatter and write both to stderr and `logs/app.log`.
- Control verbosity with the `LOG_LEVEL` environment variable (`DEBUG`, `INFO`, etc.), e.g. `set LOG_LEVEL=DEBUG` before running the CLI.
- Key flows now emit structured messages:
  - Transaction creation (`transactions.create_transaction`) traces the incoming payload at debug level and records persisted IDs at info level.
  - Backup routines (`backups.create_backup` / `verify_backup`) log each ZIP created, verification run, and any integrity failures.
- Inspect `logs/app.log` when troubleshooting or verifying that actions (transactions, backups) completed successfully.

## Data & Backups
- Users: `data/users.json` (list of dicts; hashed PINs under `auth`)
- Transactions: `data/transaction.csv` (CSV headers defined in `storage.py`)
- Backups: `backups/` contains timestamped ZIP files (`backup-YYYYMMDD-HHMMSS.zip`) with `users.json`, `transactions.csv`, and a manifest that stores file sizes + SHA-256 hashes so integrity checks can run locally.

## Backup Workflow
1. **Make a backup**: Choose `[5] -> [1]` to generate a ZIP snapshot of `users.json` and `transactions.csv`. Files missing on disk are skipped automatically.
2. **List backups**: `[5] -> [2]` shows every ZIP in `backups/`, newest first, so you can pick one for verification or restore.
3. **Verify integrity**: `[5] -> [3]` re-computes SHA-256 hashes for each archived file and compares them with the manifest. Any mismatches or missing files are reported.
4. **Restore data**: `[5] -> [4]` lets you pick a ZIP, confirms the overwrite, and writes only the whitelisted files (`users.json`, `transactions.csv`) back into `data/`. Use this after verifying a backup or when moving machines.

## Roadmap Ideas
1. Paginated transaction viewer with filters (date range, category, payment method)
2. Visual dashboards (sparklines/ASCII charts) and richer CSV/Excel export options
3. Automated backup/restore commands and better error handling
4. Optional data import/export (JSON ? CSV) for interoperability

## Troubleshooting
- Delete or edit `data/users.json` / `transaction.csv` if you want a clean slate.
- Ensure the working directory is the project root before running `python main.py` so relative data paths resolve correctly.
