"""Check database structure."""
import sqlite3

conn = sqlite3.connect(r"C:\FaxManagerData\Data\dmelogic.db")
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()

print(f"Found {len(tables)} tables:\n")
for table in tables:
    print(f"  📁 {table[0]}")
    
    # Show row count
    cur.execute(f"SELECT COUNT(*) FROM [{table[0]}]")
    count = cur.fetchone()[0]
    print(f"     Rows: {count}")
    
    # Show a few column names
    cur.execute(f"PRAGMA table_info([{table[0]}])")
    cols = cur.fetchall()
    col_names = [c[1] for c in cols[:5]]
    if len(cols) > 5:
        col_names.append(f"... ({len(cols)-5} more)")
    print(f"     Columns: {', '.join(col_names)}")
    print()

conn.close()
