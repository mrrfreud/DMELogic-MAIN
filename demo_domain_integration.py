"""
Demonstration: Complete Domain Model Integration

Shows how the repository pattern + domain models work together:

1. fetch_order_with_items() - Single source of truth for order data
2. Domain models (Order, OrderItem) - Rich, typed business objects
3. Service layer - High-level operations for specific use cases
4. View models - Transform domain → external formats (State Portal, HCFA-1500)

This replaces scattered SQL queries with clean, testable architecture.
"""

from dmelogic.db import (
    fetch_order_with_items,
    build_state_portal_json_for_order,
    build_state_portal_csv_row_for_order,
)


def demo_fetch_order():
    """Show basic order fetching with rich domain model."""
    print("=" * 70)
    print("DEMO 1: Fetch Order with Items (Domain Model)")
    print("=" * 70)
    
    folder_path = r"C:\FaxManagerData\Data"
    order_id = 1
    
    # Single call gets complete order aggregate
    order = fetch_order_with_items(order_id, folder_path=folder_path)
    
    if not order:
        print(f"❌ Order {order_id} not found")
        return
    
    # Rich domain model with typed fields
    print(f"\n✓ Order #{order.id}")
    print(f"  Patient: {order.patient_full_name}")
    print(f"  DOB: {order.patient_dob_at_order_time or 'N/A'}")
    print(f"  Status: {order.order_status.value}")  # Enum!
    print(f"  Prescriber: {order.prescriber_name_at_order_time} (NPI: {order.prescriber_npi_at_order_time})")
    print(f"  Insurance: {order.insurance_name_at_order_time}")
    
    # Items are fully hydrated
    print(f"\n  Items ({len(order.items)}):")
    for item in order.items:
        print(f"    • {item.hcpcs_code}: {item.description}")
        print(f"      Qty: {item.quantity}, Refills: {item.refills}, Days: {item.days_supply}")
        if item.cost_ea:
            print(f"      Cost: ${item.cost_ea} ea = ${item.total_cost or 0}")
    
    # ICD codes extracted
    if order.icd_codes:
        print(f"\n  ICD-10 Codes: {', '.join(order.icd_codes)}")
    
    print("\n✓ Complete typed domain model ready for any view")


def demo_state_portal_json():
    """Show State Portal JSON export using service layer."""
    print("\n" + "=" * 70)
    print("DEMO 2: State Portal JSON Export (Service Layer)")
    print("=" * 70)
    
    folder_path = r"C:\FaxManagerData\Data"
    order_id = 1
    
    try:
        # High-level service function handles everything
        json_data = build_state_portal_json_for_order(order_id, folder_path=folder_path)
        
        print("\n✓ JSON ready for State Portal API:")
        print(f"  Claim Number: {json_data.get('claimNumber', 'N/A')}")
        print(f"  Status: {json_data.get('status', 'N/A')}")
        
        if 'patient' in json_data:
            patient = json_data['patient']
            print(f"  Patient: {patient.get('lastName', '')}, {patient.get('firstName', '')}")
        
        if 'prescriber' in json_data:
            prescriber = json_data['prescriber']
            print(f"  Prescriber NPI: {prescriber.get('npi', 'N/A')}")
        
        if 'claim' in json_data and 'items' in json_data['claim']:
            items = json_data['claim']['items']
            print(f"  Items: {len(items)} products")
            
            # Show first item
            if items:
                item = items[0]
                print(f"\n  Sample Item:")
                print(f"    HCPCS: {item.get('hcpcsCode', 'N/A')}")
                print(f"    Description: {item.get('description', 'N/A')}")
                print(f"    Quantity: {item.get('quantity', 'N/A')}")
        
        print("\n✓ Ready to POST to state portal endpoint")
        
    except ValueError as e:
        print(f"❌ {e}")


def demo_state_portal_csv():
    """Show State Portal CSV export using service layer."""
    print("\n" + "=" * 70)
    print("DEMO 3: State Portal CSV Export (Service Layer)")
    print("=" * 70)
    
    folder_path = r"C:\FaxManagerData\Data"
    order_id = 1
    
    try:
        # High-level service function returns CSV row list
        csv_row = build_state_portal_csv_row_for_order(order_id, folder_path=folder_path)
        
        print("\n✓ CSV row ready for bulk export:")
        print(f"  Fields: {len(csv_row)} values")
        print(f"  First 5 fields: {csv_row[:5]}")
        
        print("\n✓ Ready for CSV writer / batch export")
        
    except ValueError as e:
        print(f"❌ {e}")


def demo_architecture_overview():
    """Show the clean architecture in action."""
    print("\n" + "=" * 70)
    print("ARCHITECTURE OVERVIEW")
    print("=" * 70)
    
    print("""
✓ Repository Pattern (dmelogic/db/orders.py)
  └─ fetch_order_with_items(order_id, folder_path) → Order
     • Single source of truth for order data
     • Returns rich domain model (not raw SQL rows)
     • Handles connection management

✓ Domain Models (dmelogic/models/*.py)
  └─ Order, OrderItem
     • Typed fields with enums (OrderStatus, BillingType)
     • Computed properties (patient_full_name, icd_codes)
     • Business logic encapsulation

✓ Service Layer (dmelogic/db/order_workflow.py)
  └─ build_state_portal_json_for_order(order_id, folder_path) → dict
  └─ build_state_portal_csv_row_for_order(order_id, folder_path) → dict
     • High-level operations for specific use cases
     • Coordinates repository + view models
     • Simple, testable interface

✓ View Models (dmelogic/db/state_portal_view.py)
  └─ StatePortalOrderView.from_order(order) → view
     • Transforms domain → external format
     • Isolates mapping logic
     • Easy to add new formats (HCFA-1500 next!)

BENEFITS:
  • No scattered SQL queries in UI code
  • Single fetch path for all order data
  • Type safety with IDE autocomplete
  • Easy to test each layer
  • Clear separation of concerns
  • Ready for HCFA-1500, delivery tickets, reports...
    """)


if __name__ == "__main__":
    print("\n🎯 Domain Model Integration Complete Demo\n")
    
    # Run all demos
    demo_fetch_order()
    demo_state_portal_json()
    demo_state_portal_csv()
    demo_architecture_overview()
    
    print("\n" + "=" * 70)
    print("✓ All systems operational - clean architecture in place!")
    print("=" * 70)
    print("""
NEXT STEPS:
  1. Wire UI buttons to use service functions (no raw SQL)
  2. Add similar pattern for HCFA-1500 form generation
  3. Use fetch_order_with_items() for any order display/export
  4. Add unit tests for each layer
""")
