import sqlite3
conn = sqlite3.connect('orders.db')
tables = conn.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
print('Tables in orders.db:')
for t in tables:
    print(f"  - {t[0]}")
conn.close()
