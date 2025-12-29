# Order Editor Integration Guide

## Overview

This guide shows how to integrate the new **Modern Order Editor** into the existing DME Logic application, replacing legacy order editing flows.

## Step-by-Step Integration

### Step 1: Replace Edit Order Button Handler

**Location**: `app_legacy.py` line ~10909 (or wherever `btn_edit_order` is wired)

**Current Code**:
```python
self.btn_edit_order.clicked.connect(self.edit_order)
```

**New Code**:
```python
# Option A: Use modern editor directly
self.btn_edit_order.clicked.connect(
    lambda: self.open_order_editor(self.get_selected_order_id())
)

# Option B: Add "Modern" button alongside legacy button
self.btn_edit_order_modern = QPushButton("✨ Edit Order (Modern)")
self.btn_edit_order_modern.clicked.connect(
    lambda: self.open_order_editor(self.get_selected_order_id())
)
# Add to button layout...
```

### Step 2: Add Double-Click Handler for Orders Table

**Location**: `app_legacy.py` in `create_orders_tab()` or similar

**Current**: Orders table may not have double-click handler, or has old one

**Add This**:
```python
def on_order_table_double_clicked(self, row: int, column: int):
    """Open modern order editor when user double-clicks an order row."""
    if row < 0:
        return
    
    try:
        order_id_item = self.orders_table.item(row, 0)  # Order # is column 0
        if order_id_item:
            order_id = int(order_id_item.text())
            self.open_order_editor(order_id)
    except (ValueError, AttributeError) as e:
        print(f"Error opening order editor: {e}")

# Wire it up
self.orders_table.cellDoubleClicked.connect(self.on_order_table_double_clicked)
```

### Step 3: Get Selected Order ID Helper

**Location**: Add to `MainWindow` or `PDFViewer` class

**Add This Method**:
```python
def get_selected_order_id(self) -> int | None:
    """Get the order ID of the currently selected row in orders table."""
    if not hasattr(self, 'orders_table'):
        return None
    
    current_row = self.orders_table.currentRow()
    if current_row < 0:
        return None
    
    try:
        order_id_item = self.orders_table.item(current_row, 0)
        if order_id_item:
            return int(order_id_item.text())
    except (ValueError, AttributeError):
        pass
    
    return None
```

### Step 4: Replace edit_order_by_id() Calls

**Find All Calls**: Search codebase for `edit_order_by_id(`

**Current Code** (various locations):
```python
self.edit_order_by_id(order_id)
```

**Replace With**:
```python
self.open_order_editor(order_id)
```

**Example Locations**:
- `edit_selected_order_from_history()` (line ~18561)
- Context menu handlers
- Keyboard shortcut handlers

### Step 5: Add Keyboard Shortcut (Optional)

**Location**: In `MainWindow.__init__()` or similar

**Add This**:
```python
from PyQt6.QtGui import QShortcut, QKeySequence

# Ctrl+E to edit selected order
self.edit_order_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
self.edit_order_shortcut.activated.connect(
    lambda: self.open_order_editor(self.get_selected_order_id())
)
```

### Step 6: Context Menu Integration

**Location**: Orders table context menu handler

**Add Menu Item**:
```python
def show_orders_context_menu(self, pos):
    menu = QMenu(self)
    
    # Get selected order
    row = self.orders_table.rowAt(pos.y())
    if row >= 0:
        order_id = int(self.orders_table.item(row, 0).text())
        
        # Add modern editor option
        edit_modern_action = menu.addAction("✨ Edit Order (Modern)")
        edit_modern_action.triggered.connect(lambda: self.open_order_editor(order_id))
        
        # Keep legacy option for now
        edit_legacy_action = menu.addAction("📝 Edit Order (Legacy)")
        edit_legacy_action.triggered.connect(lambda: self.edit_order_by_id(order_id))
        
        menu.addSeparator()
        
        # ... other menu items ...
    
    menu.exec(self.orders_table.mapToGlobal(pos))

# Wire up context menu
self.orders_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
self.orders_table.customContextMenuRequested.connect(self.show_orders_context_menu)
```

## Complete Example Integration

Here's a complete example showing all the pieces together:

```python
# In MainWindow or PDFViewer class

def setup_orders_tab_modern(self):
    """Setup orders tab with modern order editor integration."""
    
    # ... existing table setup code ...
    
    # Button handlers - use modern editor
    self.btn_edit_order.clicked.connect(
        lambda: self.open_order_editor(self.get_selected_order_id())
    )
    
    # Double-click opens modern editor
    self.orders_table.cellDoubleClicked.connect(self.on_order_table_double_clicked)
    
    # Keyboard shortcut
    self.edit_order_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
    self.edit_order_shortcut.activated.connect(
        lambda: self.open_order_editor(self.get_selected_order_id())
    )
    
    # Context menu
    self.orders_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    self.orders_table.customContextMenuRequested.connect(self.show_orders_context_menu)

def get_selected_order_id(self) -> int | None:
    """Get currently selected order ID."""
    if not hasattr(self, 'orders_table'):
        return None
    
    current_row = self.orders_table.currentRow()
    if current_row < 0:
        return None
    
    try:
        order_id_item = self.orders_table.item(current_row, 0)
        if order_id_item:
            return int(order_id_item.text())
    except (ValueError, AttributeError):
        pass
    
    return None

def on_order_table_double_clicked(self, row: int, column: int):
    """Handle double-click on order table row."""
    if row < 0:
        return
    
    try:
        order_id = int(self.orders_table.item(row, 0).text())
        self.open_order_editor(order_id)
    except (ValueError, AttributeError) as e:
        print(f"Error opening order editor: {e}")

def show_orders_context_menu(self, pos):
    """Show context menu for orders table."""
    menu = QMenu(self)
    
    row = self.orders_table.rowAt(pos.y())
    if row >= 0:
        order_id = int(self.orders_table.item(row, 0).text())
        
        # Modern editor
        edit_action = menu.addAction("✨ Edit Order")
        edit_action.triggered.connect(lambda: self.open_order_editor(order_id))
        
        menu.addSeparator()
        
        # Other actions...
        export_action = menu.addAction("📤 Export to Portal")
        export_action.triggered.connect(lambda: self.export_order_to_state_portal())
        
        pdf_action = menu.addAction("📄 Generate 1500")
        pdf_action.triggered.connect(lambda: self.generate_1500_for_order(order_id))
    
    menu.exec(self.orders_table.mapToGlobal(pos))
```

## Testing Your Integration

### Checklist

After integration, verify these work:

1. **Edit Button**
   - [ ] Click "Edit Order" button
   - [ ] Order Editor opens for selected order
   - [ ] All sections populated correctly

2. **Double-Click**
   - [ ] Double-click any order row
   - [ ] Order Editor opens
   - [ ] Correct order loaded

3. **Keyboard Shortcut**
   - [ ] Select an order
   - [ ] Press Ctrl+E
   - [ ] Order Editor opens

4. **Context Menu**
   - [ ] Right-click order row
   - [ ] "Edit Order" appears in menu
   - [ ] Clicking opens Order Editor

5. **Status Changes**
   - [ ] Change order status in editor
   - [ ] Close editor
   - [ ] Orders table refreshes with new status

6. **Multiple Opens**
   - [ ] Open editor for order #1
   - [ ] Close it
   - [ ] Open editor for order #2
   - [ ] Both work correctly

## Rollback Plan

If you need to rollback to legacy editor:

### Quick Rollback (Keep Both)

```python
# Add toggle setting
USE_MODERN_EDITOR = False  # Set to True to use new editor

def edit_order_handler(self):
    order_id = self.get_selected_order_id()
    if USE_MODERN_EDITOR:
        self.open_order_editor(order_id)
    else:
        self.edit_order_by_id(order_id)  # Legacy

self.btn_edit_order.clicked.connect(self.edit_order_handler)
```

### Full Rollback

1. Revert button handler: `self.btn_edit_order.clicked.connect(self.edit_order)`
2. Remove double-click handler
3. Remove keyboard shortcut
4. Keep new code commented out for future use

## Gradual Migration Strategy

### Week 1: Soft Launch
- Add "Edit Order (Modern)" button alongside legacy button
- Keep legacy "Edit Order" button
- Users can opt-in to new interface
- Collect feedback

### Week 2: Make Default
- Make modern editor the default double-click action
- Keep legacy editor accessible via menu
- Monitor for issues

### Week 3: Full Migration
- Remove legacy button
- Keep legacy editor code for emergency rollback
- Update documentation

### Week 4: Cleanup
- Remove legacy editor code
- Clean up old dialog classes
- Update all documentation

## Common Integration Issues

### Issue 1: Import Error

**Error**: `ImportError: cannot import name 'OrderEditorDialog'`

**Fix**: Add to imports at top of file:
```python
from dmelogic.ui.order_editor import OrderEditorDialog
```

### Issue 2: Method Not Found

**Error**: `AttributeError: 'PDFViewer' has no attribute 'open_order_editor'`

**Fix**: The method is in `MainWindow`, not `PDFViewer`. Make sure:
```python
class MainWindow(PDFViewer):
    # ... has open_order_editor() method
```

### Issue 3: Table Not Refreshing

**Problem**: After changing status, orders table doesn't update

**Fix**: Connect the signal in `open_order_editor()`:
```python
dialog = OrderEditorDialog(order_id, folder_path, parent=self)
dialog.order_updated.connect(self.load_orders)  # This line is crucial
dialog.exec()
```

### Issue 4: Theme Not Applied

**Problem**: Order editor doesn't match app theme

**Fix**: Theme should be applied by QApplication:
```python
# In app.py main()
app = QApplication(sys.argv)
theme_path = Path(__file__).parent / "assets" / "theme.qss"
if theme_path.exists():
    with open(theme_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())  # Applied to all dialogs
```

## Performance Optimization

### Lazy Loading

If order loading is slow, consider lazy loading sections:

```python
def _bind_order_to_ui(self):
    """Bind order data with lazy loading for large orders."""
    # Load critical info immediately
    self._update_header()
    self._populate_patient_section()
    
    # Defer heavy operations
    QTimer.singleShot(100, self._populate_items_table)
    QTimer.singleShot(200, self._populate_notes)
```

### Caching

For frequently accessed orders:

```python
_order_cache = {}  # Module-level cache

def _load_order(self):
    if self.order_id in _order_cache:
        self.order = _order_cache[self.order_id]
    else:
        self.order = fetch_order_with_items(self.order_id, ...)
        _order_cache[self.order_id] = self.order
```

## User Training

### Quick Start for Users

1. **Opening Orders**
   - Double-click any order in the table
   - Or select order and click "Edit Order"
   - Or select order and press Ctrl+E

2. **Viewing Information**
   - All order details in left panel
   - Organized by section (Patient, Prescriber, Insurance, etc.)
   - Items table shows quantities, modifiers, costs

3. **Changing Status**
   - Use "Change Status To" dropdown
   - Only valid transitions shown
   - Click "Update Status" to apply

4. **Actions**
   - Right panel has buttons for common operations
   - Click "Send to Portal" to export order
   - Click "Process Refill" for rental equipment

## Support Resources

- **Technical Documentation**: `ORDER_EDITOR_IMPLEMENTATION.md`
- **Quick Reference**: `ORDER_EDITOR_QUICK_REF.md`
- **This Integration Guide**: `ORDER_EDITOR_INTEGRATION.md`
- **Demo**: Run `python demo_order_editor.py` to see it in action

## Questions?

Common questions answered:

**Q: Can I keep the legacy editor?**
A: Yes! You can run both in parallel during transition period.

**Q: Will this break existing workflows?**
A: No. The new editor reads/writes same database. All data compatible.

**Q: What if users prefer the old interface?**
A: You can add a settings toggle to choose which editor to use.

**Q: Is this production-ready?**
A: Yes! The editor is fully tested and uses proven domain model patterns.

---

**Integration Difficulty**: ⭐⭐ (Easy - mostly just wiring up existing methods)

**Estimated Integration Time**: 30-60 minutes

**Risk Level**: Low (can run alongside legacy code, easy rollback)

**Recommendation**: Start with parallel deployment, make default after 1-2 weeks

