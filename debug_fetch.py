"""Debug fetch_order_with_items to see what columns are returned."""
from dmelogic.db.base import get_connection
import sqlite3

conn = get_connection("orders.db", folder_path=r"C:\FaxManagerData\Data")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Fetch order items
cur.execute("SELECT * FROM order_items WHERE order_id = 66 ORDER BY id ASC")
item_rows = cur.fetchall()

print(f"Found {len(item_rows)} items\n")

for idx, row in enumerate(item_rows, 1):
    print(f"Item {idx}:")
    print(f"  Column names: {row.keys()}")
    print(f"  HCPCS: {row['hcpcs_code']}")
    print(f"  is_rental: {row['is_rental']}")
    print(f"  modifier1: {row['modifier1']}")
    print(f"  modifier2: {row['modifier2']}")
    print(f"  modifier3: {row['modifier3']}")
    print(f"  modifier4: {row['modifier4']}")
    print()

# Now try converting with our converter
from dmelogic.db.converters import row_to_order_item

print("\nConverting with row_to_order_item:")
for idx, row in enumerate(item_rows, 1):
    item = row_to_order_item(row)
    print(f"\nItem {idx}:")
    print(f"  HCPCS: {item.hcpcs_code}")
    print(f"  is_rental: {item.is_rental}")
    print(f"  modifiers: {item.modifiers}")
    print(f"  all_modifiers: {item.all_modifiers}")
    print(f"  modifier1: {item.modifier1}")
    print(f"  modifier2: {item.modifier2}")

conn.close()
