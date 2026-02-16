import sqlite3
oc = sqlite3.connect('C:/ProgramData/DMELogic/Data/orders.db')
oc.row_factory = sqlite3.Row
cur = oc.cursor()
cur.execute('SELECT id, patient_id, attached_rx_files FROM orders WHERE patient_id = 329')
rows = cur.fetchall()
print(f'Orders for patient 329: {len(rows)}')
for r in rows:
    print(f'  Order {r[0]}: {r[2]}')
oc.close()
