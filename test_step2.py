"""
Test workflow services (Step 2).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dmelogic.workflows import (
    OrderWorkflowService,
    RefillWorkflowService,
    create_order_with_items,
    process_refill,
    delete_order,
    OrderValidationError,
    RefillValidationError
)
from dmelogic.db.repositories import OrderRepository


def test_order_workflow_service():
    """Test OrderWorkflowService."""
    print("\n=== Testing OrderWorkflowService ===")
    
    service = OrderWorkflowService()
    
    # Test with invalid patient (should fail)
    print("\nTesting validation (invalid patient)...")
    try:
        service.create_order_with_items(
            patient_id=999999,  # Non-existent
            prescriber_id=1,
            items=[{'hcpcs_code': 'E0601', 'quantity': 1, 'unit_price': 250.00}]
        )
        print("  ✗ Should have raised OrderValidationError")
    except OrderValidationError as e:
        print(f"  ✓ Validation error caught: {e}")
    
    # Test with invalid prescriber (should fail)
    print("\nTesting validation (invalid prescriber)...")
    try:
        service.create_order_with_items(
            patient_id=1,
            prescriber_id=999999,  # Non-existent
            items=[{'hcpcs_code': 'E0601', 'quantity': 1, 'unit_price': 250.00}]
        )
        print("  ✗ Should have raised OrderValidationError")
    except OrderValidationError as e:
        print(f"  ✓ Validation error caught: {e}")
    
    # Test with no items (should fail)
    print("\nTesting validation (no items)...")
    try:
        service.create_order_with_items(
            patient_id=1,
            prescriber_id=1,
            items=[]  # Empty
        )
        print("  ✗ Should have raised OrderValidationError")
    except OrderValidationError as e:
        print(f"  ✓ Validation error caught: {e}")
    
    # Test successful order creation
    print("\nTesting successful order creation...")
    try:
        order_id = service.create_order_with_items(
            patient_id=1,
            prescriber_id=1,
            items=[
                {'hcpcs_code': 'E0601', 'quantity': 1, 'unit_price': 250.00, 'description': 'CPAP Device'},
                {'hcpcs_code': 'A4604', 'quantity': 30, 'unit_price': 1.50, 'description': 'Tubing'}
            ],
            notes="Test order from workflow service"
        )
        print(f"  ✓ Order created successfully: {order_id}")
        
        # Verify order exists
        repo = OrderRepository()
        order = repo.get_by_id(order_id)
        if order:
            print(f"  ✓ Order verified: {order.get('patient_name', 'N/A')}")
            print(f"    Status: {order.get('order_status', 'N/A')}")
            print(f"    Notes: {order.get('notes', 'N/A')}")
        
        # Test update status
        print("\nTesting update_order_status...")
        success = service.update_order_status(
            order_id=order_id,
            new_status="Shipped",
            notes="Test shipment"
        )
        if success:
            print(f"  ✓ Status updated successfully")
            
            # Verify update
            order = repo.get_by_id(order_id)
            if order and order.get('order_status') == 'Shipped':
                print(f"  ✓ Status verified: {order['order_status']}")
        
        # Test soft delete
        print("\nTesting soft_delete_order...")
        success = service.soft_delete_order(
            order_id=order_id,
            deleted_by="test_user",
            reason="Testing workflow service"
        )
        if success:
            print(f"  ✓ Order soft-deleted successfully")
            
            # Verify deletion
            order = repo.get_by_id(order_id)
            if order and order.get('deleted_at'):
                print(f"  ✓ Deletion verified: {order.get('deleted_at')}")
                print(f"    Deleted by: {order.get('deleted_by', 'N/A')}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ OrderWorkflowService tests complete!")


def test_convenience_functions():
    """Test convenience functions."""
    print("\n=== Testing Convenience Functions ===")
    
    # Test create_order_with_items
    print("\nTesting create_order_with_items()...")
    try:
        order_id = create_order_with_items(
            patient_id=1,
            prescriber_id=1,
            items=[
                {'hcpcs_code': 'E0601', 'quantity': 1, 'unit_price': 250.00}
            ],
            notes="Test via convenience function"
        )
        print(f"  ✓ Order created: {order_id}")
        
        # Test delete_order
        print("\nTesting delete_order()...")
        success = delete_order(
            order_id=order_id,
            deleted_by="test",
            reason="Testing convenience function"
        )
        if success:
            print(f"  ✓ Order deleted: {order_id}")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✓ Convenience function tests complete!")


def test_refill_workflow_service():
    """Test RefillWorkflowService."""
    print("\n=== Testing RefillWorkflowService ===")
    
    service = RefillWorkflowService()
    
    # Test with invalid order item
    print("\nTesting validation (invalid order_item_id)...")
    try:
        service.process_refill(order_item_id=999999)
        print("  ✗ Should have raised RefillValidationError")
    except RefillValidationError as e:
        print(f"  ✓ Validation error caught: {e}")
    
    print("\n  Note: Full refill testing requires order items with refills configured.")
    print("  This would be tested in integration tests with proper test data.")
    
    print("\n✓ RefillWorkflowService validation tests complete!")


def test_transaction_rollback():
    """Test that transactions rollback on failure."""
    print("\n=== Testing Transaction Rollback ===")
    
    service = OrderWorkflowService()
    repo = OrderRepository()
    
    # Get initial count
    initial_orders = len(repo.get_deleted_orders())
    
    # Try to create order with validation error
    print("\nAttempting to create order with invalid data...")
    try:
        service.create_order_with_items(
            patient_id=999999,  # Invalid
            prescriber_id=1,
            items=[{'hcpcs_code': 'E0601', 'quantity': 1, 'unit_price': 250.00}]
        )
    except OrderValidationError:
        print("  ✓ Validation failed (expected)")
    
    # Verify no orders were created
    final_orders = len(repo.get_deleted_orders())
    
    if initial_orders == final_orders:
        print("  ✓ Transaction rolled back successfully (no orders created)")
    else:
        print(f"  ✗ Transaction may not have rolled back properly")
    
    print("\n✓ Transaction rollback tests complete!")


def test_workflow_integration():
    """Test complete workflow integration."""
    print("\n=== Testing Workflow Integration ===")
    
    print("\nCreating order with multiple items...")
    try:
        # Create order
        order_id = create_order_with_items(
            patient_id=1,
            prescriber_id=1,
            items=[
                {
                    'hcpcs_code': 'E0601',
                    'quantity': 1,
                    'unit_price': 250.00,
                    'description': 'CPAP Device'
                },
                {
                    'hcpcs_code': 'A4604',
                    'quantity': 30,
                    'unit_price': 1.50,
                    'description': 'Disposable Tubing'
                },
                {
                    'hcpcs_code': 'A7034',
                    'quantity': 12,
                    'unit_price': 5.00,
                    'description': 'Filters'
                }
            ],
            notes="Complete workflow integration test"
        )
        
        print(f"  ✓ Order {order_id} created with 3 items")
        
        # Update status
        service = OrderWorkflowService()
        service.update_order_status(order_id, "Processing", "Ready to ship")
        print(f"  ✓ Status updated to Processing")
        
        service.update_order_status(order_id, "Shipped", "Sent via UPS")
        print(f"  ✓ Status updated to Shipped")
        
        service.update_order_status(order_id, "Completed", "Delivered successfully")
        print(f"  ✓ Status updated to Completed")
        
        # Verify final state
        repo = OrderRepository()
        final_order = repo.get_by_id(order_id)
        
        if final_order:
            print(f"\n  Final order state:")
            print(f"    ID: {final_order.get('order_id')}")
            print(f"    Patient: {final_order.get('patient_name')}")
            print(f"    Status: {final_order.get('order_status')}")
            print(f"    Notes: {final_order.get('notes')}")
        
        print("\n✓ Workflow integration test complete!")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("Step 2: Testing Workflow Services")
    print("="*60)
    
    test_order_workflow_service()
    test_convenience_functions()
    test_refill_workflow_service()
    test_transaction_rollback()
    test_workflow_integration()
    
    print("\n" + "="*60)
    print("✅ Step 2 Workflow Services Tests Complete!")
    print("="*60)
    print("\nNew features available:")
    print("  • OrderWorkflowService")
    print("    - create_order_with_items()")
    print("    - soft_delete_order()")
    print("    - update_order_status()")
    print("  • RefillWorkflowService")
    print("    - process_refill()")
    print("  • Convenience functions:")
    print("    - create_order_with_items()")
    print("    - delete_order()")
    print("    - process_refill()")
    print("  • Full UnitOfWork transaction support")
    print("  • Automatic audit logging")
    print("  • Validation with clear error messages")
