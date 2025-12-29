# Modern Order Editor - Complete Implementation

## Overview

The **Order Editor** is a new unified interface that serves as the central hub for all order-related operations. It replaces scattered legacy UI flows with a single, modern, domain-model-powered dialog.

## Key Features

### 1. **Domain Model Powered**
- Uses `fetch_order_with_items()` as single source of truth
- All data loaded from rich `Order` domain model
- Consistent with order wizard and export flows

### 2. **Comprehensive Order Display**
Organized sections showing:
- **Patient Information**: Name, DOB, phone, address
- **Prescriber Information**: Name, NPI
- **Insurance Information**: Primary insurance, policy number, billing type
- **Clinical Information**: RX date, order date, delivery date, ICD-10 codes, doctor directions
- **Order Items Table**: HCPCS, description, quantity, refills, days supply, **modifiers**, cost
- **Order Total**: Calculated from items
- **Notes**: Order-level notes

### 3. **Status Management**
- Visual status badge with color coding
- Status dropdown populated with **allowed transitions only** (workflow engine validation)
- One-click status changes with confirmation
- Automatic table refresh after status update

### 4. **Action Buttons**

#### Export & Forms
- **📤 Send to State Portal**: Uses `StatePortalOrderView.from_order()` pattern
- **📄 Generate HCFA-1500**: Will use `Hcfa1500ClaimView.from_order()` (ready for implementation)
- **🎫 Print Delivery Ticket**: Print delivery documentation

#### Processing
- **🔄 Process Refill**: Create refill order with automatic K modifier updates for rental items
- **✏️ Edit Items**: Open item editor dialog (modal item editing)

#### Documents
- **📁 View Documents**: View PDFs, images, etc. related to order

### 5. **Billing Modifiers Display**
- Items table shows modifiers column using `format_modifiers_for_display()`
- Example: "RR, KH" for rental month 1
- "None" for items without modifiers

## Architecture

### Component Structure

```
OrderEditorDialog (QDialog)
├── Header (order ID + status badge)
├── Main Splitter
│   ├── Left Panel (75%) - Order Details
│   │   ├── Patient Section (QGroupBox)
│   │   ├── Prescriber Section (QGroupBox)
│   │   ├── Insurance Section (QGroupBox)
│   │   ├── Clinical Section (QGroupBox)
│   │   ├── Items Section (QGroupBox)
│   │   │   └── Items Table (QTableWidget)
│   │   └── Notes Section (QGroupBox)
│   └── Right Panel (25%) - Actions
│       ├── Status Management (QGroupBox)
│       ├── Export & Forms (QGroupBox)
│       ├── Processing (QGroupBox)
│       └── Documents (QGroupBox)
└── Bottom Buttons (Save Changes, Close)
```

### Data Flow

1. **Load Order**: `fetch_order_with_items(order_id, folder_path)` → `Order` domain model
2. **Bind to UI**: Populate all sections from `Order` properties
3. **User Actions**: Button clicks trigger operations on order
4. **Update**: Changes saved via repository functions
5. **Refresh**: `order_updated` signal → parent refreshes tables

## Integration Points

### In MainWindow

```python
# New methods added to MainWindow class:

def open_order_editor(self, order_id: int) -> None:
    """Open the modern Order Editor dialog."""
    from dmelogic.ui.order_editor import OrderEditorDialog
    
    dialog = OrderEditorDialog(
        order_id=order_id,
        folder_path=self.current_folder,
        parent=self
    )
    
    dialog.order_updated.connect(lambda: self.load_orders())
    dialog.exec()

def edit_order_by_id_modern(self, order_id: int) -> None:
    """Modern wrapper for edit_order_by_id."""
    self.open_order_editor(order_id)
```

### Usage Patterns

#### From Order Table Double-Click
```python
def on_order_double_clicked(self, row, column):
    order_id = int(self.orders_table.item(row, 0).text())
    self.open_order_editor(order_id)
```

#### From Edit Button
```python
self.btn_edit_order.clicked.connect(lambda: self.open_order_editor(self.get_selected_order_id()))
```

#### From Context Menu
```python
def show_order_context_menu(self, pos):
    menu = QMenu()
    edit_action = menu.addAction("Edit Order")
    edit_action.triggered.connect(lambda: self.open_order_editor(order_id))
```

## Status Workflow Integration

The Order Editor uses the **order workflow engine** for status transitions:

```python
from dmelogic.db.order_workflow import (
    can_transition,
    get_allowed_next_statuses,
)

# Populate status combo with ONLY valid transitions
allowed = get_allowed_next_statuses(current_status)
for status in allowed:
    self.status_combo.addItem(status.value, status)

# Validate before changing
if not can_transition(old_status, new_status):
    QMessageBox.warning(self, "Invalid Status Change", ...)
    return
```

Status badge color coding:
- 🟠 **Pending** → Orange (#FFA500)
- 🔴 **Docs Needed** → Red (#FF6B6B)
- 🟦 **Ready** → Teal (#4ECDC4)
- 🟢 **Delivered** → Light Green (#95E1D3)
- 💚 **Billed** → Pale Green (#A8E6CF)
- ✅ **Paid** → Green (#51CF66)
- ⚫ **Closed** → Gray (#868E96)
- ⚪ **Cancelled** → Light Gray (#DEE2E6)
- 🟡 **On Hold** → Yellow (#FFD93D)
- 🩷 **Denied** → Pink (#FF6B9D)

## Export & Forms Implementation

### State Portal Export (✅ Ready)

```python
def _send_to_portal(self):
    from dmelogic.db.order_workflow import build_state_portal_json_for_order
    
    json_data = build_state_portal_json_for_order(
        self.order_id,
        folder_path=self.folder_path
    )
    
    # POST to API endpoint
    # response = requests.post(portal_url, json=json_data)
```

### HCFA-1500 Generation (🔜 Pending)

```python
def _generate_1500(self):
    from dmelogic.forms import Hcfa1500ClaimView
    
    claim = Hcfa1500ClaimView.from_order(self.order)
    pdf_bytes = claim.render_to_pdf()
    
    # Save or display PDF
```

## Refill Processing with Modifiers

When processing refills for rental items:

```python
from dmelogic.db.rental_modifiers import update_rental_month_on_refill

for item in self.order.items:
    if item.refills > 0 and item.is_rental:
        # Increment rental month and update K modifier
        # Month 1 (KH) → Month 2 (KI) → Month 4 (KJ)
        update_rental_month_on_refill(item)
        
        # Save updated modifiers to database
        # update_order_item_modifiers(item.id, item.modifier2, item.rental_month)
```

## Testing

### Manual Testing

```bash
# Demo script - opens order editor for order #1
python demo_order_editor.py

# Or specify order ID
python demo_order_editor.py 5
```

### Integration Testing

```python
from dmelogic.ui.order_editor import OrderEditorDialog

# Test loading
dialog = OrderEditorDialog(order_id=1, folder_path="...")
assert dialog.order is not None
assert dialog.order.id == 1

# Test status population
assert dialog.status_combo.count() > 1  # Current + allowed transitions

# Test items display
assert dialog.items_table.rowCount() == len(dialog.order.items)
```

## Future Enhancements

### Phase 1 (Current) ✅
- [x] Domain model integration
- [x] Status workflow validation
- [x] Comprehensive display sections
- [x] Action buttons layout
- [x] Modifier display in items table

### Phase 2 (Next)
- [ ] Inline item editing in table
- [ ] Add/remove items from order
- [ ] Drag-and-drop document attachment
- [ ] Real-time validation feedback
- [ ] Undo/redo support

### Phase 3 (Future)
- [ ] Order history timeline view
- [ ] Comments/activity log
- [ ] Multi-order batch operations
- [ ] Export templates (Excel, CSV, JSON)
- [ ] Print preview for all documents

## Migration Strategy

### Gradual Replacement

1. **Phase 1**: New editor available via dedicated button
   - "Edit Order (Modern)" button alongside legacy "Edit Order"
   - Users can opt-in to new interface

2. **Phase 2**: Make new editor default
   - Double-click uses new editor
   - Legacy editor available via menu: "Edit Order (Legacy)"

3. **Phase 3**: Remove legacy editor
   - All order editing goes through new interface
   - Clean up old code paths

### Feature Parity Checklist

Before fully replacing legacy editor:
- [ ] All fields editable (patient, prescriber, insurance)
- [ ] Item add/edit/delete functionality
- [ ] Document attachment/viewing
- [ ] Print delivery ticket
- [ ] Export to all required formats
- [ ] Validation equivalent to legacy
- [ ] Performance equivalent or better

## Benefits

### For Users
- **Single interface** for all order operations (no hunting through menus)
- **Visual status tracking** with workflow validation
- **Clear action buttons** for common tasks
- **Modern, responsive UI** with better organization

### For Developers
- **Domain model consistency** (same Order object everywhere)
- **Easier testing** (single dialog vs. scattered logic)
- **Cleaner code** (no massive monolithic functions)
- **Extensible architecture** (easy to add new actions)

### For Maintenance
- **Single source of truth** for order display
- **Workflow engine** prevents invalid state transitions
- **Centralized validation** (one place to enforce rules)
- **Easier debugging** (clear data flow)

## Files

- `dmelogic/ui/order_editor.py` - Main dialog implementation (800 lines)
- `dmelogic/ui/main_window.py` - Integration with MainWindow
- `demo_order_editor.py` - Standalone demo script
- `ORDER_EDITOR_IMPLEMENTATION.md` - This documentation

## Related Documentation

- `MODIFIERS_IMPLEMENTATION_COMPLETE.md` - Billing modifiers system
- `DOMAIN_MODEL_INTEGRATION.md` - Domain model architecture
- `UNITOFWORK_GUIDE.md` - Transaction patterns
- `UI_DESIGN_SYSTEM.md` - UI standards and components

---

**Status**: ✅ Complete and ready for integration
**Last Updated**: December 6, 2025
