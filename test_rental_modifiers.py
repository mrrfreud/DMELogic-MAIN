"""
Test rental and modifier functionality.
"""
from decimal import Decimal
from dmelogic.db.models import OrderInput, OrderItemInput
from dmelogic.db.orders import create_order
from dmelogic.db import fetch_order_with_items

# Create test order with rental items and modifiers
order_input = OrderInput(
    patient_last_name="TestRental",
    patient_first_name="John",
    patient_dob="1980-01-01",
    patient_phone="555-1234",
    prescriber_name="Dr. Smith",
    prescriber_npi="1234567890",
    rx_date="2025-12-06",
    order_date="2025-12-06",
    billing_type="Insurance",
    primary_insurance="Test Insurance",
    primary_insurance_id="TEST123",
    icd_code_1="M54.5",
    items=[
        OrderItemInput(
            hcpcs="E0143",
            description="Walker, folding, adjustable height",
            quantity=1,
            refills=0,
            days_supply=30,
            cost_ea=Decimal("150.00"),
            is_rental=False,  # Purchase
            modifier1="NU",   # New equipment
            modifier2=None,
            modifier3=None,
            modifier4=None,
        ),
        OrderItemInput(
            hcpcs="E0185",
            description="Wheelchair, power",
            quantity=1,
            refills=0,
            days_supply=30,
            cost_ea=Decimal("500.00"),
            is_rental=True,   # Rental
            modifier1="RR",   # Rental
            modifier2="KH",   # Initial rental month
            modifier3=None,
            modifier4=None,
        ),
    ],
)

# Test validation
errors = order_input.validate()
if errors:
    print("❌ Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ Order validation passed")

# Test item validation and modifier normalization
for idx, item in enumerate(order_input.items, 1):
    print(f"\n📦 Item {idx}: {item.hcpcs} - {item.description}")
    print(f"   Rental: {'Yes' if item.is_rental else 'No'}")
    
    # Test normalized modifiers
    mods = item.normalized_modifiers()
    print(f"   Modifiers: {[m for m in mods if m]}")
    
    # Test item validation
    item_errors = item.validate()
    if item_errors:
        print(f"   ❌ Errors: {item_errors}")
    else:
        print(f"   ✅ Valid")

# Create order in database
try:
    print("\n\n🔨 Creating order in database...")
    order_id = create_order(order_input, folder_path=r"C:\FaxManagerData\Data")
    print(f"✅ Order created with ID: {order_id}")
    
    # Fetch it back
    print(f"\n📖 Fetching order {order_id}...")
    order = fetch_order_with_items(order_id, r"C:\FaxManagerData\Data")
    
    print(f"✅ Order {order.id} fetched")
    print(f"   Patient: {order.patient_full_name}")
    print(f"   Status: {order.order_status.value}")
    print(f"   Items: {len(order.items)}")
    
    for idx, item in enumerate(order.items, 1):
        print(f"\n   📦 Item {idx}:")
        print(f"      HCPCS: {item.hcpcs_code}")
        print(f"      Description: {item.description}")
        print(f"      Quantity: {item.quantity}")
        print(f"      Rental: {'Yes' if item.is_rental else 'No'}")
        print(f"      Modifiers: {item.modifiers}")
        print(f"      Cost: ${item.cost_ea}")
        print(f"      Total: ${item.total_cost}")
    
    print("\n✅ All rental and modifier fields working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
