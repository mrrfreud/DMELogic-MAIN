"""
Apply billing modifiers migration.

Adds modifier1, modifier2, modifier3, modifier4, and rental_month columns to order_items table.
"""

from dmelogic.db.base import run_migrations
from dmelogic.db.migrations import ORDER_MIGRATIONS


def main():
    """Run the billing modifiers migration."""
    print("=" * 70)
    print("APPLYING BILLING MODIFIERS MIGRATION")
    print("=" * 70)
    
    folder_path = r"C:\FaxManagerData\Data"
    
    print(f"\nDatabase location: {folder_path}")
    print("\nRunning migrations...")
    
    try:
        count = run_migrations("orders.db", ORDER_MIGRATIONS, folder_path=folder_path)
        
        print(f"\n✓ Successfully applied {count} migration(s)")
        print("\nNew columns added to order_items:")
        print("  - modifier1 (TEXT)")
        print("  - modifier2 (TEXT)")
        print("  - modifier3 (TEXT)")
        print("  - modifier4 (TEXT)")
        print("  - rental_month (INTEGER DEFAULT 0)")
        
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
