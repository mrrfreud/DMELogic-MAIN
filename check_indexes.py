"""Check if refill tracking indexes exist in orders.db"""
import sqlite3

conn = sqlite3.connect('orders.db')
cur = conn.cursor()

# Check for refill tracking indexes
result = cur.execute("""
    SELECT name, sql 
    FROM sqlite_master 
    WHERE type='index' 
    AND name IN ('idx_order_items_refill_tracking', 'idx_orders_patient_name')
""").fetchall()

if result:
    print("✅ INDEXES FOUND:\n")
    for name, sql in result:
        print(f"Index: {name}")
        print(f"SQL: {sql}\n")
else:
    print("❌ NO INDEXES FOUND - Migration005 has not been applied yet")

# Check schema_version
version = cur.execute("SELECT MAX(version) FROM schema_version WHERE db_name = 'orders.db'").fetchone()[0]
print(f"\nCurrent schema version: {version}")

conn.close()
