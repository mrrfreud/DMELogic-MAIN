import sqlite3

conn = sqlite3.connect('C:/Dme_Solutions/Data/orders.db')
cursor = conn.cursor()

# Check schema
cursor.execute('PRAGMA table_info(orders)')
cols = cursor.fetchall()
print('Orders table columns:')
for col in cols:
    print(f'  {col[1]} ({col[2]})')

print('\n' + '='*50)

# Check sample orders
cursor.execute('SELECT id, patient_id, patient_last_name, patient_first_name FROM orders LIMIT 5')
orders = cursor.fetchall()
print(f'\nSample orders (showing patient_id):')
for order in orders:
    print(f'  Order {order[0]}: patient_id={order[1]}, name={order[2]}, {order[3]}')

print('\n' + '='*50)

# Check BRIGHTLIN DOLMAN orders
cursor.execute("""
    SELECT id, patient_id, patient_last_name, patient_first_name, rx_date 
    FROM orders 
    WHERE patient_last_name = 'DOLMAN' AND patient_first_name = 'BRIGHTLIN'
""")
dolman_orders = cursor.fetchall()
print(f'\nBRIGHTLIN DOLMAN orders: {len(dolman_orders)} found')
for order in dolman_orders:
    print(f'  Order {order[0]}: patient_id={order[1]}, rx_date={order[4]}')

conn.close()
