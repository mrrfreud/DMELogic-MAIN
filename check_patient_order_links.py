#!/usr/bin/env python
"""
Diagnostic script to find orders that aren't linked to a valid patient.

Run this script to identify orders where:
1. patient_id is NULL
2. patient_id doesn't match any existing patient

This helps explain why some patients don't show orders in their Order History tab.
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
    
    # Load all patient IDs from patients.db
    pconn = sqlite3.connect(patients_db)
    pconn.row_factory = sqlite3.Row
    pcur = pconn.cursor()
    pcur.execute("SELECT id, last_name, first_name, dob FROM patients")
    patients = {row["id"]: dict(row) for row in pcur.fetchall()}
    pconn.close()
    
    print(f"Found {len(patients)} patients in patients.db")
    print()
    
    # Check orders for patient linkage issues
    oconn = sqlite3.connect(orders_db)
    oconn.row_factory = sqlite3.Row
    ocur = oconn.cursor()
    
    # Find orders with NULL patient_id
    ocur.execute("""
        SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob, 
               order_date, order_status
        FROM orders
        WHERE patient_id IS NULL OR patient_id = 0 OR patient_id = ''
        ORDER BY id
    """)
    null_orders = ocur.fetchall()
    
    if null_orders:
        print(f"🔴 Found {len(null_orders)} orders with NULL/empty patient_id:")
        print("-" * 80)
        for order in null_orders:
            print(f"  Order #{order['id']:03d}: {order['patient_last_name']}, {order['patient_first_name']} "
                  f"(DOB: {order['patient_dob']}) - {order['order_status']} - {order['order_date']}")
        print()
    else:
        print("✅ No orders with NULL patient_id found")
        print()
    
    # Find orders where patient_id doesn't match any patient
    ocur.execute("""
        SELECT id, patient_id, patient_last_name, patient_first_name, patient_dob,
               order_date, order_status
        FROM orders
        WHERE patient_id IS NOT NULL AND patient_id != 0 AND patient_id != ''
        ORDER BY id
    """)
    linked_orders = ocur.fetchall()
    
    orphaned_orders = []
    for order in linked_orders:
        pid = order["patient_id"]
        if pid and pid not in patients:
            orphaned_orders.append(order)
    
    if orphaned_orders:
        print(f"🔴 Found {len(orphaned_orders)} orders with patient_id that doesn't exist:")
        print("-" * 80)
        for order in orphaned_orders:
            print(f"  Order #{order['id']:03d}: patient_id={order['patient_id']} "
                  f"({order['patient_last_name']}, {order['patient_first_name']}) - {order['order_status']}")
        print()
    else:
        print(f"✅ All {len(linked_orders)} linked orders reference valid patients")
        print()
    
    oconn.close()
    
    # Summary and recommendations
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_issues = len(null_orders) + len(orphaned_orders)
    if total_issues == 0:
        print("✅ All orders are properly linked to patients!")
    else:
        print(f"⚠️  Found {total_issues} orders with linkage issues")
        print()
        print("RECOMMENDED FIX:")
        print("1. Open the application")
        print("2. Go to Orders screen")
        print("3. For each problematic order, double-click to edit")
        print("4. Click 'Link Patient' to properly connect it to a patient record")
        print()
        print("Or run the following SQL to attempt auto-fix by matching name + DOB:")
        print()
        print("-- Auto-link orders by matching patient name + DOB")
        print("UPDATE orders SET patient_id = (")
        print("    SELECT p.id FROM patients p")
        print("    WHERE UPPER(p.last_name) = UPPER(orders.patient_last_name)")
        print("      AND UPPER(p.first_name) = UPPER(orders.patient_first_name)")
        print("      AND p.dob = orders.patient_dob")
        print("    LIMIT 1")
        print(") WHERE patient_id IS NULL;")


if __name__ == "__main__":
    main()
