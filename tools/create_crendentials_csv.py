# tools/create_credentials_csv.py
import csv
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "credentials.csv"

ROWS = [
    # case, username, password, expected
    # ✅ Valid user (Sauce Demo standard)
    {"case": "valid_standard_user", "username": "standard_user", "password": "secret_sauce", "expected": "success"},
    # ❌ Locked out user
    {"case": "locked_out_user", "username": "locked_out_user", "password": "secret_sauce", "expected": "locked"},
    # ❌ Completely wrong
    {"case": "invalid_combo", "username": "wrong_user", "password": "wrongpass", "expected": "invalid"},
    # ❌ Empty username
    {"case": "empty_username", "username": "", "password": "secret_sauce", "expected": "empty_username"},
    # ❌ Empty password
    {"case": "empty_password", "username": "standard_user", "password": "", "expected": "empty_password"},
]

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def write_csv(path: Path):
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case", "username", "password", "expected"])
        writer.writeheader()
        writer.writerows(ROWS)
    print(f"✅ Wrote {len(ROWS)} rows to {path}")

if __name__ == "__main__":
    write_csv(DEFAULT_PATH)