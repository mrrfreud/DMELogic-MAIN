import sqlite3

# Check billing DB tables
conn = sqlite3.connect(r"C:\ProgramData\DMELogic\Data\billing.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("=== Billing DB Tables ===")
for r in cur.fetchall():
    print(r)
    # Show schema for each
    cur2 = conn.cursor()
    cur2.execute(f"PRAGMA table_info({r[0]})")
    for col in cur2.fetchall():
        print(f"  {col}")
conn.close()

# Check how existing orders have amounts
conn2 = sqlite3.connect(r"C:\ProgramData\DMELogic\Data\orders.db")
cur2 = conn2.cursor()
print("\n=== Orders with non-empty total (sample) ===")
cur2.execute("SELECT order_id, hcpcs_code, qty, cost_ea, total FROM order_items WHERE total IS NOT NULL AND total != '' LIMIT 10")
for r in cur2.fetchall():
    print(r)

print("\n=== Inventory items with retail_price ===")
conn3 = sqlite3.connect(r"C:\ProgramData\DMELogic\Data\inventory.db")
cur3 = conn3.cursor()
cur3.execute("SELECT item_id, hcpcs_code, description, retail_price, cost FROM inventory WHERE hcpcs_code LIKE 'T4530%' LIMIT 10")
for r in cur3.fetchall():
    print(r)

print("\n=== Any T45xx items ===")
cur3.execute("SELECT item_id, hcpcs_code, description, retail_price, cost FROM inventory WHERE hcpcs_code LIKE 'T45%' LIMIT 10")
for r in cur3.fetchall():
    print(r)

print("\n=== Inventory HCPCS sample with prices ===")
cur3.execute("SELECT DISTINCT substr(hcpcs_code, 1, 5) as hcpcs, retail_price FROM inventory WHERE retail_price > 0 GROUP BY substr(hcpcs_code, 1, 5) LIMIT 20")
for r in cur3.fetchall():
    print(r)

conn2.close()
conn3.close()
