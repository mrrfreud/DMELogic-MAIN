"""Apply refill tracking indexes directly"""
import sqlite3

conn = sqlite3.connect('orders.db')

print("🔧 Creating refill tracking indexes...\n")

# Index 1: Refill tracking on order_items
print("Creating idx_order_items_refill_tracking...")
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_order_items_refill_tracking
    ON order_items(last_filled_date, day_supply, refills)
    WHERE last_filled_date IS NOT NULL
      AND last_filled_date != ''
      AND CAST(refills AS INTEGER) > 0
""")
print("✅ idx_order_items_refill_tracking created")

# Index 2: Patient name sorting on orders
print("\nCreating idx_orders_patient_name...")
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_orders_patient_name
    ON orders(patient_last_name, patient_first_name)
""")
print("✅ idx_orders_patient_name created")

conn.commit()

# Verify
result = conn.execute("""
    SELECT name, sql 
    FROM sqlite_master 
    WHERE type='index' 
    AND name LIKE 'idx_%'
""").fetchall()

print("\n📊 ALL CUSTOM INDEXES IN orders.db:\n")
for name, sql in result:
    print(f"✅ {name}")
    if sql:
        print(f"   {sql}\n")

conn.close()
print("✅ Refill tracking indexes active!")
