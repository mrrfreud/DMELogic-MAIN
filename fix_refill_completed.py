"""Fix orders that should have refill_completed = 1 but don't.

Any order that has been used as a parent (i.e., another order references it in parent_order_id)
should have refill_completed = 1 and is_locked = 1.
"""

import sqlite3
import os

# Database path
DB_FOLDER = r"C:\ProgramData\DMELogic\Data"
ORDERS_DB = os.path.join(DB_FOLDER, "orders.db")


def fix_refill_completed():
    """Find and fix orders that should be marked as refill_completed."""
    conn = sqlite3.connect(ORDERS_DB)
    cursor = conn.cursor()
    
    # Find all orders that are parents (have children pointing to them) but don't have refill_completed = 1
    cursor.execute("""
        SELECT DISTINCT o.id, o.refill_completed, o.is_locked
        FROM orders o
        WHERE o.id IN (
            SELECT DISTINCT parent_order_id 
            FROM orders 
            WHERE parent_order_id IS NOT NULL
        )
        AND (COALESCE(o.refill_completed, 0) = 0 OR COALESCE(o.is_locked, 0) = 0)
    """)
    
    orders_to_fix = cursor.fetchall()
    
    if not orders_to_fix:
        print("No orders need fixing.")
        conn.close()
        return
    
    print(f"Found {len(orders_to_fix)} order(s) that need refill_completed and is_locked flags:")
    for order_id, refill_completed, is_locked in orders_to_fix:
        print(f"  - Order ID {order_id}: refill_completed={refill_completed}, is_locked={is_locked}")
    
    # Fix them
    cursor.execute("""
        UPDATE orders 
        SET refill_completed = 1, is_locked = 1
        WHERE id IN (
            SELECT DISTINCT parent_order_id 
            FROM orders 
            WHERE parent_order_id IS NOT NULL
        )
        AND (COALESCE(refill_completed, 0) = 0 OR COALESCE(is_locked, 0) = 0)
    """)
    
    affected = cursor.rowcount
    conn.commit()
    
    print(f"\nFixed {affected} order(s).")
    
    # Verify the fix
    cursor.execute("""
        SELECT id, refill_completed, is_locked
        FROM orders
        WHERE id IN (
            SELECT DISTINCT parent_order_id 
            FROM orders 
            WHERE parent_order_id IS NOT NULL
        )
    """)
    
    print("\nCurrent state of parent orders:")
    for order_id, refill_completed, is_locked in cursor.fetchall():
        print(f"  - Order ID {order_id}: refill_completed={refill_completed}, is_locked={is_locked}")
    
    conn.close()


if __name__ == "__main__":
    fix_refill_completed()
