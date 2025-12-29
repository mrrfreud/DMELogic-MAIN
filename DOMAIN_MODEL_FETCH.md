# Domain Model Fetch - Order/OrderItem Implementation

## Overview

This document describes the **Order domain model** and `fetch_order_with_items()` function - the **single source of truth** for loading complete order data with typed, validated fields.

## Purpose

The Order domain model serves as the foundation for:
- **State Portal View**: Maps Order object fields directly to HCFA-1500 form boxes
- **Order Editor UI**: Load complete order without scattered SQL queries
- **Billing Workflows**: Full context for rentals, modifiers, same/similar checks
- **1500 Claim Generation**: Clean typed data for box-by-box mapping
- **Audit Views**: Standardized order representation
- **Print Workflows**: Template-friendly data structure
- **Refill Logic**: Fetch source order with items via domain model

## Architecture

### Two Model Types

**1. Input Models (Creation)**
```python
OrderInput     # For creating new orders (validation-focused)
OrderItemInput # For creating order items (validation-focused)
```

**2. Domain Models (Fetching)**
```python
Order      # For fetching complete orders (display-focused)
OrderItem  # For fetching order items (display-focused)
```

### Why Two Models?

- **OrderInput**: Validates required fields, business rules, patient/prescriber references
- **Order**: Represents complete fetched order with all fields, items list, computed properties
- **Different purposes**: Creation needs validation, fetching needs complete representation

## Domain Models

### OrderItem

```python
@dataclass
class OrderItem:
    """Order item domain model - single line item on an order."""
    
    # IDs
    id: int
    order_id: int
    
    # Item details
    rx_no: Optional[str]
    hcpcs_code: Optional[str]
    description: Optional[str]
    item_number: Optional[str]
    
    # Quantities
    quantity: int
    refills: int
    day_supply: int
    
    # Pricing (Decimal for precision)
    cost_ea: Optional[Decimal]
    total: Optional[Decimal]
    
    # Additional info
    pa_number: Optional[str]
    directions: Optional[str]
    last_filled_date: Optional[str]
    
    # Computed properties
    @property
    def has_refills_remaining(self) -> bool:
        """Check if item has refills available."""
        return self.refills > 0
    
    @property
    def formatted_total(self) -> str:
        """Return formatted dollar amount: '$60.48'"""
        if self.total is None:
            return "$0.00"
        return f"${self.total:.2f}"
```

### Order

```python
@dataclass
class Order:
    """Complete order domain model with all fields and items list."""
    
    # IDs & Dates
    id: int
    order_date: Optional[str]
    rx_date: Optional[str]
    
    # Patient info
    patient_last_name: Optional[str]
    patient_first_name: Optional[str]
    patient_dob: Optional[str]
    patient_phone: Optional[str]
    patient_address: Optional[str]
    
    # Prescriber info
    prescriber_name: Optional[str]
    prescriber_npi: Optional[str]
    
    # Billing info
    billing_type: Optional[str]  # Maps to billing_selection column
    order_status: OrderStatus    # Enum with safe fallback to PENDING
    
    # Insurance info
    primary_insurance: Optional[str]
    primary_insurance_id: Optional[str]
    
    # Diagnosis codes (ICD-10)
    icd_code_1: Optional[str]
    icd_code_2: Optional[str]
    icd_code_3: Optional[str]
    icd_code_4: Optional[str]
    icd_code_5: Optional[str]
    
    # Additional details
    doctor_directions: Optional[str]
    delivery_date: Optional[str]
    notes: Optional[str]
    
    # Items list
    items: list[OrderItem] = field(default_factory=list)
    
    # Computed properties (see below)
```

### Order Properties

```python
# Name formatting
@property
def patient_full_name(self) -> str:
    """Return 'LOPEZ, ANA' format."""

# Items checks
@property
def has_items(self) -> bool:
    """True if order has any items."""

@property
def total_items_count(self) -> int:
    """Sum of all item quantities: 4 + 175 + 2 + 1 = 182"""

# Financials
@property
def order_total(self) -> Decimal:
    """Sum of all item totals (Decimal precision)."""

@property
def formatted_order_total(self) -> str:
    """Formatted dollar amount: '$82.49'"""

# Clinical
@property
def has_diagnosis_codes(self) -> bool:
    """True if at least one ICD-10 code present."""
```

## fetch_order_with_items()

### Signature

```python
def fetch_order_with_items(
    order_id: int,
    folder_path: Optional[str] = None
) -> Optional[Order]:
    """
    Fetch a complete Order domain object with all items.
    
    Returns:
        Order object with items list, or None if not found
    """
```

### Implementation Details

#### 1. Schema Mapping

**orders table** → **Order fields**
```sql
SELECT 
    id, order_date, rx_date,
    patient_last_name, patient_first_name, patient_dob,
    patient_phone, patient_address,
    prescriber_name, prescriber_npi,
    billing_selection as billing_type,  -- Column alias!
    order_status,
    primary_insurance, primary_insurance_id,
    icd_code_1, icd_code_2, icd_code_3, icd_code_4, icd_code_5,
    doctor_directions, delivery_date, notes
FROM orders
WHERE id = ?
```

**order_items table** → **OrderItem fields**
```sql
SELECT 
    id, order_id, rx_no, hcpcs_code, description,
    item_number, 
    qty as quantity,  -- Column alias!
    refills, day_supply,
    cost_ea, total, pa_number, directions, last_filled_date
FROM order_items
WHERE order_id = ?
ORDER BY id
```

#### 2. Safe Type Conversions

**Decimal Conversion** (for monetary values):
```python
def _decimal_or_none(value: Any) -> Optional[Decimal]:
    """
    Safe conversion to Decimal.
    
    Handles:
    - None/empty → None
    - "12.34" → Decimal("12.34")
    - Invalid → None
    """
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None

# Usage
cost_ea = _decimal_or_none(row["cost_ea"])
total = _decimal_or_none(row["total"])
```

**Enum Conversion** (for order_status):
```python
def _safe_order_status(value: Any) -> OrderStatus:
    """
    Safe conversion to OrderStatus with fallback to PENDING.
    
    Handles:
    - "Ready" → OrderStatus.READY
    - "Delivered" → OrderStatus.DELIVERED
    - Invalid/None → OrderStatus.PENDING (fallback)
    """
    if value is None:
        return OrderStatus.PENDING
    
    try:
        return OrderStatus(value)
    except (ValueError, KeyError):
        return OrderStatus.PENDING

# Usage
order_status = _safe_order_status(row["order_status"])
```

**Integer Conversion** (for quantities):
```python
from .converters import safe_int

# Usage (all TEXT fields in order_items)
quantity = safe_int(row["quantity"], default=0)
refills = safe_int(row["refills"], default=0)
day_supply = safe_int(row["day_supply"], default=0)
```

#### 3. Full Implementation

```python
def fetch_order_with_items(
    order_id: int,
    folder_path: Optional[str] = None
) -> Optional[Order]:
    conn = get_connection("orders.db", folder_path=folder_path)
    conn.row_factory = sqlite3.Row
    
    try:
        cursor = conn.cursor()
        
        # 1. Fetch order header
        cursor.execute("""
            SELECT id, order_date, rx_date, ... 
            FROM orders WHERE id = ?
        """, (order_id,))
        
        order_row = cursor.fetchone()
        if not order_row:
            return None
        
        # 2. Fetch all items
        cursor.execute("""
            SELECT id, order_id, rx_no, ... 
            FROM order_items WHERE order_id = ? ORDER BY id
        """, (order_id,))
        
        item_rows = cursor.fetchall()
        
        # 3. Build OrderItem objects
        items = []
        for item_row in item_rows:
            item = OrderItem(
                id=item_row["id"],
                order_id=item_row["order_id"],
                # ... all fields with safe conversions
                cost_ea=_decimal_or_none(item_row["cost_ea"]),
                total=_decimal_or_none(item_row["total"]),
                quantity=safe_int(item_row["quantity"], default=0),
                # ...
            )
            items.append(item)
        
        # 4. Build complete Order object
        order = Order(
            id=order_row["id"],
            order_date=order_row["order_date"],
            # ... all fields
            order_status=_safe_order_status(order_row["order_status"]),
            items=items  # Complete items list
        )
        
        return order
        
    finally:
        conn.close()
```

## Usage Examples

### Basic Usage

```python
from dmelogic.db import fetch_order_with_items

# Fetch order with all items
order = fetch_order_with_items(order_id=28)

if order:
    print(f"Patient: {order.patient_full_name}")
    print(f"Status: {order.order_status.value}")
    print(f"Total: {order.formatted_order_total}")
    
    for item in order.items:
        print(f"  - {item.description}: {item.formatted_total}")
```

### State Portal Mapping (HCFA-1500)

```python
def map_order_to_1500_form(order: Order) -> Dict[str, str]:
    """Map Order domain model to HCFA-1500 form boxes."""
    
    return {
        # Box 1: Insurance type
        "box1": order.billing_type or "",
        
        # Box 2: Patient name
        "box2": order.patient_full_name,
        
        # Box 3: Patient DOB
        "box3": order.patient_dob or "",
        
        # Box 5: Patient address
        "box5": order.patient_address or "",
        
        # Box 7: Patient phone
        "box7": order.patient_phone or "",
        
        # Box 11: Primary insurance ID
        "box11": order.primary_insurance_id or "",
        
        # Box 17: Referring provider
        "box17": order.prescriber_name or "",
        
        # Box 17b: Referring provider NPI
        "box17b": order.prescriber_npi or "",
        
        # Box 21: Diagnosis codes
        "box21_1": order.icd_code_1 or "",
        "box21_2": order.icd_code_2 or "",
        "box21_3": order.icd_code_3 or "",
        "box21_4": order.icd_code_4 or "",
        
        # Box 24: Service lines (map from items)
        # ... map order.items to service lines
    }
```

### Order Editor UI

```python
class OrderEditorDialog(QDialog):
    def load_order(self, order_id: int):
        """Load order for editing."""
        order = fetch_order_with_items(order_id)
        
        if not order:
            QMessageBox.warning(self, "Error", "Order not found")
            return
        
        # Populate patient fields
        self.patient_name_field.setText(order.patient_full_name)
        self.patient_dob_field.setText(order.patient_dob or "")
        self.patient_phone_field.setText(order.patient_phone or "")
        
        # Populate prescriber fields
        self.prescriber_name_field.setText(order.prescriber_name or "")
        self.prescriber_npi_field.setText(order.prescriber_npi or "")
        
        # Populate diagnosis codes
        self.icd1_field.setText(order.icd_code_1 or "")
        self.icd2_field.setText(order.icd_code_2 or "")
        # ...
        
        # Populate items table
        self.items_table.setRowCount(len(order.items))
        for idx, item in enumerate(order.items):
            self.items_table.setItem(idx, 0, QTableWidgetItem(item.hcpcs_code or ""))
            self.items_table.setItem(idx, 1, QTableWidgetItem(item.description or ""))
            self.items_table.setItem(idx, 2, QTableWidgetItem(str(item.quantity)))
            self.items_table.setItem(idx, 3, QTableWidgetItem(item.formatted_total))
        
        # Update totals
        self.order_total_label.setText(order.formatted_order_total)
```

### Refill Workflow

```python
from dmelogic.workflows.refill_workflow_service import RefillWorkflowService

def create_refill_from_source_order(source_order_id: int):
    """Create refill order from source order."""
    
    # Fetch complete source order
    source_order = fetch_order_with_items(source_order_id)
    
    if not source_order:
        raise ValueError("Source order not found")
    
    # Check each item for refills
    refillable_items = [
        item for item in source_order.items 
        if item.has_refills_remaining
    ]
    
    if not refillable_items:
        raise ValueError("No items with refills remaining")
    
    # Use workflow service to create refill
    service = RefillWorkflowService()
    result = service.process_refill(
        source_order_id=source_order_id,
        folder_path="..."
    )
    
    return result
```

### Audit View

```python
def generate_order_audit_report(order_id: int) -> str:
    """Generate audit report for order."""
    
    order = fetch_order_with_items(order_id)
    
    if not order:
        return "Order not found"
    
    report = []
    report.append(f"Order #{order.id} Audit Report")
    report.append("=" * 80)
    report.append(f"Patient: {order.patient_full_name}")
    report.append(f"Status: {order.order_status.value}")
    report.append(f"Order Date: {order.order_date}")
    report.append(f"Rx Date: {order.rx_date}")
    
    if order.has_diagnosis_codes:
        report.append("\nDiagnosis Codes:")
        codes = [c for c in [order.icd_code_1, order.icd_code_2, 
                             order.icd_code_3, order.icd_code_4, 
                             order.icd_code_5] if c]
        for idx, code in enumerate(codes, 1):
            report.append(f"  {idx}. {code}")
    
    report.append(f"\nItems ({order.total_items_count} total qty):")
    for idx, item in enumerate(order.items, 1):
        report.append(f"  {idx}. {item.description}")
        report.append(f"     HCPCS: {item.hcpcs_code} | Qty: {item.quantity}")
        report.append(f"     Total: {item.formatted_total}")
        if item.has_refills_remaining:
            report.append(f"     Refills: {item.refills} remaining")
    
    report.append(f"\nOrder Total: {order.formatted_order_total}")
    
    return "\n".join(report)
```

## Testing

### Test Results

**Single Item Order (Order #1)**
```
✅ Order fetched successfully
Patient: LOPEZ, ANA
DOB: 03/12/1964
Status: Ready
Items: 1 (4 qty)
Order Total: $60.48
```

**Multi-Item Order (Order #28)**
```
✅ Multi-item order fetched successfully
Patient: MCCULLOUGH, TRISTAN
Status: Delivered
Items: 4 (178 qty)
Order Total: $82.49

Items:
  1. MEDLINE CILD BRIEF SIZE 6 P (qty: 0, 6 refills) - $0.00
  2. FITRIGHT UNDERPADS (qty: 175, 6 refills) - $50.75
  3. REUSASABLE UNDER PAD 34X36 PERFORMAX (qty: 2, 6 refills) - $27.14
  4. GLOVES VYNIL LARGE (qty: 1, 6 refills) - $4.60
```

### Test Files

**test_fetch_order.py** - Single item test
**test_multi_item_order.py** - Multi-item test

Both tests confirm:
- ✅ Order objects load correctly with all fields
- ✅ Items list populates with proper types (Decimal, int)
- ✅ Domain properties work (has_items, order_total, etc.)
- ✅ Safe conversions handle TEXT columns and invalid data
- ✅ Enum conversion with PENDING fallback

## Integration Points

### Current Integrations

1. **dmelogic/db/__init__.py**
   - Exports: `Order`, `OrderItem`, `fetch_order_with_items`
   - Available for import: `from dmelogic.db import fetch_order_with_items, Order`

### Future Integrations

1. **state_portal_view.py**
   - Replace dict-based order loading with `fetch_order_with_items()`
   - Map Order object to 1500 form boxes

2. **Order Editor UI** (new feature)
   - Load orders via `fetch_order_with_items()`
   - Edit patient/prescriber/items fields
   - Save via workflow services

3. **Billing Module** (future)
   - Consume Order objects for claim generation
   - Rental tracking via Order.items list
   - Same/similar checks with complete order context

4. **Reporting** (future)
   - Use Order domain model for clean, typed data access
   - Generate audit reports, financial summaries

## Benefits

### Type Safety
- **Decimal** for monetary values (no float precision errors)
- **OrderStatus** enum (validated status values)
- **Optional[str]** for nullable fields (explicit optionality)

### Single Source of Truth
- One function to fetch complete orders
- No scattered SQL queries across codebase
- Consistent data structure everywhere

### Business Logic Encapsulation
- Computed properties on domain models
- `has_refills_remaining`, `order_total`, `patient_full_name`
- Logic lives with the data

### Future-Proof
- Easy to add new properties without changing callers
- Clean foundation for state portal, 1500 forms, billing
- Extensible for rentals, modifiers, compliance checks

## Schema Notes

### Column Name Mapping

**orders table:**
- `billing_selection` → `billing_type` (aliased in SELECT)
- No `prescriber_id` column (denormalized design)
- Stores prescriber_name, prescriber_npi directly

**order_items table:**
- `qty` → `quantity` (aliased in SELECT)
- `id` column (not rowid)
- All numeric fields stored as TEXT

### Safe Conversions Required

- **TEXT → int**: Use `safe_int(value, default=0)`
- **TEXT → Decimal**: Use `_decimal_or_none(value)`
- **TEXT → OrderStatus**: Use `_safe_order_status(value)`

## Summary

The Order domain model and `fetch_order_with_items()` function provide:

1. **Complete order representation** with typed fields and items list
2. **Single source of truth** for order data access
3. **Type-safe conversions** for Decimal, enum, int fields
4. **Business logic properties** (totals, refill checks, name formatting)
5. **Foundation for advanced features** (state portal, billing, 1500 forms)

**Usage Pattern:**
```python
from dmelogic.db import fetch_order_with_items

order = fetch_order_with_items(order_id)
# Now you have a complete, typed Order object
# with all patient, prescriber, insurance, and item data
# ready for display, editing, billing, or reporting
```

**Next Steps:**
- Integrate into state portal view (1500 form mapping)
- Build order editor UI using Order model
- Extend for billing workflows (rentals, modifiers)
- Add to reporting/audit views
