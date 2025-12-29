"""Check which database file is being used."""
from dmelogic.db.base import resolve_db_path, get_connection
import os

folder_path = r"C:\FaxManagerData\Data"

# Check which path is resolved
db_path = resolve_db_path("orders.db", folder_path=folder_path)
print(f"Resolved DB path: {db_path}")
print(f"File exists: {os.path.exists(db_path)}")
print(f"File size: {os.path.getsize(db_path) if os.path.exists(db_path) else 'N/A'}")

# Try dmelogic.db too
dmelogic_path = resolve_db_path("dmelogic.db", folder_path=folder_path)
print(f"\nDMELogic DB path: {dmelogic_path}")
print(f"File exists: {os.path.exists(dmelogic_path)}")
print(f"File size: {os.path.getsize(dmelogic_path) if os.path.exists(dmelogic_path) else 'N/A'}")

# Check what's actually in the folder
print(f"\nFiles in {folder_path}:")
if os.path.exists(folder_path):
    for f in os.listdir(folder_path):
        if f.endswith('.db'):
            full_path = os.path.join(folder_path, f)
            size = os.path.getsize(full_path)
            print(f"  - {f} ({size:,} bytes)")
else:
    print("  Folder doesn't exist!")
