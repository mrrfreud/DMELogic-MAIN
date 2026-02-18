import sqlite3

# Check inventory tables
conn = sqlite3.connect(r'C:\ProgramData\DMELogic\Data\inventory.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("=== Inventory DB Tables ===")
for r in cur.fetchall():
    print(r)

print("\n=== T4530 items ===")
cur.execute("SELECT item_id, hcpcs_code, description, retail_price, cost, item_number FROM inventory WHERE hcpcs_code='T4530' LIMIT 5")
for r in cur.fetchall():
    print(r)

print("\n=== All HCPCS with prices (sample) ===")
cur.execute("SELECT DISTINCT hcpcs_code, retail_price, cost FROM inventory WHERE retail_price > 0 LIMIT 20")
for r in cur.fetchall():
    print(r)
conn.close()

# Check orders DB for amount field
conn2 = sqlite3.connect(r'C:\ProgramData\DMELogic\Data\orders.db')
cur2 = conn2.cursor()
print("\n=== Orders tables ===")
cur2.execute("SELECT name FROM sqlite_master WHERE type='table'")
for r in cur2.fetchall():
    print(r)

print("\n=== Order items schema ===")
cur2.execute("PRAGMA table_info(order_items)")
for r in cur2.fetchall():
    print(r)

print("\n=== Orders schema (sample) ===")
cur2.execute("PRAGMA table_info(orders)")
for r in cur2.fetchall():
    print(r)

print("\n=== ORD-297 ===")
cur2.execute("SELECT * FROM orders WHERE order_id='ORD-297'")
rows = cur2.fetchall()
cols = [d[0] for d in cur2.description]
for row in rows:
    for c, v in zip(cols, row):
        print(f"  {c}: {v}")

print("\n=== ORD-297 items ===")
cur2.execute("SELECT * FROM order_items WHERE order_id='ORD-297'")
rows = cur2.fetchall()
if rows:
    cols = [d[0] for d in cur2.description]
    for row in rows:
        for c, v in zip(cols, row):
            print(f"  {c}: {v}")
        print()
else:
    print("  No items found in order_items table")

# Check if there's a fee_schedule or billing table
conn3 = sqlite3.connect(r'C:\ProgramData\DMELogic\Data\billing.db')
cur3 = conn3.cursor()
print("\n=== Billing DB tables ===")
cur3.execute("SELECT name FROM sqlite_master WHERE type='table'")
for r in cur3.fetchall():
    print(r)

# Check fee schedule if it exists
for table in ['fee_schedule', 'fees', 'pricing', 'hcpcs_fees', 'allowable']:
    try:
        cur3.execute(f"SELECT * FROM {table} LIMIT 3")
        print(f"\n=== {table} ===")
        cols = [d[0] for d in cur3.description]
        print(cols)
        for r in cur3.fetchall():
            print(r)
    except:
        pass
conn3.close()
