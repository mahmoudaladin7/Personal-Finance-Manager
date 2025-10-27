# tests_sanity.py
from __future__ import annotations

from pathlib import Path
from decimal import Decimal
import shutil
import tempfile

from users import validate_username, validate_currency, validate_pin, register_user, authenticate
from transactions import parse_money, create_transaction
from storage import read_json
from backups import BackupSpec, create_backup, list_backups, verify_backup, restore_backup

def test_validators():
    # username
    assert validate_username("Khalid") == "Khalid"
    try:
        validate_username("!")
        raise AssertionError("username with '!' should fail")
    except ValueError:
        pass

    # currency
    assert validate_currency("sar") == "SAR"
    try:
        validate_currency("S4R")
        raise AssertionError("currency with digit should fail")
    except ValueError:
        pass

    # pin
    assert validate_pin("1234") == "1234"
    for bad in ("12", "abcd", "1234567890123"):
        try:
            validate_pin(bad)
            raise AssertionError(f"pin {bad!r} should fail")
        except ValueError:
            pass

def test_money_parse():
    assert parse_money("12").compare(Decimal("12.00")) == 0
    assert parse_money("12.5").compare(Decimal("12.50")) == 0
    try:
        parse_money("+10")
        raise AssertionError("leading + should fail")
    except ValueError:
        pass
    try:
        parse_money("-1")
        raise AssertionError("negative amount should fail")
    except ValueError:
        pass

def test_user_and_backup_flow(tmpdir: Path):
    data_dir = tmpdir / "data"
    backups_dir = tmpdir / "backups"
    data_dir.mkdir()
    backups_dir.mkdir()

    users_json = data_dir / "users.json"
    users_json.write_text("[]", encoding="utf-8")

    # register + login
    u = register_user(users_json, "Tester", "USD", "1234")
    assert u["name"] == "Tester"
    assert authenticate(users_json, "Tester", "1234") is not None
    assert authenticate(users_json, "Tester", "9999") is None

    # backup
    spec = BackupSpec(backup_dir=backups_dir, files=[users_json])
    zp = create_backup(spec)
    assert zp.exists()
    ok, errs = verify_backup(zp)
    assert ok and not errs

    # simulate restore to a fresh directory
    data_dir2 = tmpdir / "restore_data"
    restored = restore_backup(zp, data_dir2, overwrite=True)
    assert (data_dir2 / "users.json").exists()
    assert read_json(data_dir2 / "users.json")[0]["name"] == "Tester"
    assert restored, "expected at least one restored file"

def run_all():
    print("Running sanity tests…")
    test_validators()
    test_money_parse()

    with tempfile.TemporaryDirectory() as td:
        test_user_and_backup_flow(Path(td))

    print("✅ All sanity tests passed.")

if __name__ == "__main__":
    run_all()
