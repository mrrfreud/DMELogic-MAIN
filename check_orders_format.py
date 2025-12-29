import sqlite3

conn = sqlite3.connect('C:/FaxManagerData/Data/orders.db')
cursor = conn.cursor()

# Check total orders
cursor.execute('SELECT COUNT(*) FROM orders')
total = cursor.fetchone()[0]
print(f'Total orders in C:/FaxManagerData/Data/orders.db: {total}')

# Check a few sample orders with their patient_dob format
cursor.execute('SELECT id, patient_last_name, patient_first_name, patient_dob, patient_id FROM orders LIMIT 10')
samples = cursor.fetchall()
print('\nSample orders:')
for s in samples:
    print(f'  Order {s[0]}: {s[1]}, {s[2]} | DOB: "{s[3]}" | patient_id: {s[4]}')

# Try to find DOLMAN with different DOB formats
print('\n--- Checking for DOLMAN with various DOB formats ---')
cursor.execute('''
    SELECT id, patient_dob, patient_id 
    FROM orders 
    WHERE patient_last_name = 'DOLMAN'
''')
dolman = cursor.fetchall()
print(f'Any DOLMAN orders: {len(dolman)}')
for d in dolman:
    print(f'  Order {d[0]}: DOB="{d[1]}" patient_id={d[2]}')

conn.close()
