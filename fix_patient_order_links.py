#!/usr/bin/env python
"""
One-time migration script to link orphaned orders to patients by matching
patient name and DOB.

This fixes orders that have patient_id = NULL by looking up the patient
in the patients table using the snapshot fields (patient_last_name, 
patient_first_name, patient_dob).

Run this once to fix historical data, then all future orders will be
properly linked at creation time.
"""

import sqlite3
import os

def main():
    # Get database paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check installer_data folder first, then current directory
    data_folders = [
        os.path.join(script_dir, "installer_data"),
        script_dir,
        os.path.join(script_dir, "data"),
    ]
    
    orders_db = None
    patients_db = None
    
    for folder in data_folders:
        orders_path = os.path.join(folder, "orders.db")
        patients_path = os.path.join(folder, "patients.db")
        
        if os.path.exists(orders_path):
            orders_db = orders_path
        if os.path.exists(patients_path):
            patients_db = patients_path
            
        if orders_db and patients_db:
            break
    
    if not orders_db:
        print("ERROR: Could not find orders.db")
        return
    
    if not patients_db:
        print("ERROR: Could not find patients.db")
        return
        
    print(f"Orders DB: {orders_db}")
    print(f"Patients DB: {patients_db}")
    print("-" * 80)
    
    # Load all patients from patients.db (building a lookup by name + DOB)
    pconn = sqlite3.connect(patients_db)
    pconn.row_factory = sqlite3.Row
    pcur = pconn.cursor()
    pcur.execute("SELECT id, last_name, first_name, dob FROM patients")
    
    # Create lookup: (UPPER(last_name), UPPER(first_name), normalized_dob) -> patient_id
    patient_lookup = {}
    for row in pcur.fetchall():
        # Normalize DOB by removing common separators
        dob = (row["dob"] or "").replace("/", "").replace("-", "").replace(".", "").replace(" ", "").strip()
        key = (
            (row["last_name"] or "").upper().strip(),
            (row["first_name"] or "").upper().strip(),
            dob,
        )
        patient_lookup[key] = row["id"]
    pconn.close()
    
    print(f"Loaded {len(patient_lookup)} patients for lookup")
    print()
    
    # Find orders with NULL patient_id
    oconn = sqlite3.connect(orders_db)
    oconn.row_factory = sqlite3.Row
    ocur = oconn.cursor()
    
    ocur.execute("""
        SELECT id, patient_last_name, patient_first_name, patient_dob
        FROM orders
        WHERE patient_id IS NULL OR patient_id = 0 OR patient_id = ''
        ORDER BY id
    """)
    orphan_orders = ocur.fetchall()
    
    if not orphan_orders:
        print("✅ No orphaned orders found - nothing to fix!")
        oconn.close()
        return
    
    print(f"Found {len(orphan_orders)} orders with NULL patient_id")
    print()
    
    # Attempt to match each order to a patient
    fixed_count = 0
    not_found = []
    
    for order in orphan_orders:
        order_id = order["id"]
        last_name = (order["patient_last_name"] or "").upper().strip()
        first_name = (order["patient_first_name"] or "").upper().strip()
        dob_raw = order["patient_dob"] or ""
        dob_norm = dob_raw.replace("/", "").replace("-", "").replace(".", "").replace(" ", "").strip()
        
        lookup_key = (last_name, first_name, dob_norm)
        
        patient_id = patient_lookup.get(lookup_key)
        
        if patient_id:
            print(f"  ✅ Order #{order_id:03d}: Linking to patient_id={patient_id} ({last_name}, {first_name})")
            ocur.execute(
                "UPDATE orders SET patient_id = ? WHERE id = ?",
                (patient_id, order_id),
            )
            fixed_count += 1
        else:
            print(f"  ❌ Order #{order_id:03d}: No matching patient found for ({last_name}, {first_name}, {dob_raw})")
            not_found.append(order)
    
    oconn.commit()
    oconn.close()
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Fixed: {fixed_count} orders")
    print(f"❌ Not found: {len(not_found)} orders")
    
    if not_found:
        print()
        print("Orders that couldn't be auto-linked (patient not found):")
        for order in not_found:
            print(f"  - Order #{order['id']:03d}: {order['patient_last_name']}, {order['patient_first_name']} (DOB: {order['patient_dob']})")
        print()
        print("These orders may need manual attention:")
        print("1. The patient might not exist in the patients database")
        print("2. The name/DOB in the order might be slightly different from the patient record")
        print("3. You can manually link via the Order Editor 'Link Patient' button")


if __name__ == "__main__":
    main()
