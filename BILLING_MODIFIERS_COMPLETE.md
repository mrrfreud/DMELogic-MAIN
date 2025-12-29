# Billing Modifiers Implementation - Complete

**Date**: December 6, 2025  
**Status**: ✅ Complete - Database, Models, and Business Logic Ready

---

## Overview

Added comprehensive billing modifier support to order items with automatic rental month tracking and K modifier assignment for HCFA-1500 forms and State Portal submissions.

### Features Implemented

✅ **4 Modifier Fields** per order item (modifier1-4)  
✅ **Rental Month Tracking** for automatic K modifier progression  
✅ **Auto-Assignment Logic** for rental equipment (RR + K modifiers)  
✅ **Validation** to ensure billing compliance  
✅ **Preset Library** for common modifier combinations  
✅ **Database Migration** applied successfully  

---

## Database Schema

### New Columns in `order_items`

```sql
ALTER TABLE order_items ADD COLUMN modifier1 TEXT;
ALTER TABLE order_items ADD COLUMN modifier2 TEXT;
ALTER TABLE order_items ADD COLUMN modifier3 TEXT;
ALTER TABLE order_items ADD COLUMN modifier4 TEXT;
ALTER TABLE order_items ADD COLUMN rental_month INTEGER DEFAULT 0;
```

**Migration**: `Migration006_AddBillingModifiers` (version 6)  
**Applied to**: `C:\FaxManagerData\Data\orders.db`  

---

## Domain Model Updates

### OrderItem Model (`dmelogic/db/models.py`)

```python
@dataclass
class OrderItem:
    # ... existing fields ...
    
    # Billing modifiers (up to 4 for HCFA-1500 and State Portal)
    modifier1: Optional[str] = None
    modifier2: Optional[str] = None
    modifier3: Optional[str] = None
    modifier4: Optional[str] = None
    
    # Rental tracking
    rental_month: int = 0  # Tracks rental month (1-13+)
    
    @property
    def is_rental(self) -> bool:
        """Check if item is rental (has RR modifier)."""
        return 'RR' in self.all_modifiers
    
    @property
    def all_modifiers(self) -> list[str]:
        """Get all non-empty modifiers."""
        return [m for m in [self.modifier1, self.modifier2, 
                           self.modifier3, self.modifier4] if m]
    
    def get_rental_k_modifier(self) -> Optional[str]:
        """Get appropriate K modifier for current rental month."""
        # Returns KH, KI, KJ, or None based on rental_month
```

---

## Rental Equipment Billing Rules

### DME Rental Modifier Progression

| Rental Month | Modifier | Description | Payment Notes |
|--------------|----------|-------------|---------------|
| Month 1 | RR + **KH** | Initial claim, first month rental | Full rental rate |
| Months 2-3 | RR + **KI** | Second and third rental months | Full rental rate |
| Months 4-13 | RR + **KJ** | Fourth through thirteenth months | ~25% payment drop |
| Month 14+ | RR only | Ownership transfer period | No K modifier |

### Automatic K Modifier Assignment

The system automatically assigns K modifiers based on rental month:

```python
from dmelogic.db.rental_modifiers import auto_assign_rental_modifiers

# For initial rental (month 1)
auto_assign_rental_modifiers(item, refill_number=0)
# Result: modifier1='RR', modifier2='KH', rental_month=1

# For first refill (month 2)
auto_assign_rental_modifiers(item, refill_number=1)
# Result: modifier1='RR', modifier2='KI', rental_month=2

# For fourth refill (month 5)
auto_assign_rental_modifiers(item, refill_number=4)
# Result: modifier1='RR', modifier2='KJ', rental_month=5
```

---

## API Reference

### Rental Modifier Functions (`dmelogic/db/rental_modifiers.py`)

#### `get_rental_k_modifier_for_month(rental_month: int) -> Optional[str]`

Get the appropriate K modifier for a specific rental month.

```python
get_rental_k_modifier_for_month(1)   # Returns 'KH'
get_rental_k_modifier_for_month(2)   # Returns 'KI'
get_rental_k_modifier_for_month(5)   # Returns 'KJ'
get_rental_k_modifier_for_month(14)  # Returns None
```

#### `auto_assign_rental_modifiers(item: OrderItem, refill_number: int = 0) -> None`

Automatically assign RR + K modifiers based on refill number.

```python
item = OrderItem(modifier1='RR', ...)
auto_assign_rental_modifiers(item, refill_number=0)
# Sets: modifier1='RR', modifier2='KH', rental_month=1
```

#### `update_rental_month_on_refill(item: OrderItem) -> None`

Increment rental month and update K modifier when processing a refill.

```python
item = OrderItem(modifier1='RR', modifier2='KH', rental_month=1, ...)
update_rental_month_on_refill(item)
# Updates: modifier2='KI', rental_month=2
```

#### `format_modifiers_for_display(item: OrderItem) -> str`

Format all modifiers as comma-separated string for display.

```python
format_modifiers_for_display(item)  # Returns "RR, KH" or "RR, KJ, NU"
```

#### `validate_rental_modifiers(item: OrderItem) -> list[str]`

Validate that modifiers match rental month and billing rules.

```python
errors = validate_rental_modifiers(item)
if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

#### `apply_modifier_preset(item: OrderItem, preset_name: str) -> bool`

Apply common modifier combinations from preset library.

```python
apply_modifier_preset(item, "rental_month_1")  # RR, KH
apply_modifier_preset(item, "rental_month_4")  # RR, KJ
apply_modifier_preset(item, "purchase_new")    # NU
```

---

## Common Modifier Presets

Predefined modifier combinations for quick application:

```python
COMMON_MODIFIER_PRESETS = {
    "rental_month_1": ("RR", "KH", None, None),
    "rental_month_2": ("RR", "KI", None, None),
    "rental_month_3": ("RR", "KI", None, None),
    "rental_month_4": ("RR", "KJ", None, None),
    "rental_month_5": ("RR", "KJ", None, None),
    "rental_new": ("RR", "NU", None, None),      # New rental equipment
    "rental_used": ("RR", "UE", None, None),     # Used rental equipment
    "purchase_new": ("NU", None, None, None),    # New purchase
    "purchase_used": ("UE", None, None, None),   # Used purchase
}
```

---

## Usage Examples

### Example 1: Initial Rental Setup

```python
from dmelogic.db import fetch_order_with_items
from dmelogic.db.rental_modifiers import apply_modifier_preset

# Fetch order
order = fetch_order_with_items(order_id, folder_path)

# Mark first item as rental month 1
item = order.items[0]
apply_modifier_preset(item, "rental_month_1")

# Save changes
# ... (update database)

print(f"Modifiers: {item.modifier1}, {item.modifier2}")  # RR, KH
print(f"Rental month: {item.rental_month}")  # 1
```

### Example 2: Processing a Refill

```python
from dmelogic.db.rental_modifiers import update_rental_month_on_refill

# Fetch existing rental item
order = fetch_order_with_items(order_id, folder_path)
item = order.items[0]  # Assume has RR, KH, rental_month=1

# Process refill - automatically updates K modifier
update_rental_month_on_refill(item)

print(f"Modifiers: {item.modifier1}, {item.modifier2}")  # RR, KI
print(f"Rental month: {item.rental_month}")  # 2

# Save updated item to database
# ... (update database)
```

### Example 3: Display Modifiers in UI

```python
from dmelogic.db.rental_modifiers import format_modifiers_for_display

# Fetch order
order = fetch_order_with_items(order_id, folder_path)

# Display each item with modifiers
for item in order.items:
    print(f"{item.hcpcs_code}: {item.description}")
    print(f"  Modifiers: {format_modifiers_for_display(item)}")
    
    if item.is_rental:
        print(f"  Rental month: {item.rental_month}")
        k_mod = item.get_rental_k_modifier()
        print(f"  Expected K modifier: {k_mod or 'None'}")
```

### Example 4: Validate Before Billing

```python
from dmelogic.db.rental_modifiers import validate_rental_modifiers

# Before submitting to State Portal or 1500 form
order = fetch_order_with_items(order_id, folder_path)

for item in order.items:
    errors = validate_rental_modifiers(item)
    if errors:
        print(f"Item {item.hcpcs_code} has validation errors:")
        for error in errors:
            print(f"  - {error}")
        # Handle errors (fix or warn user)
```

---

## UI Integration Points

### Order Entry Form

Add 4 modifier input fields per item:

```python
# In order item entry dialog/widget
self.modifier1_input = QLineEdit()  # Max 2 characters
self.modifier2_input = QLineEdit()
self.modifier3_input = QLineEdit()
self.modifier4_input = QLineEdit()

# Add preset dropdown
self.preset_combo = QComboBox()
self.preset_combo.addItems([
    "None",
    "Rental - Month 1",
    "Rental - Month 2-3",
    "Rental - Month 4+",
    "Purchase - New",
    "Purchase - Used",
])

# Connect preset selection
self.preset_combo.currentTextChanged.connect(self.apply_preset)
```

### Refill Processing

Auto-update K modifiers when processing refills:

```python
def process_refill(self, item_id: int):
    """Process a refill for rental equipment."""
    # Fetch item
    item = fetch_item_by_id(item_id, self.folder_path)
    
    if item.is_rental:
        # Auto-update rental month and K modifier
        update_rental_month_on_refill(item)
        
        # Save to database
        save_item(item, self.folder_path)
        
        # Show confirmation
        self.show_info(
            f"Refill processed for {item.hcpcs_code}\n"
            f"Now rental month {item.rental_month} with modifier {item.modifier2}"
        )
```

### Order Display/Review

Show modifiers in item list:

```python
# In order review table
for item in order.items:
    row = [
        item.hcpcs_code,
        item.description,
        str(item.quantity),
        format_modifiers_for_display(item),  # "RR, KH" or "NU"
        f"${item.cost_ea or 0:.2f}",
    ]
    self.table.addRow(row)
```

---

## State Portal Integration

Modifiers are included in State Portal exports via `StatePortalOrderView`:

```python
# In state_portal_view.py (update needed)
def to_portal_json(self) -> dict:
    """Include modifiers in JSON export."""
    return {
        # ... existing fields ...
        "claim": {
            "items": [
                {
                    "hcpcsCode": item.hcpcs_code,
                    "description": item.description,
                    "quantity": item.quantity,
                    "modifier1": item.modifier1 or "",
                    "modifier2": item.modifier2 or "",
                    "modifier3": item.modifier3 or "",
                    "modifier4": item.modifier4 or "",
                    # ... other fields ...
                }
                for item in self.order.items
            ]
        }
    }
```

---

## HCFA-1500 Form Integration

Modifiers map directly to HCFA-1500 form fields:

```
Box 24D: HCPCS/Rates/Charges
[HCPCS Code] [Mod1] [Mod2] [Mod3] [Mod4]

Example:
E0601    RR   KH
E0601    RR   KI
E0601    RR   KJ
```

Implementation in future `Hcfa1500ClaimView`:

```python
class Hcfa1500ClaimView:
    def render_service_line(self, item: OrderItem) -> str:
        """Render service line with modifiers."""
        modifiers = [
            item.modifier1 or "",
            item.modifier2 or "",
            item.modifier3 or "",
            item.modifier4 or "",
        ]
        
        return f"{item.hcpcs_code} {' '.join([m for m in modifiers if m])}"
```

---

## Testing

### Run Tests

```powershell
python test_billing_modifiers.py
```

### Test Results

```
✓ K modifier calculation: 7/7 tests passed
✓ Auto-assignment: 4/4 tests passed
✓ Preset application: 4/4 tests passed
✓ Validation: 2/2 tests passed
✓ Database integration: Working
```

### Manual Testing

```python
# Test in Python REPL
from dmelogic.db import fetch_order_with_items
from dmelogic.db.rental_modifiers import *

# Fetch order
order = fetch_order_with_items(1, r"C:\FaxManagerData\Data")

# Test modifiers
item = order.items[0]
apply_modifier_preset(item, "rental_month_1")
print(f"Modifiers: {format_modifiers_for_display(item)}")  # RR, KH
```

---

## Files Modified/Created

### Core Implementation
- ✅ `dmelogic/db/models.py` - Added modifier fields to OrderItem
- ✅ `dmelogic/db/converters.py` - Updated row_to_order_item converter
- ✅ `dmelogic/db/migrations.py` - Added Migration006_AddBillingModifiers
- ✅ `dmelogic/db/rental_modifiers.py` - New module with rental logic

### Migration & Testing
- ✅ `apply_modifier_migration.py` - Migration application script
- ✅ `test_billing_modifiers.py` - Comprehensive test suite

### Documentation
- ✅ `BILLING_MODIFIERS_COMPLETE.md` - This file

---

## Next Steps

### Immediate (Ready Now)

1. **Update Order Entry UI**
   - Add 4 modifier input fields to order item form
   - Add preset dropdown for quick modifier selection
   - Show rental month for rental items

2. **Update State Portal Export**
   - Include modifier1-4 in `StatePortalOrderView.to_portal_json()`
   - Include modifiers in CSV export

3. **Update Order Display**
   - Show modifiers in order review tables
   - Format as "RR, KH" in display columns

### Near-Term (Next Sprint)

4. **Refill Processing Integration**
   - Auto-update K modifiers when processing refills
   - Increment rental_month automatically
   - Validate modifiers before saving

5. **HCFA-1500 Form Generation**
   - Create `Hcfa1500ClaimView` class
   - Map modifiers to Box 24D
   - Follow same pattern as State Portal view

6. **Validation & Warnings**
   - Add validation to order save workflow
   - Warn users if K modifier doesn't match rental month
   - Prevent billing submission with invalid modifiers

---

## Summary

✅ **Database**: 5 new columns added to order_items  
✅ **Models**: OrderItem updated with modifier fields and properties  
✅ **Business Logic**: Complete rental modifier calculation and validation  
✅ **Testing**: All tests passing  
✅ **Documentation**: Complete API reference and examples  
✅ **Ready For**: UI integration, State Portal export, HCFA-1500 forms  

**The foundation is complete. Modifiers are now tracked at the database level and ready for use in forms, exports, and billing workflows!**
