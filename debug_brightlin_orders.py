import sqlite3

# Check the orders database for BRIGHTLIN
conn = sqlite3.connect('C:/FaxManagerData/Data/orders.db')
cursor = conn.cursor()

# Look for order 84
cursor.execute('''
    SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob, rx_date
    FROM orders 
    WHERE id = 84
''')
order = cursor.fetchone()
if order:
    print(f'Order 84 details:')
    print(f'  patient_id: {order[1]}')
    print(f'  Name: {order[2]}, {order[3]}')
    print(f'  DOB: {order[4]}')
    print(f'  RX Date: {order[5]}')
else:
    print('Order 84 not found')

print('\n' + '='*60)

# Check patients database for BRIGHTLIN
conn2 = sqlite3.connect('C:/FaxManagerData/Data/patients.db')
cursor2 = conn2.cursor()
cursor2.execute('SELECT id, last_name, first_name, dob FROM patients WHERE last_name = ? AND first_name = ?', 
                ('DOLMAN', 'BRIGHTLIN'))
patient = cursor2.fetchone()
if patient:
    print(f'\nBRIGHTLIN DOLMAN in patients.db:')
    print(f'  patient_id: {patient[0]}')
    print(f'  DOB: {patient[3]}')
else:
    print('\nBRIGHTLIN DOLMAN not found in patients.db')

print('\n' + '='*60)

# Search for all orders with BRIGHTLIN (any case)
cursor.execute('''
    SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob
    FROM orders 
    WHERE UPPER(patient_first_name) LIKE '%BRIGHTLIN%' OR UPPER(patient_last_name) LIKE '%DOLMAN%'
''')
orders = cursor.fetchall()
print(f'\nAll orders matching BRIGHTLIN or DOLMAN: {len(orders)}')
for o in orders:
    print(f'  Order {o[0]}: patient_id={o[1]}, Name={o[2]}, {o[3]}, DOB={o[4]}')

conn.close()
conn2.close()
