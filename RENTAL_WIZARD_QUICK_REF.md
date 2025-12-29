# Quick Reference: Rental + Modifiers in Wizard

## For Developers

### Wizard DTO
```python
# dmelogic/ui/order_wizard.py
@dataclass
class OrderItem:
    hcpcs: str = ""
    description: str = ""
    quantity: int = 1
    refills: int = 0
    days_supply: int = 30
    directions: str = ""
    is_rental: bool = False      # ← NEW
    modifiers: str = ""          # ← NEW (free text)
```

### Conversion Helper
```python
# dmelogic/db/orders.py
from dmelogic.db.orders import wizard_item_to_input
item_input = wizard_item_to_input(wizard_item)
# Returns OrderItemInput with:
#   - is_rental: bool
#   - modifier1, modifier2, modifier3, modifier4: str | None
```

### Database Persistence
```python
# Happens automatically in create_order_from_wizard_result()
# Saves to order_items:
#   - is_rental (INTEGER: 0 or 1)
#   - modifier1, modifier2, modifier3, modifier4 (TEXT)
```

### Domain Model
```python
# Already working via converters
order = fetch_order_with_items(order_id, folder_path)
for item in order.items:
    if item.is_rental:
        print(f"Rental: {item.hcpcs} with modifiers {item.modifiers}")
```

---

## For End Users

### How to Mark Item as Rental

1. In Order Wizard, navigate to **Items** step
2. Add a new row
3. Fill in HCPCS code (e.g., `E0601`)
4. **Check the "Rental?" checkbox** ✓
5. Enter modifiers in **Modifiers** column (e.g., `RR, NU`)

### Modifier Entry Formats

All of these work:
- Comma-separated: `RR, NU, KX`
- Space-separated: `RR NU KX`
- Slash-separated: `RR/NU`
- Mixed: `RR, NU/KX`

System automatically:
- Normalizes to uppercase
- Trims whitespace
- Limits to 4 modifiers (CMS requirement)

### Common Scenarios

**Monthly CPAP Rental**:
- HCPCS: `E0601`
- Qty: `1`
- Refills: `11` (12-month rental)
- ✓ Rental
- Modifiers: `RR`

**Purchase with Medical Necessity**:
- HCPCS: `E0470`
- Qty: `1`
- Refills: `0`
- ☐ Rental
- Modifiers: `NU, KX`

**Capped Rental (13th month)**:
- HCPCS: `E0601`
- Qty: `1`
- Refills: `0`
- ✓ Rental
- Modifiers: `RR, MS`

---

## Testing

### Quick Unit Test
```bash
python test_rental_wizard_flow.py
```

### Visual Test
```bash
python demo_rental_wizard.py
```

### In Production App
```bash
python app.py
```
- Click "New Order" wizard
- Navigate to Items step
- Verify 8 columns including "Rental?" and "Modifiers"

---

## Flow Diagram

```
User Input → Wizard → Converter → Database → Domain
    ↓          ↓          ↓           ↓         ↓
[✓] RR,NU → OrderItem → wizard_item → DB row → OrderItem
                        _to_input              .is_rental
                                              .modifiers
```

---

## Common Modifiers

| Code | Meaning |
|------|---------|
| RR   | Rental |
| NU   | New equipment |
| UE   | Used equipment |
| KX   | Medical policy requirements met |
| MS   | Six-month maintenance fee |
| BP   | Beneficiary purchase option |
| BR   | Beneficiary rental option |

---

## Files

- **Wizard UI**: `dmelogic/ui/order_wizard.py`
- **Conversion**: `dmelogic/db/orders.py` (`wizard_item_to_input`)
- **Tests**: `test_rental_wizard_flow.py`
- **Demo**: `demo_rental_wizard.py`
- **Docs**: `RENTAL_WIZARD_INTEGRATION.md`
