# Order Editor Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DME Manager Application                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    All Entry Points                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐     │  │
│  │  │  Double-   │  │ Edit Order │  │ Patient Dialog │     │  │
│  │  │   Click    │  │   Button   │  │ Order History  │     │  │
│  │  └──────┬─────┘  └──────┬─────┘  └────────┬───────┘     │  │
│  │         │                │                  │             │  │
│  │         └────────────────┴──────────────────┘             │  │
│  │                          │                                │  │
│  │                          ▼                                │  │
│  │              ┌───────────────────────┐                   │  │
│  │              │ open_order_editor()   │◄─── Refill Flows  │  │
│  │              │  (MainWindow method)  │                   │  │
│  │              └───────────┬───────────┘                   │  │
│  └──────────────────────────┼───────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Order Editor Dialog                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │  Header: Order #123 ● Status Badge              │   │  │
│  │  ├──────────────────────────────────────────────────┤   │  │
│  │  │  📋 Order Details Panel                          │   │  │
│  │  │    ┌─────────────────┐ ┌──────────────────┐    │   │  │
│  │  │    │ Patient Info    │ │ Prescriber Info  │    │   │  │
│  │  │    │ • Name, DOB     │ │ • Name, NPI      │    │   │  │
│  │  │    │ • Insurance     │ │ • Phone, Fax     │    │   │  │
│  │  │    └─────────────────┘ └──────────────────┘    │   │  │
│  │  │    ┌──────────────────────────────────────┐    │   │  │
│  │  │    │ Clinical Information                  │    │   │  │
│  │  │    │ • RX Date, Order Date                 │    │   │  │
│  │  │    │ • ICD Codes 1-5                       │    │   │  │
│  │  │    │ • Doctor Directions                   │    │   │  │
│  │  │    └──────────────────────────────────────┘    │   │  │
│  │  │    ┌──────────────────────────────────────┐    │   │  │
│  │  │    │ Order Items (with Modifiers)         │    │   │  │
│  │  │    │ HCPCS│Desc│Qty│Refills│Mod1-4│Cost  │    │   │  │
│  │  │    │─────────────────────────────────────│    │   │  │
│  │  │    │ E0601│ ... │ 1 │  11  │ RR  │$150  │    │   │  │
│  │  │    └──────────────────────────────────────┘    │   │  │
│  │  │    ┌──────────────────────────────────────┐    │   │  │
│  │  │    │ Notes                                 │    │   │  │
│  │  │    │ Customer requested delivery on Fri... │    │   │  │
│  │  │    └──────────────────────────────────────┘    │   │  │
│  │  ├──────────────────────────────────────────────────┤   │  │
│  │  │  ⚙️ Actions Panel                               │   │  │
│  │  │  [Change Status▼] [Send to Portal] [HCFA-1500] │   │  │
│  │  │  [Process Refill] [Link Patient] [View Docs]   │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Domain Model Layer                          │  │
│  │  ┌────────────────────┐  ┌────────────────────┐         │  │
│  │  │ fetch_order_with_  │  │ Order Workflow     │         │  │
│  │  │ items()            │  │ Validation         │         │  │
│  │  │ • Typed Order      │  │ • Status Rules     │         │  │
│  │  │ • OrderItem[]      │  │ • Transitions      │         │  │
│  │  │ • Patient, Rx      │  │                    │         │  │
│  │  └────────────────────┘  └────────────────────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                  │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              Database Layer (SQLite)                     │  │
│  │  • orders.db - Main order data with modifiers            │  │
│  │  • patients.db - Patient demographics                    │  │
│  │  • prescribers.db - Prescriber information               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Code Flow Diagram

```
User Action (Click/Double-Click)
         │
         ▼
Entry Point Method
  • on_orders_double_clicked()
  • _handle_edit_order_button()
  • edit_order_from_patient_dialog()
  • edit_order_by_id()
         │
         ▼
Extract Order ID
  order_id = get_order_id_from_display(order_number)
         │
         ▼
Call Unified Entry Point
  self.open_order_editor(order_id)
         │
         ▼
Create Order Editor Dialog
  dialog = OrderEditorDialog(
      order_id=order_id,
      folder_path=folder_path,
      parent=self
  )
         │
         ▼
Load Domain Model
  order = fetch_order_with_items(order_id)
  • Returns typed Order object
  • Includes patient, prescriber, items
  • Uses converters for data transformation
         │
         ▼
Populate UI Sections
  • Patient Info → _populate_patient_section()
  • Prescriber Info → _populate_prescriber_section()
  • Clinical Data → _populate_clinical_section()
  • Order Items → _populate_items_table()
  • Notes → _populate_notes_section()
         │
         ▼
Apply Theme (theme.qss)
  • Colors from centralized stylesheet
  • Component classes (primary, section-title, etc.)
  • Consistent hover/focus states
         │
         ▼
Show Dialog Modally
  dialog.exec()
         │
         ▼
User Interacts
  • Changes status → Workflow validation
  • Exports to portal → JSON builder
  • Generates HCFA-1500 → Billing form
  • Processes refill → Creates new order
         │
         ▼
Emit Signals
  order_updated.emit()
         │
         ▼
Parent Refreshes
  load_orders()  # Reload orders table
```

## Entry Points → Order Editor Mapping

| Entry Point | File | Line | Method | Action |
|------------|------|------|---------|--------|
| **Orders Table (double-click)** | app_legacy.py | 28683 | `on_orders_double_clicked()` | Extract ID → `open_order_editor()` |
| **Edit Order Button** | app_legacy.py | 10909 | `_handle_edit_order_button()` | Get selected → `open_order_editor()` |
| **Patient Dialog Orders** | app_legacy.py | 9564 | `edit_order_from_patient_dialog()` | Parse "ORD-036" → `open_order_editor()` |
| **Refill Processing** | app_legacy.py | 18565 | `edit_order_by_id()` | Validate ID → `open_order_editor()` |
| **Direct Calls** | Various | - | `edit_order()` | Extract ID → `open_order_editor()` |

## Theme System Integration

```
Application Startup
         │
         ▼
Load Theme (app.py)
  with open("assets/theme.qss") as f:
      app.setStyleSheet(f.read())
         │
         ▼
All Widgets Inherit Theme
  • QMainWindow → #1E1E1E background
  • QTableWidget → #2B2B2B with borders
  • QPushButton → Styled by class property
  • QLabel[class="section-title"] → Bold, blue
         │
         ▼
Order Editor Created
  • Inherits application theme
  • Uses class properties for specific styling
  • Consistent with rest of application
         │
         ▼
Components Auto-Styled
  button.setProperty("class", "primary")
  → Blue button with hover effects (from theme.qss)
```

## Domain Model Data Flow

```
┌──────────────────────────────────────────────────┐
│ fetch_order_with_items(order_id)                │
│                                                  │
│ 1. Query main order data                        │
│    SELECT * FROM orders WHERE id = ?            │
│                                                  │
│ 2. Query order items                            │
│    SELECT * FROM order_items WHERE order_id = ? │
│                                                  │
│ 3. Convert to domain objects                    │
│    • dict → Order (dataclass)                   │
│    • dict → OrderItem (dataclass)               │
│    • Apply converters (dates, bools, etc.)      │
│                                                  │
│ 4. Return typed structure                       │
│    order: Order                                 │
│      .id, .rx_date, .status, .notes             │
│      .patient_last_name, .patient_first_name    │
│      .prescriber_name, .prescriber_npi          │
│      .items: List[OrderItem]                    │
│        [0].hcpcs_code, .quantity, .refills      │
│        [0].modifier1, .modifier2, .modifier3... │
│                                                  │
│ 5. Order Editor populates UI from domain object │
└──────────────────────────────────────────────────┘
```

## Workflow Validation Flow

```
User Clicks "Change Status"
         │
         ▼
Show Status Dialog
  • Current: "Pending"
  • Available: Dropdown with valid transitions
         │
         ▼
User Selects New Status
  new_status = "Active"
         │
         ▼
Validate Transition
  from dmelogic.workflows.order_workflow import validate_status_transition
  
  is_valid = validate_status_transition(
      current_status=order.status,
      new_status=new_status
  )
         │
         ├─ Invalid ─► Show Error
         │              "Cannot transition Pending → Completed"
         │
         └─ Valid ──► Update Database
                       UPDATE orders SET order_status = ? WHERE id = ?
                       │
                       ▼
                     Reload Order
                       order = fetch_order_with_items(order_id)
                       │
                       ▼
                     Update UI
                       • Status badge reflects new status
                       • Color changes (Pending=orange → Active=blue)
                       │
                       ▼
                     Emit Signal
                       order_updated.emit()
                       │
                       ▼
                     Parent Refreshes
                       load_orders()
```

## Legacy vs Modern Comparison

### 🔴 Legacy Approach (Before)
```python
def edit_order(self):
    # 150+ lines of code
    conn = sqlite3.connect(...)
    cursor.execute("SELECT ...")
    order_data = cursor.fetchone()
    
    # Manual notes handling
    if notes:
        notes_dialog = QDialog()
        # 50 lines of inline styles
        notes_dialog.exec()
    
    cursor.execute("SELECT ... FROM order_items")
    order_items = cursor.fetchall()
    
    # Create legacy dialog
    dialog = NewOrderDialog(self, order_data, order_items, order_id)
    dialog.show()
```

### ✅ Modern Approach (After)
```python
def edit_order(self):
    # 5 lines of code
    order_id = self.get_order_id_from_selected_row()
    if order_id > 0:
        self.open_order_editor(order_id)
```

**Benefits:**
- **92% less code** per entry point
- **Single source of truth** for order editing
- **Domain model** handles data loading
- **Theme system** handles styling
- **Workflow engine** handles validation
- **Consistent UX** across all workflows

---

## Statistics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Entry Point Code** | 150+ lines | 5-15 lines | 90% reduction |
| **Order Editing Dialogs** | Multiple (NewOrderDialog, etc.) | 1 (OrderEditorDialog) | 100% consolidation |
| **Inline Styles** | Scattered throughout | 0 (uses theme.qss) | 100% centralized |
| **Data Loading** | Direct SQL in each method | Domain model | Type-safe |
| **Validation** | Manual checks | Workflow engine | Enforced |
| **Maintainability** | Low (duplicated code) | High (DRY principle) | ⭐⭐⭐⭐⭐ |

---

**Architecture Status**: PRODUCTION READY ✅  
**Integration**: COMPLETE 🚀  
**Theme Applied**: YES 🎨  
**Domain Model**: INTEGRATED ✨
