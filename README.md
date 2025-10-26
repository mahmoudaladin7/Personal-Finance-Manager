# Personal Finance Manager (Console Edition)

A lightweight, terminal-based companion that lets you register users, authenticate with a PIN, and store personal finance transactions locally without any external dependencies. Data stays on disk in JSON/CSV files, so it works completely offline and is easy to back up.

> Project status: This repository captures the first milestone (user management + storage foundation). Transaction entry, reporting, and other advanced features are still in progress.

## Features
- Interactive console menu for logging in, switching users, and exiting safely
- Secure user management with PBKDF2 PIN hashing and validation helpers in `users.py`
- JSON-backed user storage plus CSV transaction history via `storage.py`
- Demo data seeding and backup helpers so you can explore the workflow quickly
- Clear extension points for adding transactions, viewing history, and generating reports (to be built next)

## Project Status & Roadmap
- [done] Milestone 1: Core CLI shell, user registration/authentication, JSON/CSV persistence helpers
- [up next] Milestone 2: Transaction capture workflow (amount/category/payment validation)
- [planned] Milestone 3: Transaction browsing (filters, pagination, exports)
- [planned] Milestone 4: Reports (per-user summaries, income vs expense charts) and automated backups

## Repository Layout
- `main.py` - CLI entry point, menus, and demo backup routine
- `users.py` - validation, registration, and authentication logic
- `storage.py` - JSON/CSV utilities shared by the app
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
- **Backup demo data**: Option `[5] Save / Backup` populates `users.json` with a demo account (if empty) and appends a sample transaction to `data/transaction.csv`.
- **Next steps**: Menu actions `[2] Add transaction`, `[3] View transactions`, and `[4] Reports` are placeholders, so extend `main.py` using the helpers in `storage.py` to implement them.

Demo credentials (added by the backup step): `Demo / 1234` (USD).

## Data & Backups
- Users: `data/users.json` (list of dicts; hashed PINs under `auth`)
- Transactions: `data/transaction.csv` (CSV headers defined in `storage.py`)
- Backups: `backups/` is git-ignored so local exports stay private

## Roadmap Ideas
1. Implement transaction capture (amount validation, categories, payment methods)
2. Paginated transaction viewer with filters (date range, category, payment method)
3. Summary reports (per-user balance, income vs expenses, export to CSV)
4. Automated backup/restore commands and better error handling

## Troubleshooting
- Delete or edit `data/users.json` / `transaction.csv` if you want a clean slate.
- Ensure the working directory is the project root before running `python main.py` so relative data paths resolve correctly.
