"""Apply Migration005 to add refill tracking indexes"""
import sqlite3
from dmelogic.db.migrations import Migration005_AddRefillTrackingIndexes

# Connect to orders.db
conn = sqlite3.connect('orders.db')

# Create schema_version table if it doesn't exist
conn.execute("""
    CREATE TABLE IF NOT EXISTS schema_version (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version INTEGER NOT NULL,
        db_name TEXT NOT NULL,
        description TEXT,
        applied_at TEXT DEFAULT (datetime('now'))
    )
""")

# Check current version
cur = conn.cursor()
current_version = cur.execute(
    "SELECT COALESCE(MAX(version), 0) FROM schema_version WHERE db_name = 'orders.db'"
).fetchone()[0]

print(f"Current orders.db version: {current_version}")

# Apply Migration005 if not already applied
if current_version < 5:
    print("\n🔧 Applying Migration005_AddRefillTrackingIndexes...")
    
    migration = Migration005_AddRefillTrackingIndexes()
    
    # Run the migration
    migration.up(conn)
    
    # Record in schema_version
    conn.execute("""
        INSERT INTO schema_version (version, db_name, description)
        VALUES (?, ?, ?)
    """, (5, 'orders.db', 'Add indexes for refill tracking'))
    
    conn.commit()
    print("✅ Migration005 applied successfully!")
else:
    print(f"✅ Migration005 already applied (current version: {current_version})")

# Verify indexes now exist
result = conn.execute("""
    SELECT name, sql 
    FROM sqlite_master 
    WHERE type='index' 
    AND name IN ('idx_order_items_refill_tracking', 'idx_orders_patient_name')
""").fetchall()

print("\n📊 INDEXES IN orders.db:\n")
for name, sql in result:
    print(f"✅ {name}")
    print(f"   {sql}\n")

conn.close()
print("\n✅ Refill tracking indexes are now active!")
