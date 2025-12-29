# Order Editor Quick Reference

## Opening Orders - All Entry Points Now Use Modern Editor

### 1. From Orders Table
```
Double-click any order row (except Paid column)
→ Modern Order Editor opens
```

### 2. From Edit Order Button
```
Select order → Click "Edit Order" button
→ Modern Order Editor opens
```

### 3. From Patient Dialog
```
Patient Details → Orders Tab → Double-click order
→ Modern Order Editor opens
```

### 4. From Code
```python
# Anywhere in the application
self.open_order_editor(order_id)
```

## Order Editor Features

### View Sections
- **Patient**: Demographics, insurance, contact info
- **Prescriber**: Name, NPI, phone, fax
- **Clinical**: RX date, ICD codes, doctor directions
- **Items**: HCPCS, qty, refills, **modifiers**, costs
- **Notes**: Order notes prominently displayed
- **Attachments**: RX files, signed tickets

### Action Buttons

#### Status Management
- Change status (Pending → Active → Completed, etc.)
- Workflow validation prevents invalid transitions

#### Export/Forms
- **Send to State Portal**: JSON export with billing info
- **Generate HCFA-1500**: Create billing form
- **Print HCFA-1500**: Direct printing

#### Processing
- **Process Refill**: Create new order from refillable items
- **Link Patient**: Associate order with patient record

#### Documents
- **View Attachments**: Open RX files, signed tickets
- **Link Documents**: Associate files with order

## Code Integration Examples

### Replace Legacy Edit Calls
```python
# OLD - Legacy approach
dialog = NewOrderDialog(self, order_data, order_items, order_id)
dialog.show()

# NEW - Modern approach
self.open_order_editor(order_id)
```

### Button Handlers
```python
# Edit Order button
self.btn_edit_order.clicked.connect(self._handle_edit_order_button)

def _handle_edit_order_button(self):
    current_row = self.orders_table.currentRow()
    if current_row >= 0:
        order_id = self.get_order_id_from_selected_row()
        self.open_order_editor(order_id)
```

### Double-Click Handlers
```python
def on_orders_double_clicked(self):
    # Handle special columns (Paid, etc.) first
    # ...
    
    # For all other columns
    order_id = self.get_order_id_from_row()
    self.open_order_editor(order_id)
```

## Theme Integration

### Colors
- Background: `#1E1E1E`
- Tables: `#2B2B2B`
- Primary Blue: `#0078D4`
- Success Green: `#28A745`
- Warning Orange: `#FFC107`
- Danger Red: `#DC3545`

### Component Classes
```python
# Use theme classes for consistent styling
button.setProperty("class", "primary")  # Blue primary button
label.setProperty("class", "section-title")  # Section headers
widget.setProperty("class", "OrderCard")  # Card containers
```

## Testing Checklist

✅ Double-click order row → Editor opens  
✅ Edit Order button → Editor opens  
✅ Patient dialog orders → Editor opens  
✅ Refill dialogs → Editor opens  
✅ Status changes work  
✅ Portal export works  
✅ HCFA-1500 generation works  
✅ Theme applied consistently  
✅ No syntax errors  
✅ Application launches  

## Legacy Code (Can Remove After Testing)

```python
# These methods preserved with _LEGACY suffix
edit_order_LEGACY()
edit_order_by_id_LEGACY()

# Can be safely removed once integration confirmed
```

## Quick Start for Developers

1. **Open order**: Call `self.open_order_editor(order_id)`
2. **Get editor instance**: Created as modal dialog
3. **Connect signals**: `order_updated.connect(your_refresh_method)`
4. **Theme styling**: Uses `assets/theme.qss` automatically

## Domain Model Integration

```python
# Order Editor uses domain model
from dmelogic.db.orders import fetch_order_with_items

order = fetch_order_with_items(order_id)
# Returns typed Order object with items, patient, prescriber
```

## Workflow Validation

```python
# Status changes validated
from dmelogic.workflows.order_workflow import validate_status_transition

is_valid = validate_status_transition(
    current_status="Pending",
    new_status="Active"
)
```

---

**Integration Status**: COMPLETE ✅  
**Production Ready**: YES 🚀  
**Theme Applied**: YES 🎨  
**Legacy Preserved**: YES 📦
