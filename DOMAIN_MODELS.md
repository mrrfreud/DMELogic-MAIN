# Domain Models - DME Logic

## Overview

DME Logic uses **rich domain models** based on dataclasses to represent business entities. These models:

1. **Provide type safety** - IDE autocomplete, static analysis
2. **Encapsulate business rules** - Validation, calculations, state transitions
3. **Decouple layers** - Database representation ≠ business representation
4. **Enable rich behavior** - Methods, properties, domain logic
5. **Serve as contracts** - Clear interface between layers

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  UI Layer                            │
│  Consumes: Order, Patient, Prescriber domain models │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│              Service Layer                           │
│  Operates on: Domain models                          │
│  Returns: Domain models                              │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│            Repository Layer                          │
│  Maps: sqlite3.Row → Domain Model                    │
│  Returns: Domain models (not raw rows!)              │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│            Database Layer                            │
│  Storage: SQLite tables with schema                  │
└──────────────────────────────────────────────────────┘
```

---

## Domain Model Catalog

### Order Domain

| Model | Purpose | Key Business Rules |
|-------|---------|-------------------|
| **Order** | DME order aggregate root | Status transitions, validation, refill tracking |
| **OrderItem** | Line item in order | Quantity rules, refill calculations, pricing |
| **OrderStatus** | Order status enum | State machine for order lifecycle |

### Patient Domain

| Model | Purpose | Key Business Rules |
|-------|---------|-------------------|
| **Patient** | Patient entity | Demographics, insurance, contact validation |
| **PatientInsurance** | Insurance coverage | Coverage dates, policy validation |
| **PatientStatus** | Patient status enum | Active/Inactive/Deceased |

### Prescriber Domain

| Model | Purpose | Key Business Rules |
|-------|---------|-------------------|
| **Prescriber** | Healthcare provider | NPI validation, credentials, can_prescribe rules |
| **PrescriberStatus** | Prescriber status enum | Active/Inactive/Suspended |

### Inventory Domain

| Model | Purpose | Key Business Rules |
|-------|---------|-------------------|
| **InventoryItem** | DME product | Stock levels, reorder points, pricing, reservation |
| **InventoryStatus** | Item status enum | Active/Discontinued/Out of Stock |

### Insurance Domain

| Model | Purpose | Key Business Rules |
|-------|---------|-------------------|
| **InsurancePolicy** | Insurance company/plan | Refill rules, auth requirements, coverage limits |
| **InsuranceType** | Insurance type enum | Medicare/Medicaid/Commercial rules |

---

## Key Patterns

### Pattern 1: Aggregate Root

**Order** is an aggregate root that contains **OrderItems**:

```python
@dataclass
class Order:
    """Order aggregate root."""
    items: List[OrderItem] = field(default_factory=list)
    
    def add_item(self, item: OrderItem) -> None:
        """Add item with validation."""
        errors = item.validate()
        if errors:
            raise ValueError(f"Invalid item: {'; '.join(errors)}")
        item.order_id = self.id
        self.items.append(item)
    
    def remove_item(self, item_id: int) -> bool:
        """Remove item from order."""
        # Items managed through Order, not directly
```

**Business Rule**: Items are always accessed through the Order aggregate.

### Pattern 2: Business Rule Validation

All models have `validate()` method that returns error list:

```python
def validate(self) -> List[str]:
    """Validate business rules."""
    errors = []
    
    if not self.patient_last_name:
        errors.append("Patient last name is required")
    
    if self.billing_selection == "Insurance" and not self.primary_insurance:
        errors.append("Primary insurance required for insurance billing")
    
    # Validate all items
    for item in self.items:
        item_errors = item.validate()
        errors.extend(item_errors)
    
    return errors
```

**Usage**:
```python
order = Order(...)
errors = order.validate()
if errors:
    raise ValueError(f"Order invalid: {'; '.join(errors)}")
```

### Pattern 3: Calculated Properties

Models use `@property` for calculated fields:

```python
@dataclass
class OrderItem:
    refills: int = 0
    last_filled_date: Optional[date] = None
    day_supply: int = 30
    
    @property
    def next_refill_date(self) -> Optional[date]:
        """Calculate when refill is due."""
        if self.last_filled_date and self.day_supply > 0:
            return self.last_filled_date + timedelta(days=self.day_supply)
        return None
    
    @property
    def is_refillable(self) -> bool:
        """Check if eligible for refill."""
        if self.refills <= 0:
            return False
        next_date = self.next_refill_date
        return next_date is None or date.today() >= next_date
```

**Benefits**: No need to store calculated values in database.

### Pattern 4: Business Behavior Methods

Models encapsulate domain logic:

```python
@dataclass
class OrderItem:
    def use_refill(self, fill_date: Optional[date] = None) -> None:
        """Use one refill and update tracking."""
        if self.refills <= 0:
            raise ValueError(f"No refills remaining for {self.hcpcs_code}")
        
        self.refills -= 1
        self.last_filled_date = fill_date or date.today()

@dataclass
class InventoryItem:
    def reserve(self, quantity: int) -> None:
        """Reserve quantity for order."""
        if quantity > self.quantity_available:
            raise ValueError(f"Cannot reserve {quantity} - only {self.quantity_available} available")
        self.quantity_reserved += quantity
```

### Pattern 5: Enum-Based State Machines

Enums encode valid states and transitions:

```python
class OrderStatus(Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    
    @property
    def is_active(self) -> bool:
        return self not in (OrderStatus.CANCELLED, OrderStatus.DELIVERED)
    
    @property
    def can_be_edited(self) -> bool:
        return self in (OrderStatus.PENDING, OrderStatus.ON_HOLD)

@dataclass
class Order:
    order_status: OrderStatus = OrderStatus.PENDING
    
    def change_status(self, new_status: OrderStatus, reason: str = "") -> None:
        """Change status with validation."""
        if not self.order_status.can_be_edited and new_status != OrderStatus.CANCELLED:
            raise ValueError(f"Cannot change from {self.order_status} to {new_status}")
        
        self.order_status = new_status
```

---

## Repository Mapping Pattern

Repositories map database rows to domain models:

### ❌ Old Way (Returning Raw Rows)

```python
def fetch_order_by_id(order_id: int) -> Optional[sqlite3.Row]:
    """Returns raw sqlite3.Row - requires dict access everywhere."""
    conn = get_connection("orders.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    return cur.fetchone()  # Returns sqlite3.Row

# Usage - error prone!
row = fetch_order_by_id(123)
print(row["patient_name"])  # Typo-prone, no autocomplete
```

### ✅ New Way (Returning Domain Models)

```python
def fetch_order_by_id(order_id: int) -> Optional[Order]:
    """Returns rich Order domain model."""
    conn = get_connection("orders.db")
    cur = conn.cursor()
    
    # Fetch order header
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    if not row:
        return None
    
    # Map to domain model
    order = Order(
        id=row["id"],
        rx_date=parse_date(row["rx_date"]),
        order_date=parse_date(row["order_date"]),
        patient_name=row["patient_name"] or "",
        patient_first_name=row["patient_first_name"] or "",
        patient_last_name=row["patient_last_name"] or "",
        patient_dob=parse_date(row["patient_dob"]),
        prescriber_name=row["prescriber_name"] or "",
        prescriber_npi=row["prescriber_npi"] or "",
        order_status=OrderStatus(row["order_status"]),
        # ... map all fields ...
    )
    
    # Fetch order items
    cur.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    for item_row in cur.fetchall():
        item = OrderItem(
            id=item_row["rowid"],
            order_id=order_id,
            hcpcs_code=item_row["hcpcs_code"] or "",
            description=item_row["description"] or "",
            quantity=safe_int(item_row["qty"], 1),
            day_supply=safe_int(item_row["day_supply"], 30),
            refills=safe_int(item_row["refills"], 0),
            cost_ea=parse_decimal(item_row["cost_ea"]),
            total=parse_decimal(item_row["total"]),
            last_filled_date=parse_date(item_row["last_filled_date"]),
        )
        order.items.append(item)
    
    return order

# Usage - type safe, autocomplete works!
order = fetch_order_by_id(123)
if order:
    print(order.patient_name)  # Type-checked property
    print(order.order_total)   # Calculated property
    if order.has_refillable_items:  # Business logic
        # ... process refills ...
```

---

## DME Business Rules Encoded in Models

### Medicare/Medicaid Refill Rules

**InsurancePolicy model**:

```python
def get_refill_earliest_date(self, last_filled: date, day_supply: int) -> date:
    """Calculate earliest refill date based on insurance type."""
    if self.is_government:
        # Medicare/Medicaid: 75% rule
        days_until_refill = int(day_supply * 0.75)
    else:
        # Commercial: 80% rule
        days_until_refill = int(day_supply * 0.80)
    
    return last_filled + timedelta(days=days_until_refill)

def is_refill_allowed(
    self,
    last_filled: date,
    day_supply: int,
    quantity: int,
) -> tuple[bool, str]:
    """Check refill eligibility with insurance-specific rules."""
    earliest_date = self.get_refill_earliest_date(last_filled, day_supply)
    if date.today() < earliest_date:
        return (False, f"Too soon - eligible {earliest_date}")
    
    if self.max_quantity_per_month > 0 and quantity > self.max_quantity_per_month:
        return (False, f"Exceeds max quantity {self.max_quantity_per_month}")
    
    return (True, "")
```

### HCPCS-Specific Rules

**OrderItem validation**:

```python
def validate(self) -> List[str]:
    errors = []
    
    # Certain HCPCS codes require prior auth
    if self.hcpcs_code.startswith("E") and not self.pa_number:
        errors.append(f"Prior authorization required for {self.hcpcs_code}")
    
    # Wheelchair codes have special day supply rules
    if self.hcpcs_code.startswith("K0") and self.day_supply != 30:
        errors.append("Wheelchair codes must have 30-day supply")
    
    return errors
```

### Inventory Reservation Rules

**InventoryItem model**:

```python
def reserve(self, quantity: int) -> None:
    """Reserve inventory for an order."""
    if quantity > self.quantity_available:
        raise ValueError(
            f"Cannot reserve {quantity} units - only {self.quantity_available} available"
        )
    
    self.quantity_reserved += quantity

def fulfill(self, quantity: int) -> None:
    """Fulfill order and reduce stock."""
    if quantity > self.quantity_reserved:
        raise ValueError("Cannot fulfill unreserved quantity")
    
    if quantity > self.quantity_on_hand:
        raise ValueError("Insufficient stock")
    
    self.quantity_on_hand -= quantity
    self.quantity_reserved -= quantity
```

---

## Usage Examples

### Example 1: Create Order with Validation

```python
from dmelogic.models import Order, OrderItem, OrderStatus

# Create order
order = Order(
    patient_last_name="Smith",
    patient_first_name="John",
    prescriber_name="Dr. Johnson",
    prescriber_npi="1234567890",
    primary_insurance="Medicare Part B",
    billing_selection="Insurance",
    icd_code_1="E11.9",  # Type 2 diabetes
)

# Add items
item = OrderItem(
    hcpcs_code="A4253",
    description="Blood glucose test strips",
    quantity=100,
    day_supply=30,
    refills=11,  # 12 fills total (1 year)
)

order.add_item(item)

# Validate before saving
errors = order.validate()
if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    # Save via service
    order_id = order_service.create_order(order)
```

### Example 2: Process Refill with Rules

```python
from dmelogic.models import InsurancePolicy, InsuranceType
from datetime import date

# Get insurance policy
insurance = InsurancePolicy(
    name="Medicare Part B",
    insurance_type=InsuranceType.MEDICARE,
    refill_min_days_supply=30,
)

# Get order item
item = fetch_order_item(item_id=456)

# Check if refill is allowed
is_allowed, reason = insurance.is_refill_allowed(
    last_filled=item.last_filled_date,
    day_supply=item.day_supply,
    quantity=item.quantity,
)

if not is_allowed:
    print(f"Refill denied: {reason}")
else:
    # Process refill
    item.use_refill(fill_date=date.today())
    save_order_item(item)
```

### Example 3: Reserve Inventory

```python
from dmelogic.models import InventoryItem

# Get inventory item
inventory = fetch_inventory_by_hcpcs("A4253")

# Check availability
if not inventory.is_in_stock:
    print(f"Item out of stock: {inventory.status.value}")
elif inventory.quantity_available < order_quantity:
    print(f"Insufficient stock: {inventory.quantity_available} available, {order_quantity} needed")
else:
    # Reserve for order
    try:
        inventory.reserve(order_quantity)
        save_inventory(inventory)
        print(f"Reserved {order_quantity} units")
    except ValueError as e:
        print(f"Reservation failed: {e}")
```

### Example 4: State Portal View (1500 Form)

```python
from dmelogic.models import Order, InsurancePolicy

def generate_1500_form(order_id: int) -> dict:
    """Generate CMS-1500 claim form data."""
    order = fetch_order_by_id(order_id)  # Returns Order domain model
    insurance = fetch_insurance_by_name(order.primary_insurance)
    
    # All fields are type-safe properties
    return {
        "box_1": insurance.insurance_type.value,
        "box_2": order.patient_name,
        "box_3": order.patient_dob.strftime("%m/%d/%Y") if order.patient_dob else "",
        "box_5": order.patient_address,
        "box_9": order.primary_insurance_id,
        "box_17": order.prescriber_name,
        "box_17a": order.prescriber_npi,
        "box_21": ", ".join(order.icd_codes),  # Calculated property
        "box_24": [
            {
                "date_of_service": item.last_filled_date,
                "hcpcs": item.hcpcs_code,
                "description": item.description,
                "quantity": item.quantity,
                "charges": str(item.total),
            }
            for item in order.items
        ],
        "box_28": str(order.order_total),  # Calculated property
    }
```

---

## Migration Guide

### Step 1: Update Repositories to Return Models

**Before**:
```python
def fetch_patient_by_id(patient_id: int) -> Optional[sqlite3.Row]:
    conn = get_connection("patients.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    return cur.fetchone()
```

**After**:
```python
from dmelogic.models import Patient

def fetch_patient_by_id(patient_id: int) -> Optional[Patient]:
    conn = get_connection("patients.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    row = cur.fetchone()
    if not row:
        return None
    
    return Patient(
        id=row["id"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        date_of_birth=parse_date(row["date_of_birth"]),
        phone=row["phone"] or "",
        # ... map all fields ...
    )
```

### Step 2: Update Services to Use Models

**Before**:
```python
def create_order_from_wizard(result: OrderWizardResult) -> int:
    # Manual SQL with raw values
    conn = get_connection("orders.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (patient_name, ...) VALUES (?, ...)",
        (result.patient_name, ...)
    )
    return cur.lastrowid
```

**After**:
```python
from dmelogic.models import Order, OrderItem

def create_order_from_wizard(result: OrderWizardResult) -> int:
    # Build domain model
    order = Order(
        patient_name=result.patient_name,
        prescriber_name=result.prescriber_name,
        # ... map fields ...
    )
    
    for item_data in result.items:
        item = OrderItem(
            hcpcs_code=item_data.hcpcs,
            quantity=item_data.quantity,
            # ... map fields ...
        )
        order.add_item(item)  # Validates automatically
    
    # Validate before persisting
    errors = order.validate()
    if errors:
        raise ValueError(f"Invalid order: {'; '.join(errors)}")
    
    # Save via repository
    return save_order(order)
```

### Step 3: Update UI to Use Models

**Before**:
```python
# UI accessing raw dict/row
row = fetch_order_by_id(order_id)
patient_label.setText(row["patient_name"])
status_combo.setCurrentText(row["order_status"])
```

**After**:
```python
# UI accessing domain model
order = fetch_order_by_id(order_id)  # Returns Order model
patient_label.setText(order.patient_name)  # Type-safe property
status_combo.setCurrentText(order.order_status.value)  # Enum value

# Use calculated properties
total_label.setText(f"${order.order_total}")  # Calculated
if order.has_refillable_items:  # Business logic
    refill_button.setEnabled(True)
```

---

## Benefits

### Type Safety
```python
# ❌ Old way - typos slip through
row["patinet_name"]  # Oops! Silent bug

# ✅ New way - IDE catches errors
order.patinet_name  # IDE error: No such attribute
```

### Autocomplete
```python
# ❌ Old way - no autocomplete
row["???"]  # What fields exist?

# ✅ New way - full autocomplete
order.  # IDE shows all properties and methods
```

### Business Logic Centralization
```python
# ❌ Old way - logic scattered everywhere
if row["refills"] > 0:
    last_filled = datetime.strptime(row["last_filled_date"], "%Y-%m-%d").date()
    next_refill = last_filled + timedelta(days=int(row["day_supply"]))
    if date.today() >= next_refill:
        # ... refillable ...

# ✅ New way - logic in one place
if item.is_refillable:  # Property encapsulates all logic
    # ... refillable ...
```

### Validation Consistency
```python
# ❌ Old way - validation duplicated
if not patient_last_name:
    raise ValueError("Last name required")
if billing == "Insurance" and not insurance:
    raise ValueError("Insurance required")
# ... repeated in UI, service, repository ...

# ✅ New way - validation in model
errors = order.validate()  # Same everywhere
if errors:
    show_errors(errors)
```

---

## Best Practices

### ✅ DO

- Return domain models from repositories
- Use models in service layer
- Validate using `model.validate()`
- Use calculated properties for derived data
- Encode business rules in model methods
- Use enums for states and types
- Map database rows to models once (in repository)

### ❌ DON'T

- Return `sqlite3.Row` or `dict` from repositories
- Scatter business logic across layers
- Duplicate validation logic
- Store calculated values in database
- Access database directly from models
- Use string literals for states/enums
- Pass raw database rows to UI

---

## Testing Domain Models

```python
import unittest
from dmelogic.models import Order, OrderItem, OrderStatus

class TestOrderModel(unittest.TestCase):
    def test_order_validation_requires_patient_name(self):
        """Order without patient name fails validation."""
        order = Order(patient_last_name="")
        errors = order.validate()
        self.assertIn("Patient last name is required", errors)
    
    def test_order_item_refill_calculation(self):
        """Next refill date calculated correctly."""
        item = OrderItem(
            last_filled_date=date(2025, 1, 1),
            day_supply=30,
        )
        self.assertEqual(item.next_refill_date, date(2025, 1, 31))
    
    def test_order_item_use_refill(self):
        """Using refill decrements count and updates date."""
        item = OrderItem(refills=3, last_filled_date=date(2025, 1, 1))
        item.use_refill(fill_date=date(2025, 2, 1))
        
        self.assertEqual(item.refills, 2)
        self.assertEqual(item.last_filled_date, date(2025, 2, 1))
    
    def test_order_status_transitions(self):
        """Order status follows business rules."""
        order = Order(order_status=OrderStatus.PENDING)
        
        # Can change from PENDING
        order.change_status(OrderStatus.VERIFIED)
        self.assertEqual(order.order_status, OrderStatus.VERIFIED)
        
        # Can't change from DELIVERED
        order.order_status = OrderStatus.DELIVERED
        with self.assertRaises(ValueError):
            order.change_status(OrderStatus.PENDING)
```

---

## Future Enhancements

1. **Event Sourcing**: Emit domain events (OrderCreated, RefillProcessed)
2. **Domain Services**: Complex operations involving multiple aggregates
3. **Specifications**: Reusable query criteria as objects
4. **Value Objects**: Immutable domain concepts (Address, Money, Quantity)
5. **Factory Methods**: Complex object creation logic
6. **Repository Interfaces**: Abstract repository contracts

---

## Resources

- **Domain Models**: `dmelogic/models/*.py`
- **Model Usage**: See repositories in `dmelogic/db/*.py`
- **Business Rules**: Encoded in model `validate()` and property methods
- **Architecture**: See `ARCHITECTURE.md` for overall design
