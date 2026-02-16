import sqlite3
c = sqlite3.connect('C:/ProgramData/DMELogic/Data/orders.db')
c.row_factory = sqlite3.Row
cur = c.cursor()
cur.execute('SELECT id, patient_last_name, patient_first_name, order_date, order_status, attached_rx_files, parent_order_id FROM orders WHERE id = 152')
r = cur.fetchone()
print(f'Order ID: {r["id"]}')
print(f'Patient: {r["patient_last_name"]}, {r["patient_first_name"]}')
print(f'Date: {r["order_date"]}')
print(f'Status: {r["order_status"]}')
print(f'Parent Order ID: {r["parent_order_id"]}')
print(f'attached_rx_files: [{r["attached_rx_files"]}]')
print(f'Is NULL or empty: {r["attached_rx_files"] is None or r["attached_rx_files"] == ""}')
c.close()
