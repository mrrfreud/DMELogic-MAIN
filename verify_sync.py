import sqlite3

print("\n=== VERIFYING DATABASE SYNC ===")
conn = sqlite3.connect('C:/FaxManagerData/Data/orders.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM orders')
total = cursor.fetchone()[0]
print(f'Total orders in FaxManagerData: {total}')

cursor.execute('SELECT id, patient_last_name, patient_first_name, patient_dob FROM orders WHERE id = 84')
order = cursor.fetchone()
if order:
    print(f'Order 84: {order[1]}, {order[2]} (DOB: {order[3]})')
else:
    print('Order 84: NOT FOUND')

conn.close()

print("\n⚠️  YOU MUST CLOSE AND RESTART THE APP!")
print("The app loads the database on startup and caches it.")
print("Close the app window completely and run 'python app.py' again")
