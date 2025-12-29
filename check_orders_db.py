"""Check orders.db for order 66."""
import sqlite3

conn = sqlite3.connect(r"C:\FaxManagerData\Data\orders.db")
cur = conn.cursor()

# List tables
print("📋 Tables:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for table in cur.fetchall():
    print(f"  - {table[0]}")

# Check order_items
print("\n📦 Order 66 items:")
cur.execute("""
    SELECT id, hcpcs_code, description, is_rental,
           modifier1, modifier2, modifier3, modifier4
    FROM order_items
    WHERE order_id = 66
""")

items = cur.fetchall()
if not items:
    print("  ⚠️  No items found")
else:
    for item in items:
        print(f"\n  Item {item[0]}:")
        print(f"    HCPCS: {item[1]}")
        print(f"    Description: {item[2]}")
        print(f"    is_rental: {item[3]}")
        print(f"    Modifiers: {[item[4], item[5], item[6], item[7]]}")

conn.close()
