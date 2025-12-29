# Domain Model Implementation - Complete

## Status: ✅ COMPLETE

**Date Completed**: 2025-11-08  
**Purpose**: Introduce Order/OrderItem domain models and `fetch_order_with_items()` as foundation for state portal, 1500 forms, order editor, and billing.

---

## What Was Implemented

### 1. Domain Models (dmelogic/db/models.py)

**OrderItem Dataclass** (lines 420-459)
- All fields: id, order_id, rx_no, hcpcs_code, description, item_number, quantity, refills, day_supply, cost_ea, total, pa_number, directions, last_filled_date
- Properties: `has_refills_remaining`, `formatted_total`
- Purpose: Represents single line item on an order

**Order Dataclass** (lines 462-551)
- Patient fields: patient_last_name, patient_first_name, patient_dob, patient_phone, patient_address
- Prescriber fields: prescriber_name, prescriber_npi
- Billing fields: billing_type, order_status (enum), primary_insurance, primary_insurance_id
- Clinical fields: icd_code_1 through icd_code_5, doctor_directions
- Items: `items: list[OrderItem]` field
- Properties: `patient_full_name`, `has_items`, `total_items_count`, `order_total`, `formatted_order_total`, `has_diagnosis_codes`
- Purpose: Complete order representation with all data

### 2. Repository Method (dmelogic/db/orders.py)

**fetch_order_with_items(order_id, folder_path)** (lines 810-969)
- Fetches order header from `orders` table
- Fetches all items from `order_items` table
- Safe type conversions:
  - `_decimal_or_none()`: TEXT → Decimal for monetary values
  - `_safe_order_status()`: TEXT → OrderStatus enum with PENDING fallback
  - `safe_int()`: TEXT → int for quantities
- Returns: `Order | None` (fully hydrated domain object)

### 3. Helper Functions (dmelogic/db/orders.py)

**_decimal_or_none(value)** (lines 812-826)
- Safe conversion to Decimal
- Handles None, empty string, invalid values
- Returns None on failure (no exceptions)

**_safe_order_status(value)** (lines 829-843)
- Safe conversion to OrderStatus enum
- Fallback to OrderStatus.PENDING for invalid/None
- Prevents enum ValueError crashes

### 4. Exports (dmelogic/db/__init__.py)

Added to exports:
- `Order` (domain model)
- `OrderItem` (domain model)
- `fetch_order_with_items` (repository method)

Usage:
```python
from dmelogic.db import fetch_order_with_items, Order, OrderItem
```

---

## Schema Mappings

### orders table → Order model

| Column | Field | Notes |
|--------|-------|-------|
| billing_selection | billing_type | Aliased in SELECT |
| patient_last_name | patient_last_name | - |
| patient_first_name | patient_first_name | - |
| patient_dob | patient_dob | - |
| patient_phone | patient_phone | - |
| patient_address | patient_address | - |
| prescriber_name | prescriber_name | Denormalized design |
| prescriber_npi | prescriber_npi | Denormalized design |
| order_status | order_status | Safe enum conversion |
| primary_insurance | primary_insurance | - |
| primary_insurance_id | primary_insurance_id | - |
| icd_code_1..5 | icd_code_1..5 | Diagnosis codes |
| doctor_directions | doctor_directions | - |
| delivery_date | delivery_date | - |
| notes | notes | - |

### order_items table → OrderItem model

| Column | Field | Notes |
|--------|-------|-------|
| id | id | PK |
| order_id | order_id | FK to orders |
| qty | quantity | Aliased, TEXT → int |
| refills | refills | TEXT → int |
| day_supply | day_supply | TEXT → int |
| cost_ea | cost_ea | TEXT → Decimal |
| total | total | TEXT → Decimal |
| hcpcs_code | hcpcs_code | - |
| description | description | - |
| item_number | item_number | - |
| rx_no | rx_no | - |
| pa_number | pa_number | - |
| directions | directions | - |
| last_filled_date | last_filled_date | - |

---

## Test Results

**Test File**: `test_domain_model.py`

### All Tests Passed ✅

```
TEST 1: Basic Order Fetch (Order #1)
  ✅ Order #1 fetched
  ✅ Patient: LOPEZ, ANA
  ✅ Status: Ready
  ✅ Items: 1

TEST 2: Order Items (Multi-item Order #28)
  ✅ Order #28 has 4 items
  ✅ All items have correct types (int, Decimal)

TEST 3: Order Domain Properties
  ✅ patient_full_name: LOPEZ, ANA
  ✅ has_items: True
  ✅ total_items_count: 4
  ✅ order_total: $60.48
  ✅ has_diagnosis_codes: True

TEST 4: OrderItem Domain Properties
  ✅ has_refills_remaining: True
  ✅ formatted_total: $0.00

TEST 5: Safe Type Conversions
  ✅ Tested 3 orders
  ✅ All OrderStatus values → enum
  ✅ All TEXT fields → int/Decimal
  ✅ No conversion errors

TEST 6: Non-Existent Order Handling
  ✅ Returns None gracefully
```

---

## Usage Examples

### Basic Usage

```python
from dmelogic.db import fetch_order_with_items

order = fetch_order_with_items(order_id=1)

if order:
    print(f"Patient: {order.patient_full_name}")
    print(f"Status: {order.order_status.value}")
    print(f"Total: {order.formatted_order_total}")
    
    for item in order.items:
        print(f"  - {item.description}: {item.formatted_total}")
```

### State Portal (1500 Form Mapping)

```python
def map_order_to_1500_form(order: Order) -> dict:
    return {
        "box2": order.patient_full_name,
        "box3": order.patient_dob,
        "box5": order.patient_address,
        "box7": order.patient_phone,
        "box11": order.primary_insurance_id,
        "box17": order.prescriber_name,
        "box17b": order.prescriber_npi,
        "box21_1": order.icd_code_1,
        "box21_2": order.icd_code_2,
        # ... map items to service lines
    }
```

### Order Editor UI

```python
class OrderEditorDialog(QDialog):
    def load_order(self, order_id: int):
        order = fetch_order_with_items(order_id)
        
        # Populate fields from order object
        self.patient_name_field.setText(order.patient_full_name)
        self.prescriber_npi_field.setText(order.prescriber_npi or "")
        
        # Populate items table
        for idx, item in enumerate(order.items):
            self.items_table.setItem(idx, 0, QTableWidgetItem(item.hcpcs_code))
            self.items_table.setItem(idx, 1, QTableWidgetItem(item.description))
            # ...
```

---

## Integration Points

### Ready to Use

1. **dmelogic/db/__init__.py**
   - `fetch_order_with_items` exported
   - `Order`, `OrderItem` exported
   - Available: `from dmelogic.db import fetch_order_with_items`

### Next Steps (Future Work)

1. **state_portal_view.py**
   - Replace dict-based order loading
   - Use Order object for 1500 form mapping

2. **Order Editor UI** (new feature)
   - Build UI with QDialog
   - Load via `fetch_order_with_items()`
   - Edit patient/prescriber/items fields

3. **Billing Module** (future)
   - Consume Order objects for claims
   - Rental tracking via Order.items
   - Same/similar checks with full context

4. **Reporting** (future)
   - Use Order domain model for reports
   - Clean, typed data access

---

## Benefits Delivered

### 1. Type Safety
- **Decimal** for monetary values (no float errors)
- **OrderStatus** enum (validated statuses)
- **Optional[str]** for nullable fields (explicit)

### 2. Single Source of Truth
- One function: `fetch_order_with_items()`
- No scattered SQL queries
- Consistent data structure everywhere

### 3. Business Logic Encapsulation
- Computed properties on domain models
- `order_total`, `has_refills_remaining`, `patient_full_name`
- Logic lives with the data

### 4. Future-Proof
- Easy to add properties without changing callers
- Foundation for state portal, 1500 forms, billing
- Extensible for rentals, modifiers, compliance

---

## Files Modified

1. **dmelogic/db/models.py**
   - Added: OrderItem dataclass (lines 420-459)
   - Added: Order dataclass (lines 462-551)
   - Total: 131 lines of domain model code

2. **dmelogic/db/orders.py**
   - Added: `_decimal_or_none()` helper (lines 812-826)
   - Added: `_safe_order_status()` helper (lines 829-843)
   - Added: `fetch_order_with_items()` (lines 845-969)
   - Updated: Imports (Decimal, Order, OrderItem, OrderStatus)
   - Total: 160 lines of repository code

3. **dmelogic/db/__init__.py**
   - Added: Import from orders module
   - Added: Export `fetch_order_with_items`
   - Total: 3 lines changed

---

## Documentation

1. **DOMAIN_MODEL_FETCH.md** (650+ lines)
   - Complete implementation guide
   - Usage examples
   - Schema mappings
   - Integration patterns
   - Test results

2. **test_domain_model.py** (170+ lines)
   - 6 comprehensive tests
   - All tests passing
   - Covers: fetch, items, properties, conversions, edge cases

---

## Summary

**What**: Introduced Order/OrderItem domain models and `fetch_order_with_items()` repository method.

**Why**: Foundation for state portal mapping, 1500 forms, order editor, billing, and all future order-centric features.

**How**: 
- Added typed dataclasses with computed properties
- Implemented single repository method with safe conversions
- Comprehensive test suite (all passing)
- Complete documentation

**Result**: ✅ Ready to use for state portal, UI, billing integration

**Next Steps**: 
- Integrate into state portal view (1500 mapping)
- Build order editor UI
- Extend for billing workflows
