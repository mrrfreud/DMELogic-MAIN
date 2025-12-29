import sqlite3

conn = sqlite3.connect('C:/Dme_Solutions/Data/orders.db')
cursor = conn.cursor()

cursor.execute('SELECT created_date, patient_last_name, patient_first_name, patient_name FROM orders WHERE id = 85')
row = cursor.fetchone()

print(f'Created: {row[0]}')
print(f'patient_last_name: [{row[1]}]')
print(f'patient_first_name: [{row[2]}]')
print(f'patient_name: [{row[3]}]')

conn.close()
