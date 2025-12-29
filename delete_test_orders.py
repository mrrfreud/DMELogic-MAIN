"""
Script to delete test orders from the database.
"""
import sqlite3
import shutil
from pathlib import Path

DB_PATH = r'C:\FaxManagerData\Data\orders.db'

def backup_database():
    """Create a backup before deletion."""
    backup_path = f"{DB_PATH}.backup_before_delete"
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")

def list_orders():
    """List all orders."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, patient_name, order_date, order_status FROM orders ORDER BY id')
    orders = cur.fetchall()
    
    print('\n' + '='*70)
    print('ALL ORDERS IN DATABASE')
    print('='*70)
    print(f"{'ID':<5} | {'Patient Name':<30} | {'Date':<12} | {'Status':<15}")
    print('-'*70)
    
    for order in orders:
        patient = order[1] or "N/A"
        date = order[2] or "N/A"
        status = order[3] or "N/A"
        print(f"{order[0]:<5} | {patient:<30} | {date:<12} | {status:<15}")
    
    print(f"\nTotal Orders: {len(orders)}")
    conn.close()
    return orders

def delete_test_orders():
    """Delete test orders."""
    backup_database()
    orders = list_orders()
    
    if not orders:
        print("\n❌ No orders found in database.")
        return
    
    print("\n" + "="*70)
    print("DELETE OPTIONS")
    print("="*70)
    print("1. Delete specific order IDs")
    print("2. Delete all orders")
    print("3. Cancel")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    if choice == "1":
        ids_input = input("\nEnter order IDs to delete (comma-separated): ").strip()
        ids = [int(x.strip()) for x in ids_input.split(',') if x.strip().isdigit()]
        
        if not ids:
            print("❌ No valid IDs provided.")
            conn.close()
            return
        
        # Delete order items first
        cur.execute(f'DELETE FROM order_items WHERE order_id IN ({",".join("?" * len(ids))})', ids)
        items_deleted = cur.rowcount
        
        # Delete orders
        cur.execute(f'DELETE FROM orders WHERE id IN ({",".join("?" * len(ids))})', ids)
        orders_deleted = cur.rowcount
        
        conn.commit()
        print(f"\n✅ Deleted {orders_deleted} orders and {items_deleted} order items")
        
    elif choice == "2":
        confirm = input("\n⚠️  DELETE ALL ORDERS? This cannot be undone! Type 'YES' to confirm: ").strip()
        
        if confirm == "YES":
            cur.execute('DELETE FROM order_items')
            items_deleted = cur.rowcount
            
            cur.execute('DELETE FROM orders')
            orders_deleted = cur.rowcount
            
            conn.commit()
            print(f"\n✅ Deleted all {orders_deleted} orders and {items_deleted} order items")
        else:
            print("\n❌ Deletion cancelled.")
    else:
        print("\n❌ Operation cancelled.")
    
    conn.close()
    
    # Show remaining orders
    print("\n" + "="*70)
    print("REMAINING ORDERS")
    print("="*70)
    list_orders()

if __name__ == "__main__":
    delete_test_orders()
