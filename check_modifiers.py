"""Check if modifiers are being stored and retrieved correctly."""

import sqlite3
from pathlib import Path

DB_PATH = r"C:\FaxManagerData\Data\dmelogic.db"

# Connect to database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# List tables
print("📋 Tables in database:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n" + "="*60)

# Check order_items schema
print("\n📐 order_items schema:")
try:
    cur.execute("PRAGMA table_info(order_items)")
    cols = cur.fetchall()
    for col in cols:
        print(f"  {col[1]:20} {col[2]:10} {'NOT NULL' if col[3] else ''}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "="*60)

# Check data in order 66
print("\n📦 Order 66 items:")
try:
    cur.execute("""
        SELECT id, hcpcs_code, description, is_rental, 
               modifier1, modifier2, modifier3, modifier4
        FROM order_items 
        WHERE order_id = 66
    """)
    items = cur.fetchall()
    
    if not items:
        print("  ⚠️  No items found for order 66")
    else:
        for item in items:
            print(f"\n  Item {item[0]}:")
            print(f"    HCPCS: {item[1]}")
            print(f"    Description: {item[2]}")
            print(f"    is_rental: {item[3]}")
            print(f"    modifier1: {item[4]}")
            print(f"    modifier2: {item[5]}")
            print(f"    modifier3: {item[6]}")
            print(f"    modifier4: {item[7]}")
            
except Exception as e:
    print(f"  ❌ Error: {e}")

conn.close()
