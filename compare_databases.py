import sqlite3

print("="*70)
print("CHECKING C:/Dme_Solutions/Data/orders.db")
print("="*70)

conn1 = sqlite3.connect('C:/Dme_Solutions/Data/orders.db')
cursor1 = conn1.cursor()

cursor1.execute('SELECT COUNT(*) FROM orders')
count1 = cursor1.fetchone()[0]
print(f'Total orders: {count1}')

cursor1.execute('''
    SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob, rx_date
    FROM orders 
    WHERE id = 84
''')
order1 = cursor1.fetchone()
if order1:
    print(f'\nOrder 84 EXISTS:')
    print(f'  patient_id: {order1[1]}')
    print(f'  Name: {order1[2]}, {order1[3]}')
    print(f'  DOB: {order1[4]}')
    print(f'  RX Date: {order1[5]}')
    
    # Get items
    cursor1.execute('SELECT hcpcs_code, description FROM order_items WHERE order_id = 84')
    items = cursor1.fetchall()
    print(f'  Items: {len(items)}')
    for item in items:
        print(f'    - {item[0]}: {item[1]}')
else:
    print('\nOrder 84 NOT FOUND')

conn1.close()

print("\n" + "="*70)
print("CHECKING C:/FaxManagerData/Data/orders.db")
print("="*70)

conn2 = sqlite3.connect('C:/FaxManagerData/Data/orders.db')
cursor2 = conn2.cursor()

cursor2.execute('SELECT COUNT(*) FROM orders')
count2 = cursor2.fetchone()[0]
print(f'Total orders: {count2}')

cursor2.execute('''
    SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob, rx_date
    FROM orders 
    WHERE id = 84
''')
order2 = cursor2.fetchone()
if order2:
    print(f'\nOrder 84 EXISTS:')
    print(f'  patient_id: {order2[1]}')
    print(f'  Name: {order2[2]}, {order2[3]}')
    print(f'  DOB: {order2[4]}')
else:
    print('\nOrder 84 NOT FOUND')

conn2.close()
