import sqlite3
from dmelogic.db.converters import row_to_order

conn = sqlite3.connect('C:/Dme_Solutions/Data/orders.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("SELECT * FROM orders WHERE id = 85")
header_row = cursor.fetchone()

print("Raw row keys:")
print(list(header_row.keys()))
print("\nRaw values:")
print(f"patient_last_name in row: {header_row['patient_last_name']}")
print(f"patient_first_name in row: {header_row['patient_first_name']}")

print("\n\nConverting to Order...")
order = row_to_order(header_row)

print(f"\nOrder object:")
print(f"  patient_id: {order.patient_id}")
print(f"  patient_last_name: {order.patient_last_name}")
print(f"  patient_first_name: {order.patient_first_name}")
print(f"  patient_name_at_order_time: {order.patient_name_at_order_time}")

conn.close()
