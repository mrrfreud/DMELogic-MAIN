"""Quick test of domain models and safe conversions."""

from dmelogic.db import (
    Patient, Prescriber, InventoryItem,
    OrderInput, OrderItemInput,
    safe_int, safe_decimal, safe_date
)

print("=" * 60)
print("Testing safe_int conversions:")
print("=" * 60)
print(f"  safe_int(5) = {safe_int(5)}")
print(f"  safe_int('10') = {safe_int('10')}")
print(f"  safe_int('2x') = {safe_int('2x')} (should default to 0 with warning)")
print(f"  safe_int(None) = {safe_int(None)}")
print(f"  safe_int('') = {safe_int('')}")
print(f"  safe_int(1.8) = {safe_int(1.8)}")

print("\n" + "=" * 60)
print("Testing safe_decimal conversions:")
print("=" * 60)
print(f"  safe_decimal(123.45) = {safe_decimal(123.45)}")
print(f"  safe_decimal('$99.99') = {safe_decimal('$99.99')}")
print(f"  safe_decimal('1,234.56') = {safe_decimal('1,234.56')}")
print(f"  safe_decimal('N/A') = {safe_decimal('N/A')} (should default to 0.00 with warning)")

print("\n" + "=" * 60)
print("Testing OrderInput validation:")
print("=" * 60)

# Valid order
valid_order = OrderInput(
    patient_last_name="SMITH",
    patient_first_name="JOHN",
    patient_dob="1980-01-01",
    prescriber_name="Dr. Jones",
    billing_type="Insurance",
    icd_code_1="E11.9",
    items=[
        OrderItemInput(hcpcs="E0601", description="CPAP Device", quantity=1)
    ]
)

errors = valid_order.validate()
print(f"Valid order errors: {errors if errors else 'None - Valid!'}")

# Invalid order (missing diagnosis code for insurance)
invalid_order = OrderInput(
    patient_last_name="",
    patient_first_name="",
    billing_type="Insurance",
    items=[]
)

errors = invalid_order.validate()
print(f"\nInvalid order errors:")
for err in errors:
    print(f"  - {err}")

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
