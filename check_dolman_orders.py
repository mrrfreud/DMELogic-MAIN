import sqlite3

conn = sqlite3.connect('C:/FaxManagerData/Data/orders.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob, rx_date
    FROM orders 
    WHERE patient_last_name = ? AND patient_first_name = ?
''', ('DOLMAN', 'BRIGHTLIN'))

orders = cursor.fetchall()
print(f'\nOrders for BRIGHTLIN DOLMAN in C:/FaxManagerData/Data/orders.db: {len(orders)}')
for order in orders:
    print(f'  Order {order[0]}: patient_id={order[1]}, DOB={order[4]}, rx_date={order[5]}')

conn.close()

# Also check the patients DB
conn2 = sqlite3.connect('C:/FaxManagerData/Data/patients.db')
cursor2 = conn2.cursor()
cursor2.execute('SELECT id, last_name, first_name, dob FROM patients WHERE last_name = ? AND first_name = ?', ('DOLMAN', 'BRIGHTLIN'))
patient = cursor2.fetchone()
if patient:
    print(f'\nPatient record: id={patient[0]}, DOB={patient[3]}')
else:
    print('\nNo patient record found!')
conn2.close()
