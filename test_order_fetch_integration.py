"""
Quick smoke test for order fetching integration.

Verifies:
1. Repository function works
2. Service layer functions work
3. Public API exports are accessible
4. Domain models have expected properties
"""

import sys
from decimal import Decimal

def test_imports():
    """Test all public API imports."""
    print("Testing imports...")
    try:
        from dmelogic.db import (
            fetch_order_with_items,
            build_state_portal_json_for_order,
            build_state_portal_csv_row_for_order,
            Order,
            OrderItem,
            OrderStatus,
        )
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_fetch_order():
    """Test basic order fetching."""
    print("\nTesting fetch_order_with_items...")
    try:
        from dmelogic.db import fetch_order_with_items
        
        folder_path = r"C:\FaxManagerData\Data"
        order = fetch_order_with_items(1, folder_path=folder_path)
        
        if not order:
            print("  ⚠ Order 1 not found (database may be empty)")
            return True  # Not a failure, just no data
        
        # Verify order has expected properties
        assert hasattr(order, 'id'), "Order missing 'id'"
        assert hasattr(order, 'patient_full_name'), "Order missing 'patient_full_name'"
        assert hasattr(order, 'order_status'), "Order missing 'order_status'"
        assert hasattr(order, 'items'), "Order missing 'items'"
        assert isinstance(order.items, list), "order.items should be a list"
        
        print(f"  ✓ Fetched order #{order.id}")
        print(f"  ✓ Patient: {order.patient_full_name}")
        print(f"  ✓ Status: {order.order_status.value}")
        print(f"  ✓ Items: {len(order.items)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_domain_model():
    """Test domain model properties."""
    print("\nTesting domain model properties...")
    try:
        from dmelogic.db import fetch_order_with_items, OrderStatus
        
        folder_path = r"C:\FaxManagerData\Data"
        order = fetch_order_with_items(1, folder_path=folder_path)
        
        if not order:
            print("  ⚠ Order 1 not found (skipping)")
            return True
        
        # Test computed properties
        full_name = order.patient_full_name
        assert isinstance(full_name, str), "patient_full_name should be string"
        
        # Test status enum
        assert hasattr(order.order_status, 'value'), "order_status should be enum"
        
        # Test ICD codes property
        icd_codes = order.icd_codes
        assert isinstance(icd_codes, list), "icd_codes should be list"
        
        print(f"  ✓ patient_full_name: {full_name}")
        print(f"  ✓ order_status: {order.order_status.value}")
        print(f"  ✓ icd_codes: {icd_codes}")
        
        # Test items
        if order.items:
            item = order.items[0]
            assert hasattr(item, 'hcpcs_code'), "OrderItem missing 'hcpcs_code'"
            assert hasattr(item, 'description'), "OrderItem missing 'description'"
            assert hasattr(item, 'quantity'), "OrderItem missing 'quantity'"
            print(f"  ✓ First item: {item.hcpcs_code} - {item.description}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Domain model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_layer():
    """Test service layer functions."""
    print("\nTesting service layer...")
    try:
        from dmelogic.db import (
            build_state_portal_json_for_order,
            build_state_portal_csv_row_for_order,
        )
        
        folder_path = r"C:\FaxManagerData\Data"
        
        # Test JSON export
        try:
            json_data = build_state_portal_json_for_order(1, folder_path=folder_path)
            assert isinstance(json_data, dict), "JSON export should return dict"
            print(f"  ✓ JSON export: {len(json_data)} top-level keys")
        except ValueError:
            print("  ⚠ Order 1 not found for JSON export")
        
        # Test CSV export
        try:
            csv_row = build_state_portal_csv_row_for_order(1, folder_path=folder_path)
            assert isinstance(csv_row, list), "CSV export should return list"
            print(f"  ✓ CSV export: {len(csv_row)} fields")
        except ValueError:
            print("  ⚠ Order 1 not found for CSV export")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Service layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_type_safety():
    """Test that types are as expected."""
    print("\nTesting type safety...")
    try:
        from dmelogic.db import Order, OrderItem, OrderStatus
        
        # Verify these are proper types
        assert Order is not None, "Order class not found"
        assert OrderItem is not None, "OrderItem class not found"
        assert OrderStatus is not None, "OrderStatus enum not found"
        
        # Check OrderStatus enum values
        assert hasattr(OrderStatus, 'PENDING'), "OrderStatus missing PENDING"
        assert hasattr(OrderStatus, 'READY'), "OrderStatus missing READY"
        assert hasattr(OrderStatus, 'DELIVERED'), "OrderStatus missing DELIVERED"
        
        print("  ✓ Order class: available")
        print("  ✓ OrderItem class: available")
        print("  ✓ OrderStatus enum: available")
        print(f"  ✓ OrderStatus values: {', '.join([s.value for s in OrderStatus])}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Type safety test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("ORDER FETCHING INTEGRATION - SMOKE TEST")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Fetch Order", test_fetch_order),
        ("Domain Model", test_domain_model),
        ("Service Layer", test_service_layer),
        ("Type Safety", test_type_safety),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Integration is working!")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
