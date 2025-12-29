import sqlite3

conn = sqlite3.connect('C:/Dme_Solutions/Data/orders.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM orders WHERE id = 85')
row = cursor.fetchone()

print('Columns in order 85:')
if row:
    print(list(row.keys()))
    print('\nValues for name fields:')
    print(f'  patient_last_name: {row["patient_last_name"] if "patient_last_name" in row.keys() else "NOT IN ROW"}')
    print(f'  patient_first_name: {row["patient_first_name"] if "patient_first_name" in row.keys() else "NOT IN ROW"}')
else:
    print('Order 85 not found')

conn.close()
