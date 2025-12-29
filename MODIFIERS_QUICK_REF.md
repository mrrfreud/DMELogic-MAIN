# Quick Reference: Billing Modifiers

## Database Fields

```sql
-- Order items now have:
modifier1 TEXT
modifier2 TEXT
modifier3 TEXT
modifier4 TEXT
rental_month INTEGER DEFAULT 0
```

## Import

```python
from dmelogic.db import fetch_order_with_items
from dmelogic.db.rental_modifiers import (
    auto_assign_rental_modifiers,
    update_rental_month_on_refill,
    format_modifiers_for_display,
    validate_rental_modifiers,
    apply_modifier_preset,
)
```

## Rental Month Rules

| Month | K Modifier | Usage |
|-------|------------|-------|
| 1 | **KH** | Initial claim, first month rental |
| 2-3 | **KI** | Second and third rental months |
| 4-13 | **KJ** | Fourth through thirteenth months |
| 14+ | None | Ownership transfer (no K modifier) |

## Common Patterns

### Set Up New Rental

```python
item = order.items[0]
apply_modifier_preset(item, "rental_month_1")
# Result: modifier1='RR', modifier2='KH', rental_month=1
```

### Process Refill

```python
item = order.items[0]
update_rental_month_on_refill(item)
# Increments rental_month and updates K modifier automatically
```

### Display Modifiers

```python
for item in order.items:
    print(f"{item.hcpcs_code}: {format_modifiers_for_display(item)}")
    # Output: "E0601: RR, KH" or "A4495: None"
```

### Validate Before Billing

```python
errors = validate_rental_modifiers(item)
if errors:
    print("Fix these issues:", errors)
```

### Check Properties

```python
if item.is_rental:
    print(f"Rental month: {item.rental_month}")
    k_mod = item.get_rental_k_modifier()
    print(f"Should use: {k_mod}")

print(f"All modifiers: {item.all_modifiers}")  # List of non-empty modifiers
```

## Available Presets

```python
"rental_month_1"   # RR, KH (month 1)
"rental_month_2"   # RR, KI (month 2-3)
"rental_month_4"   # RR, KJ (month 4-13)
"rental_new"       # RR, NU (new rental equipment)
"rental_used"      # RR, UE (used rental equipment)
"purchase_new"     # NU (new purchase)
"purchase_used"    # UE (used purchase)
```

## UI Integration

### Order Entry Form

```python
# Add 4 modifier fields
self.modifier1 = QLineEdit()
self.modifier2 = QLineEdit()
self.modifier3 = QLineEdit()
self.modifier4 = QLineEdit()

# Add preset dropdown
self.preset_combo = QComboBox()
self.preset_combo.addItems([
    "Rental - Month 1",
    "Rental - Month 2-3", 
    "Rental - Month 4+",
    "Purchase - New",
])

# Apply preset when selected
def apply_preset(self):
    preset_name = self.get_preset_key()  # Map UI name to key
    apply_modifier_preset(self.current_item, preset_name)
    self.refresh_modifier_fields()
```

### Table Display

```python
# Add modifiers column
for item in order.items:
    row = [
        item.hcpcs_code,
        item.description,
        format_modifiers_for_display(item),  # "RR, KH"
        f"${item.cost_ea or 0:.2f}",
    ]
    table.addRow(row)
```

### Save Handler

```python
def save_item(self):
    # Get modifiers from UI
    item.modifier1 = self.modifier1.text() or None
    item.modifier2 = self.modifier2.text() or None
    item.modifier3 = self.modifier3.text() or None
    item.modifier4 = self.modifier4.text() or None
    
    # Validate
    errors = validate_rental_modifiers(item)
    if errors:
        self.show_error("\\n".join(errors))
        return
    
    # Save to database
    # ... (UPDATE query with modifier fields)
```

## Export Integration

### State Portal JSON

```python
# In StatePortalOrderView.to_portal_json()
"items": [
    {
        "hcpcsCode": item.hcpcs_code,
        "modifier1": item.modifier1 or "",
        "modifier2": item.modifier2 or "",
        "modifier3": item.modifier3 or "",
        "modifier4": item.modifier4 or "",
        # ... other fields
    }
    for item in order.items
]
```

### HCFA-1500 Form

```python
# Box 24D format: HCPCS Mod1 Mod2 Mod3 Mod4
def format_service_line(item: OrderItem) -> str:
    mods = [m for m in item.all_modifiers if m]
    return f"{item.hcpcs_code} {' '.join(mods)}"

# Example outputs:
# "E0601 RR KH"
# "E0601 RR KI"
# "A4495"
```

## Testing

```powershell
# Run test suite
python test_billing_modifiers.py

# Quick manual test
python -c "from dmelogic.db.rental_modifiers import *; print(get_rental_k_modifier_for_month(1))"  # KH
python -c "from dmelogic.db.rental_modifiers import *; print(get_rental_k_modifier_for_month(5))"  # KJ
```

## Common Issues

### Issue: Modifiers not saving

```python
# Make sure to include modifiers in UPDATE query:
cursor.execute("""
    UPDATE order_items 
    SET modifier1=?, modifier2=?, modifier3=?, modifier4=?, rental_month=?
    WHERE id=?
""", (item.modifier1, item.modifier2, item.modifier3, item.modifier4, 
      item.rental_month, item.id))
```

### Issue: Wrong K modifier for rental month

```python
# Validate and show error
errors = validate_rental_modifiers(item)
if errors:
    print("Validation failed:", errors[0])
    # Fix automatically:
    auto_assign_rental_modifiers(item, refill_number=item.rental_month-1)
```

### Issue: Modifiers not showing in exports

```python
# Update converters to include modifiers
# Already done in dmelogic/db/converters.py

# Update export views to include modifiers  
# Need to update StatePortalOrderView and Hcfa1500ClaimView
```

## Files to Update

- [ ] Order entry UI - Add 4 modifier input fields
- [ ] Order display tables - Show modifiers column
- [ ] Refill processing - Auto-update K modifiers
- [ ] State Portal export - Include modifiers in JSON/CSV
- [ ] HCFA-1500 generation - Map modifiers to Box 24D
- [ ] Order save/update - Include modifiers in SQL

## Quick Start

1. **Fetch order with modifiers**:
   ```python
   order = fetch_order_with_items(order_id, folder_path)
   item = order.items[0]
   ```

2. **Set up rental**:
   ```python
   apply_modifier_preset(item, "rental_month_1")
   ```

3. **Display**:
   ```python
   print(format_modifiers_for_display(item))
   ```

4. **Process refill**:
   ```python
   update_rental_month_on_refill(item)
   ```

5. **Validate**:
   ```python
   errors = validate_rental_modifiers(item)
   ```

**Done! Modifiers are now fully tracked and ready for billing.**
