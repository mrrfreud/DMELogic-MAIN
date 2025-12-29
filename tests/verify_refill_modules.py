"""
verify_refill_modules.py — Simple verification that refill modules exist and are importable.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("REFILL SYSTEM MODULE VERIFICATION")
print("=" * 70)

# Test 1: Check refills.py exists and imports
try:
    from dmelogic.db.refills import fetch_refills_due, RefillRow
    print("[OK] dmelogic.db.refills module imports successfully")
    print("  - fetch_refills_due() function available")
    print("  - RefillRow TypedDict available")
except ImportError as e:
    print(f"[FAIL] Failed to import refills module: {e}")
    sys.exit(1)

# Test 2: Check orders.py refill helpers
try:
    from dmelogic.db.orders import (
        fetch_order_item_with_header,
        create_refill_order_from_source,
        mark_refill_used,
    )
    print("\n[OK] dmelogic.db.orders refill helpers available")
    print("  - fetch_order_item_with_header()")
    print("  - create_refill_order_from_source()")
    print("  - mark_refill_used()")
except ImportError as e:
    print(f"[FAIL] Failed to import orders refill helpers: {e}")
    sys.exit(1)

# Test 3: Check services directory
try:
    from dmelogic.services.refill_service import process_refills, process_refills_grouped
    print("\n[OK] dmelogic.services.refill_service module imports successfully")
    print("  - process_refills() function available")
    print("  - process_refills_grouped() function available")
except ImportError as e:
    print(f"[FAIL] Failed to import refill_service: {e}")
    sys.exit(1)

# Test 4: Check UnitOfWork availability
try:
    from dmelogic.db.base import UnitOfWork
    print("\n[OK] dmelogic.db.base.UnitOfWork available")
except ImportError as e:
    print(f"[FAIL] Failed to import UnitOfWork: {e}")
    sys.exit(1)

# Test 5: Check migrations
try:
    from dmelogic.db.migrations import ORDER_MIGRATIONS
    migration_count = len(ORDER_MIGRATIONS)
    print(f"\n[OK] Order migrations available ({migration_count} migrations)")
    
    # Check for refill tracking migration
    refill_migration = [m for m in ORDER_MIGRATIONS if "refill" in m.description.lower()]
    if refill_migration:
        print(f"  - Found refill tracking index migration: {refill_migration[0].description}")
except ImportError as e:
    print(f"[FAIL] Failed to import migrations: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL REFILL SYSTEM MODULES VERIFIED [SUCCESS]")
print("=" * 70)

print("\n" + "=" * 70)
print("ARCHITECTURE SUMMARY")
print("=" * 70)
print("""
Refill Tracking System Structure:

1. DATA LAYER (dmelogic/db/)
   └── refills.py
       - fetch_refills_due(start, end, today) → List[RefillRow]
       - Computes next_refill_due from last_filled_date + day_supply
       - Filters by date range and refills > 0

2. REPOSITORY HELPERS (dmelogic/db/orders.py)
   └── Refill-specific functions:
       - fetch_order_item_with_header(item_rowid, conn) → Dict
       - create_refill_order_from_source(src, fill_date, conn) → order_id
       - mark_refill_used(item_rowid, fill_date, conn) → None

3. SERVICE LAYER (dmelogic/services/)
   └── refill_service.py
       - process_refills(item_ids, fill_date) → count
       - process_refills_grouped(item_ids, fill_date) → dict
       - Uses UnitOfWork for transactional consistency

4. PERFORMANCE (dmelogic/db/migrations.py)
   └── Migration005_AddRefillTrackingIndexes
       - Index on order_items(last_filled_date, day_supply, refills)
       - Index on orders(patient_last_name, patient_first_name)

UI INTEGRATION PATTERN:

# Generate refill list
from dmelogic.db.refills import fetch_refills_due

def on_generate_clicked(self):
    rows = fetch_refills_due(start_date, end_date, today, folder_path)
    self.display_in_grid(rows)

# Create orders for selected
from dmelogic.services.refill_service import process_refills

def on_create_orders_clicked(self):
    item_ids = self.get_selected_rowids()
    count = process_refills(item_ids, fill_date, folder_path)
    self.refresh_grid()
""")
print("=" * 70)
