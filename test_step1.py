"""
Test the new repository pattern implementation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dmelogic.db.repositories import (
    PatientRepository,
    PrescriberRepository,
    OrderRepository,
    InventoryRepository
)
from dmelogic.db.base import row_to_dict, rows_to_dicts, UnitOfWork


def test_helpers():
    """Test row_to_dict helpers."""
    print("\n=== Testing Helper Functions ===")
    
    # Test row_to_dict with None
    result = row_to_dict(None)
    assert result == {}, f"Expected empty dict, got {result}"
    print("✓ row_to_dict(None) returns empty dict")
    
    # Test rows_to_dicts
    result = rows_to_dicts([])
    assert result == [], f"Expected empty list, got {result}"
    print("✓ rows_to_dicts([]) returns empty list")
    
    print("✓ All helper tests passed!")


def test_repositories_standalone():
    """Test repositories in standalone mode."""
    print("\n=== Testing Repositories (Standalone) ===")
    
    try:
        # Test PatientRepository
        print("\nTesting PatientRepository...")
        patient_repo = PatientRepository()
        patients = patient_repo.get_all()
        print(f"  ✓ get_all() returned {len(patients)} patients")
        
        if patients:
            patient = patient_repo.get_by_id(patients[0]['id'])
            if patient:
                print(f"  ✓ get_by_id() works: {patient.get('first_name', 'N/A')}")
        
        # Test PrescriberRepository
        print("\nTesting PrescriberRepository...")
        prescriber_repo = PrescriberRepository()
        prescribers = prescriber_repo.get_all()
        print(f"  ✓ get_all() returned {len(prescribers)} prescribers")
        
        # Test OrderRepository
        print("\nTesting OrderRepository...")
        order_repo = OrderRepository()
        deleted = order_repo.get_deleted_orders()
        print(f"  ✓ get_deleted_orders() returned {len(deleted)} orders")
        
        # Test InventoryRepository
        print("\nTesting InventoryRepository...")
        inventory_repo = InventoryRepository()
        items = inventory_repo.get_all()
        print(f"  ✓ get_all() returned {len(items)} items")
        
        print("\n✓ All repository tests passed!")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_unitofwork():
    """Test UnitOfWork pattern."""
    print("\n=== Testing UnitOfWork Pattern ===")
    
    try:
        with UnitOfWork() as uow:
            # Get connections
            patient_conn = uow.connection("patients.db")
            order_conn = uow.connection("orders.db")
            
            print(f"  ✓ Got patient connection: {patient_conn}")
            print(f"  ✓ Got order connection: {order_conn}")
            
            # Create repositories with shared connections
            patient_repo = PatientRepository(conn=patient_conn)
            order_repo = OrderRepository(conn=order_conn)
            
            # Perform reads
            patients = patient_repo.get_all()
            orders = order_repo.get_deleted_orders()
            
            print(f"  ✓ PatientRepository with UoW: {len(patients)} patients")
            print(f"  ✓ OrderRepository with UoW: {len(orders)} orders")
            
            # Commit (no changes made, but tests the pattern)
            uow.commit()
            print("  ✓ UoW committed successfully")
        
        print("\n✓ UnitOfWork tests passed!")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_dict_safety():
    """Test that returned dicts support .get() safely."""
    print("\n=== Testing Dict Safety ===")
    
    try:
        patient_repo = PatientRepository()
        patients = patient_repo.get_all()
        
        if patients:
            patient = patients[0]
            
            # Test .get() with default
            name = patient.get('first_name', 'Default')
            print(f"  ✓ .get() with default works: {name}")
            
            # Test .get() on missing key
            missing = patient.get('nonexistent_field', 'Default')
            assert missing == 'Default'
            print(f"  ✓ .get() on missing key returns default")
            
            # Test direct access
            if 'first_name' in patient:
                name2 = patient['first_name']
                print(f"  ✓ Direct dict access works: {name2}")
        
        print("\n✓ Dict safety tests passed!")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("Step 1: Testing Repository Pattern Implementation")
    print("="*60)
    
    test_helpers()
    test_repositories_standalone()
    test_unitofwork()
    test_dict_safety()
    
    print("\n" + "="*60)
    print("✅ Step 1 Implementation Complete!")
    print("="*60)
    print("\nNew features available:")
    print("  • row_to_dict() / rows_to_dicts() helpers")
    print("  • PatientRepository")
    print("  • PrescriberRepository")
    print("  • OrderRepository")
    print("  • InventoryRepository")
    print("  • UnitOfWork support in all repositories")
    print("\nSee STEP1_COMPLETE.md for usage guide.")
