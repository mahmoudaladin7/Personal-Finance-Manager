from  decimal import Decimal
from pathlib import Path
import sys
from storage import read_json, write_json, append_transactions_csv, read_transactions_csv
from users import register_user, authenticate



CURRENT_USER: dict | None = None

App_ROOT = Path(__file__).resolve().parent
Data_DIR= App_ROOT / 'data'
BACKUP_DIR = App_ROOT / "backups"
USERS_JSON = Data_DIR / "users.json"
TXNS_CSV = Data_DIR / 'transaction.csv'

SUPPOURTED_TYPES = ("income", "expenses")
SUPPORTED_METHODS = ("Cash", "Debit Card", "Credit Card", "Bank Transfer", "Wallet")


def print_banner()-> None:

    print("=" * 58)
    print("💰 Personal Finance Manager (Console Edition)")
    print("=" * 58)

def main_menu() -> None:
   global CURRENT_USER 



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
            print("TODO: implement add transaction")
        elif choice == "3":
            print("TODO: implement view transactions")
        elif choice == "4":
            print("TODO: implement reports")
        elif choice == "5":
    
            demo_users = read_json(USERS_JSON)
            if not demo_users:
                demo_users = [{"user_id": "U001", "name": "Demo", "password": "1234", "currency": "USD"}]
                write_json(USERS_JSON, demo_users)
                print("Created users.json with a demo user.")
            else:
                print(f"users.json already has {len(demo_users)} user(s).")
            append_transactions_csv(TXNS_CSV, [{
                "transaction_id": "T001",
                "user_id": "U001",
                "type": "expense",
                "amount": Decimal("12.50"),   
                "category": "Food",
                "date": "2025-10-12",
                "description": "Test lunch",
                "payment_method": "Credit Card",
    }])
            rows = read_transactions_csv(TXNS_CSV)
            print(f"transactions.csv now has {len(rows)} row(s).")
        else:
            print("⚠️ Invalid choice. Try again.")


if __name__ == "__main__":
    print_banner()
    main_menu()