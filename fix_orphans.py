import sqlite3

# Get patients lookup
patients_conn = sqlite3.connect('C:/ProgramData/DMELogic/Data/patients.db')
pc = patients_conn.cursor()
pc.execute('SELECT id, last_name, first_name FROM patients')
lookup = {}
for r in pc.fetchall():
    lookup[r[1] + ', ' + r[2]] = r[0]
patients_conn.close()

# Update orders with NULL patient_id
orders_conn = sqlite3.connect('C:/ProgramData/DMELogic/Data/orders.db')
oc = orders_conn.cursor()
oc.execute('SELECT id, patient_name FROM orders WHERE patient_id IS NULL AND patient_name IS NOT NULL')
rows = oc.fetchall()

print(f"Found {len(rows)} orders with NULL patient_id")
for oid, pname in rows:
    if pname in lookup:
        pid = lookup[pname]
        oc.execute('UPDATE orders SET patient_id = ? WHERE id = ?', (pid, oid))
        print(f'Order {oid}: Set patient_id = {pid} for {pname}')
    else:
        print(f'Order {oid}: Could not find patient for {pname}')
        
orders_conn.commit()
orders_conn.close()
print('Done')
