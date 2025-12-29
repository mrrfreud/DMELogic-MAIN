# Order Editor - Quick Reference Guide

## Opening the Order Editor

### From Main Window
```python
# In MainWindow or any code with access to MainWindow instance
self.open_order_editor(order_id=5)
```

### From Order Table
```python
# Double-click handler
def on_order_double_clicked(self, row, column):
    order_id = int(self.orders_table.item(row, 0).text())
    self.open_order_editor(order_id)

# Or wire to button
self.btn_edit_order.clicked.connect(lambda: self.open_order_editor(self.get_selected_order_id()))
```

### Standalone Demo
```bash
# Default: opens order #1
python demo_order_editor.py

# Specific order ID
python demo_order_editor.py 5
```

## UI Sections

### Header
- **Order ID**: Large, bold order number
- **Status Badge**: Color-coded current status

### Left Panel (Order Details)
1. **Patient Information**: Name, DOB, phone, address
2. **Prescriber Information**: Name, NPI
3. **Insurance Information**: Primary insurance, policy #, billing type
4. **Clinical Information**: RX date, order date, delivery date, ICD codes, directions
5. **Order Items**: Table with HCPCS, description, qty, refills, days, **modifiers**, cost
6. **Notes**: Order-level notes

### Right Panel (Actions)

#### Status Management
- **Change Status To**: Dropdown (only shows valid transitions)
- **Update Status**: Apply the selected status change

#### Export & Forms
- **📤 Send to State Portal**: Export order to state portal system
- **📄 Generate HCFA-1500**: Create CMS-1500 claim form
- **🎫 Print Delivery Ticket**: Print delivery documentation

#### Processing
- **🔄 Process Refill**: Create refill order (auto-updates K modifiers for rentals)
- **✏️ Edit Items**: Open item editor

#### Documents
- **📁 View Documents**: View related PDFs/images

#### Bottom
- **🔄 Refresh Order**: Reload from database

## Key Features

### Status Workflow Validation
- Status combo only shows **allowed** transitions based on current status
- Example: From "Pending" → can go to "Docs Needed", "Ready", "On Hold", "Cancelled"
- Cannot skip required steps or make invalid transitions

### Billing Modifiers Display
Items table shows modifiers using smart formatting:
- **Rental items**: "RR, KH" (month 1), "RR, KI" (month 2-3), "RR, KJ" (month 4-13)
- **Purchase items**: "NU" (new), "UE" (used)
- **No modifiers**: "None"

### Domain Model Integration
- Uses `fetch_order_with_items()` - same as order wizard and exports
- All data from rich `Order` domain model
- Consistent computed properties:
  - `order.patient_full_name`
  - `order.order_total`
  - `item.is_rental`
  - `item.all_modifiers`

### Auto-Refresh
- After status change → refreshes order data
- Emits `order_updated` signal → parent can refresh tables
- Ensures UI always shows current state

## Common Operations

### Change Order Status
1. Select new status from "Change Status To" dropdown
2. Click "Update Status" button
3. Confirm the change
4. Order reloads with new status

### Export to State Portal
1. Click "📤 Send to State Portal"
2. Order data converted to JSON format
3. Ready for API submission
4. Shows success confirmation

### Process Refill (Rental Items)
1. Click "🔄 Process Refill"
2. System checks for items with refills > 0
3. For rental items (RR modifier):
   - Increments rental_month
   - Updates K modifier (KH → KI → KJ)
4. Creates new order linked to original

### View Order Total
- Displayed at bottom of items table
- Automatically calculated: `sum(item.cost_ea * item.quantity for item in order.items)`
- Formatted as currency: "$123.45"

## Status Color Codes

| Status | Color | Hex Code |
|--------|-------|----------|
| Pending | 🟠 Orange | #FFA500 |
| Docs Needed | 🔴 Red | #FF6B6B |
| Ready | 🟦 Teal | #4ECDC4 |
| Delivered | 🟢 Light Green | #95E1D3 |
| Billed | 💚 Pale Green | #A8E6CF |
| Paid | ✅ Green | #51CF66 |
| Closed | ⚫ Gray | #868E96 |
| Cancelled | ⚪ Light Gray | #DEE2E6 |
| On Hold | 🟡 Yellow | #FFD93D |
| Denied | 🩷 Pink | #FF6B9D |

## Integration Example

### Replace Legacy Edit Button

```python
# Old way (in app_legacy.py)
self.btn_edit_order.clicked.connect(self.edit_order)

# New way (in MainWindow)
self.btn_edit_order.clicked.connect(
    lambda: self.open_order_editor(self.get_selected_order_id())
)
```

### Connect Order Updated Signal

```python
dialog = OrderEditorDialog(order_id=5, folder_path=self.current_folder, parent=self)

# Refresh orders table when changes saved
dialog.order_updated.connect(self.load_orders)

# Show dialog
dialog.exec()
```

## Keyboard Shortcuts (Future)

Future enhancements will add:
- `Ctrl+S`: Save changes
- `Ctrl+R`: Refresh order
- `Ctrl+P`: Print delivery ticket
- `Ctrl+E`: Export to portal
- `Esc`: Close dialog

## Troubleshooting

### Order Not Loading
- **Error**: "Order #{id} could not be loaded"
- **Cause**: Order doesn't exist or database error
- **Fix**: Check order ID, verify database connection

### Status Change Fails
- **Error**: "Cannot transition from X to Y"
- **Cause**: Invalid status transition per workflow rules
- **Fix**: Use allowed transitions shown in dropdown

### Modifiers Not Showing
- **Issue**: Items table shows "None" for rental items
- **Cause**: modifier1-4 fields empty in database
- **Fix**: Use modifier presets or edit items to set modifiers

### Performance Issues
- **Issue**: Slow loading for orders with many items
- **Cause**: Large result set, no pagination
- **Fix**: Orders with 100+ items may be slow (future optimization)

## Testing Checklist

- [ ] Order loads successfully
- [ ] All sections populated with correct data
- [ ] Status badge shows correct color
- [ ] Status dropdown shows only valid transitions
- [ ] Items table displays all items with modifiers
- [ ] Order total calculated correctly
- [ ] Action buttons clickable (UI responds)
- [ ] Status change updates database
- [ ] Portal export generates JSON
- [ ] Close button dismisses dialog
- [ ] Refresh button reloads data

## Related Documentation

- `ORDER_EDITOR_IMPLEMENTATION.md` - Full technical documentation
- `MODIFIERS_IMPLEMENTATION_COMPLETE.md` - Billing modifiers system
- `DOMAIN_MODEL_INTEGRATION.md` - Domain model architecture
- `UI_DESIGN_SYSTEM.md` - UI standards

---

**Quick Start**: `python demo_order_editor.py 1`
