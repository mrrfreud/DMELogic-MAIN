"""Sync order documents to patient profiles"""
import sqlite3
import os
from datetime import datetime

orders_db = r'C:\ProgramData\DMELogic\Data\orders.db'
patients_db = r'C:\ProgramData\DMELogic\Data\patients.db'

oc = sqlite3.connect(orders_db)
oc.row_factory = sqlite3.Row
pc = sqlite3.connect(patients_db)
pc.row_factory = sqlite3.Row

ocur = oc.cursor()
pcur = pc.cursor()

# Get all orders with attached files
ocur.execute('SELECT id, patient_id, attached_rx_files FROM orders WHERE attached_rx_files IS NOT NULL AND attached_rx_files != ""')
orders = ocur.fetchall()
print(f'Orders with documents: {len(orders)}')

added = 0
skipped = 0

for order in orders:
    order_id = order['id']
    patient_id = order['patient_id']
    attached = order['attached_rx_files'] or ''
    
    if not patient_id:
        continue
        
    # Parse files (semicolon or newline separated)
    files = [f.strip() for f in attached.replace(';', '\n').split('\n') if f.strip()]
    
    for file_path in files:
        if not os.path.exists(file_path):
            print(f'  File not found: {file_path}')
            continue
            
        filename = os.path.basename(file_path)
        
        # Check if exists
        pcur.execute('SELECT id FROM patient_documents WHERE patient_id = ? AND stored_path = ?', (patient_id, file_path))
        if pcur.fetchone():
            skipped += 1
            continue
        
        # Add
        pcur.execute('INSERT INTO patient_documents (patient_id, description, original_name, stored_path, created_at) VALUES (?, ?, ?, ?, ?)',
                    (patient_id, f'Order {order_id}', filename, file_path, datetime.now().isoformat()))
        added += 1
        print(f'  Added: patient={patient_id}, file={filename}')

pc.commit()
print(f'\nAdded: {added}, Skipped: {skipped}')

# Check patient 329 specifically
pcur.execute('SELECT * FROM patient_documents WHERE patient_id = 329')
docs = pcur.fetchall()
print(f'\nPatient 329 docs: {len(docs)}')
for d in docs:
    print(f'  {d["original_name"]}: {d["stored_path"]}')

pc.close()
oc.close()
