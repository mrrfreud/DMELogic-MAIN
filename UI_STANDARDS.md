# UI Standards & Design System - DMELogic

## Overview

This document defines the **visual consistency standards** for DMELogic to ensure a unified, professional, commercial appearance across all screens. All UI components follow these patterns to create a cohesive user experience comparable to enterprise DME systems like Brightree, Bonafide, and AlayaCare.

---

## Design Philosophy

### Core Principles

1. **Consistency**: All screens use identical layouts, colors, fonts, and spacing
2. **Clarity**: Clean visual hierarchy with clear action paths
3. **Efficiency**: Minimize clicks, maximize information density
4. **Accessibility**: High contrast, readable fonts, logical tab order
5. **Professional**: Enterprise-grade visual polish

### Color Psychology

- **Blue (#007acc)**: Primary actions, trust, stability
- **Green (#28a745)**: Success, completion, positive status
- **Yellow (#ffc107)**: Warnings, attention needed, pending
- **Red (#dc3545)**: Errors, cancellations, overdue items

---

## Standard Page Layout

### Layout Pattern

Every screen follows this structure:

```
┌─────────────────────────────────────────────────┐
│ PageHeader (Title + Subtitle)                   │
├─────────────────────────────────────────────────┤
│ FilterRow (Search + Filters)                    │
├─────────────────────────────────────────────────┤
│                                                 │
│                                                 │
│         Content Area (Table/Form/Grid)          │
│                                                 │
│                                                 │
├─────────────────────────────────────────────────┤
│ SummaryFooter (Summary Text + Action Buttons)   │
└─────────────────────────────────────────────────┘
```

**Margins**: 16px all sides  
**Spacing**: 12px between sections

### Code Template

```python
from dmelogic.ui.components import create_standard_page_layout

# Create layout
main_layout, header, content, footer = create_standard_page_layout(
    title="Orders",
    subtitle="View and manage customer orders",
    parent=self
)
self.setLayout(main_layout)

# Add filters to content
filter_row, search_bar = create_filter_bar_with_search(
    search_label="Search Orders:",
    search_placeholder="Patient name, RX#..."
)
content.layout().addWidget(filter_row)

# Add table to content
self.table = QTableWidget()
apply_standard_table_style(self.table)
content.layout().addWidget(self.table, stretch=1)

# Configure footer
footer.setSummaryText("Total: 25 orders")
footer.addPrimaryButton("New Order", self.on_create)
footer.addSecondaryButton("Export", self.on_export)
```

---

## Reusable Components

### 1. PageHeader

**Purpose**: Page title and subtitle with consistent typography

**Usage**:
```python
from dmelogic.ui.components import PageHeader

header = PageHeader(
    title="Order Management",
    subtitle="View and manage customer orders"
)
```

**Styling**:
- Title: 16pt bold, white (#ffffff)
- Subtitle: 10pt normal, gray (#888888)
- Bottom margin: 12px

---

### 2. SearchBar

**Purpose**: Consistent search input with label and clear button

**Usage**:
```python
from dmelogic.ui.components import SearchBar

search_bar = SearchBar(
    label="Search:",
    placeholder="Type to search..."
)
search_bar.textChanged.connect(self.on_search)
search_bar.searchCleared.connect(self.on_search_cleared)
```

**Features**:
- Auto-enables clear button when text present
- Emits `textChanged(str)` signal
- Emits `searchCleared()` when cleared

---

### 3. SummaryFooter

**Purpose**: Summary statistics with action buttons

**Usage**:
```python
from dmelogic.ui.components import SummaryFooter

footer = SummaryFooter()
footer.setSummaryText("Total: 25 orders | Pending: 10")
footer.addPrimaryButton("Create Order", self.on_create)
footer.addSecondaryButton("Export", self.on_export)
footer.addSecondaryButton("Print", self.on_print)
```

**Layout**:
- Summary text: Left-aligned, bold
- Buttons: Right-aligned, 8px spacing

---

### 4. ActionButtonRow

**Purpose**: Horizontal row of action buttons

**Usage**:
```python
from dmelogic.ui.components import ActionButtonRow

button_row = ActionButtonRow()
button_row.addPrimaryButton("Save", self.on_save)
button_row.addSecondaryButton("Cancel", self.on_cancel)
button_row.addSpacer()  # Push remaining buttons right
button_row.addDangerButton("Delete", self.on_delete)
```

---

### 5. StatusBadge

**Purpose**: Color-coded status indicator

**Usage**:
```python
from dmelogic.ui.components import StatusBadge

badge = StatusBadge("Pending", status_type="warning")
badge = StatusBadge("Completed", status_type="success")
badge = StatusBadge("Overdue", status_type="danger")
```

**Types**:
- `success`: Green background, white text
- `warning`: Yellow background, black text
- `danger`: Red background, white text
- `info`: Blue background, white text
- `neutral`: Gray background, white text

---

### 6. FilterRow

**Purpose**: Container for multiple filter controls

**Usage**:
```python
from dmelogic.ui.components import FilterRow

filter_row = FilterRow()
search_bar = filter_row.addSearchBar("Search:", "Type to search...")
filter_row.addWidget(my_combo_box)
filter_row.addSpacer()
```

---

## Button Standards

### Button Types

#### Primary Button (`#primary-button`)
**Use for**: Main action on page (Create, Save, Submit)

```python
btn = QPushButton("Create Order")
btn.setObjectName("primary-button")
```

**Style**:
- Background: Blue (#007acc)
- Text: White, bold
- Min width: 100px
- Min height: 28px
- Border radius: 4px

#### Secondary Button (`#secondary-button`)
**Use for**: Supporting actions (Cancel, Export, Refresh)

```python
btn = QPushButton("Cancel")
btn.setObjectName("secondary-button")
```

**Style**:
- Background: Dark gray (#2b2b2b)
- Text: Light gray (#cfcfcf)
- Border: 1px solid #555555

#### Danger Button (`#danger-button`)
**Use for**: Destructive actions (Delete, Cancel Order)

```python
btn = QPushButton("Delete")
btn.setObjectName("danger-button")
```

**Style**:
- Background: Red (#dc3545)
- Text: White, bold

### Button Placement Rules

1. **Primary action**: Left-most in footer/button row
2. **Cancel/Close**: Next to primary action
3. **Destructive actions**: Right-most (after spacer)
4. **Export/Print**: Between primary and destructive

**Example**:
```
[Save] [Cancel] [Refresh]        [Delete]
  ^       ^         ^                ^
Primary  Secondary  Secondary     Danger
```

---

## Table Standards

### Standard Table Configuration

```python
from dmelogic.ui.styling import apply_standard_table_style

table = QTableWidget()
apply_standard_table_style(table)

# Sets:
# - Row height: 32px
# - Font: Segoe UI, 9pt
# - Alternating row colors
# - Row selection mode
```

### Column Width Guidelines

| Content Type | Width | Example |
|--------------|-------|---------|
| ID/Code | 80-100px | Order ID, HCPCS |
| Date | 100-120px | 2025-12-05 |
| Name | 150-200px | Patient/Prescriber Name |
| Phone | 120px | (555) 123-4567 |
| Status | 100px | Pending, Delivered |
| Description | 250-300px | Item descriptions |
| Dollar Amount | 100px | $1,234.56 |

### Cell Alignment

- **Text**: Left-aligned
- **Numbers**: Right-aligned
- **Dates**: Center-aligned
- **Status**: Center-aligned

```python
from dmelogic.ui.styling import (
    create_centered_item, create_right_aligned_item
)

# Centered (for dates, status)
item = create_centered_item("2025-12-05")

# Right-aligned (for numbers)
item = create_right_aligned_item("$1,234.56")
```

---

## Color Coding

### Refill Status Colors

Used for refills due screen and any time-sensitive items:

```python
from dmelogic.ui.styling import create_refill_status_item

# Overdue (< 0 days): Red background
item = create_refill_status_item("Patient Name", days_until_due=-5)

# Due soon (0-7 days): Yellow background
item = create_refill_status_item("Patient Name", days_until_due=3)

# Future (> 7 days): Subtle green background
item = create_refill_status_item("Patient Name", days_until_due=15)
```

**Color Rules**:
- **Overdue** (days < 0): Red (#dc3545, 30% opacity)
- **Due Soon** (0-7 days): Yellow (#ffc107, 30% opacity)
- **Future** (> 7 days): Green (#28a745, 20% opacity)

### Order Status Colors

```python
from dmelogic.ui.styling import create_order_status_item

item = create_order_status_item("Pending", "Pending")
item = create_order_status_item("Verified", "Verified")
item = create_order_status_item("Delivered", "Delivered")
item = create_order_status_item("Cancelled", "Cancelled")
```

**Status Colors**:
- **Pending**: Yellow background
- **Verified**: Blue background
- **Delivered/Completed**: Green background
- **Cancelled/Rejected**: Red background

---

## Typography

### Font Standards

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Page Title | Segoe UI | 16pt | Bold | #ffffff |
| Page Subtitle | Segoe UI | 10pt | Normal | #888888 |
| Table Headers | Segoe UI | 9pt | Bold | #cfcfcf |
| Table Cells | Segoe UI | 9pt | Normal | #e5e5e5 |
| Button Text | Segoe UI | 9pt | Bold | Varies |
| Input Text | Segoe UI | 9pt | Normal | #e5e5e5 |
| Labels | Segoe UI | 9pt | Bold | #cfcfcf |

### Hierarchy Rules

1. **Page Title**: Largest, boldest (16pt bold)
2. **Section Headers**: 10-12pt bold
3. **Body Text**: 9pt normal
4. **Helper Text**: 8pt normal, muted color

---

## Spacing System

### Base Unit: 4px

All spacing follows 4px increments:

| Name | Value | Use Case |
|------|-------|----------|
| xs | 4px | Tight spacing (icon to text) |
| sm | 8px | Related elements (button row spacing) |
| md | 12px | Section spacing (filter row to table) |
| lg | 16px | Page margins, major sections |
| xl | 24px | Large gaps (between tabs) |

### Layout Margins

```python
# Page margins
layout.setContentsMargins(16, 16, 16, 16)

# Component spacing
layout.setSpacing(12)

# Button row
button_layout.setSpacing(8)
```

---

## Theme System

### Loading Theme

All screens automatically inherit theme from `dark.qss`:

```python
# In main application startup (app_with_npi.py)
from theme.theme_manager import apply_dark_theme

app = QApplication(sys.argv)
apply_dark_theme(app)
```

### Custom Styling

Only use custom inline styles when **absolutely necessary**. Prefer QSS selectors:

```python
# ❌ Bad: Inline styles
btn.setStyleSheet("background-color: blue; color: white;")

# ✅ Good: Use object name + QSS
btn.setObjectName("primary-button")  # Styled by dark.qss
```

### Object Names

Standard object names for QSS styling:

| Object Name | Element | Style |
|-------------|---------|-------|
| `page-title` | QLabel | 16pt bold, white |
| `page-subtitle` | QLabel | 10pt, gray |
| `search-label` | QLabel | 9pt bold |
| `search-input` | QLineEdit | Dark bg, blue focus |
| `summary-label` | QLabel | 10pt bold |
| `primary-button` | QPushButton | Blue bg, white text |
| `secondary-button` | QPushButton | Gray bg, light text |
| `danger-button` | QPushButton | Red bg, white text |
| `status-badge` | QLabel | Rounded, color-coded |
| `separator` | QFrame | 1px line, gray |

---

## Screen Templates

### Template 1: Data Grid Screen (Orders, Patients, Inventory)

```python
class OrdersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        # Standard layout
        layout, header, content, footer = create_standard_page_layout(
            title="Orders",
            subtitle="View and manage customer orders"
        )
        self.setLayout(layout)
        
        # Filter row
        filter_row = FilterRow()
        self.search_bar = filter_row.addSearchBar("Search:", "Patient, RX#...")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Pending", "Verified", "Delivered"])
        filter_row.addWidget(QLabel("Status:"))
        filter_row.addWidget(self.status_combo)
        filter_row.addSpacer()
        content.layout().addWidget(filter_row)
        
        # Table
        self.table = QTableWidget()
        apply_standard_table_style(self.table)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Patient", "Items", "Status", "Total", "Actions"
        ])
        content.layout().addWidget(self.table, stretch=1)
        
        # Footer
        footer.setSummaryText("Total: 0 orders")
        footer.addPrimaryButton("New Order", self.on_create)
        footer.addSecondaryButton("Export", self.on_export)
        footer.addSecondaryButton("Print", self.on_print)
```

### Template 2: Form/Dialog Screen

```python
class PatientFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patient Details")
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = PageHeader(
            title="Patient Information",
            subtitle="Enter patient demographics"
        )
        layout.addWidget(header)
        
        # Form fields
        form_layout = QFormLayout()
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.dob = QDateEdit()
        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Date of Birth:", self.dob)
        layout.addLayout(form_layout)
        
        # Button row
        button_row = ActionButtonRow()
        button_row.addPrimaryButton("Save", self.accept)
        button_row.addSecondaryButton("Cancel", self.reject)
        layout.addWidget(button_row)
```

---

## Implementation Checklist

### For New Screens

- [ ] Use `create_standard_page_layout()` for layout
- [ ] Add `PageHeader` with title and subtitle
- [ ] Use `FilterRow` + `SearchBar` for filters
- [ ] Apply `apply_standard_table_style()` to tables
- [ ] Use `SummaryFooter` with action buttons
- [ ] Set button object names (`primary-button`, `secondary-button`)
- [ ] Use color-coded items for status/urgency
- [ ] Test with dark.qss theme loaded

### For Existing Screens

- [ ] Replace custom layouts with standard components
- [ ] Remove inline styles (use QSS selectors)
- [ ] Update button styles to use object names
- [ ] Apply standard table configuration
- [ ] Ensure consistent margins (16px) and spacing (12px)
- [ ] Add PageHeader if missing
- [ ] Replace custom search with SearchBar component

---

## Examples

### Complete Screen Example

See `dmelogic/ui/refill_screen.py` for a fully implemented example showing:

✅ Standard page layout  
✅ PageHeader with title/subtitle  
✅ FilterRow with SearchBar and date filters  
✅ Color-coded table cells (refill urgency)  
✅ SummaryFooter with statistics and action buttons  
✅ All styling via dark.qss (no inline styles)

### Component Usage Examples

```python
# Search bar with filtering
search_bar = SearchBar(label="Search:", placeholder="Type to search...")
search_bar.textChanged.connect(lambda text: self.filter_table(text))

# Status badge in table cell
badge = StatusBadge("Pending", status_type="warning")
table.setCellWidget(row, col, badge)

# Color-coded refill item
days_until = -5  # Overdue
item = create_refill_status_item("Patient Name", days_until)
table.setItem(row, col, item)

# Action buttons in footer
footer = SummaryFooter()
footer.setSummaryText(f"Total: {count} items")
footer.addPrimaryButton("Process", self.on_process)
footer.addSecondaryButton("Export", self.on_export)
```

---

## Best Practices

### ✅ DO

- Use standard components from `dmelogic.ui.components`
- Apply `apply_standard_table_style()` to all tables
- Use object names for QSS styling (`setObjectName()`)
- Follow 16px margins, 12px spacing consistently
- Color-code time-sensitive data (refills, due dates)
- Use `PageHeader` for all major screens
- Use `SummaryFooter` for statistics and actions

### ❌ DON'T

- Create custom layouts when standard components exist
- Use inline `setStyleSheet()` (use QSS selectors)
- Mix different button styles on same screen
- Use random colors (stick to theme palette)
- Forget to apply `apply_standard_table_style()`
- Create one-off widgets (reuse components)
- Hardcode colors (use StatusColors constants)

---

## Resources

### Code Files

- **Components**: `dmelogic/ui/components.py` (reusable widgets)
- **Styling**: `dmelogic/ui/styling.py` (color coding, table helpers)
- **Theme**: `theme/dark.qss` (global styles)
- **Theme Manager**: `theme/theme_manager.py` (theme loading)
- **Example**: `dmelogic/ui/refill_screen.py` (complete implementation)

### Documentation

- **THEME_QUICK_REFERENCE.md**: QSS selector reference
- **UI_DESIGN_SYSTEM.md**: Color palette and typography
- **This Document**: Complete UI standards guide

---

## Migration Guide

### Converting Existing Tab to Standard Layout

**Before** (custom layout):
```python
class OrdersTab(QWidget):
    def __init__(self):
        layout = QVBoxLayout()
        
        # Custom header
        title = QLabel("Orders")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Custom search
        search = QLineEdit()
        search.setPlaceholderText("Search...")
        layout.addWidget(search)
        
        # Table
        table = QTableWidget()
        layout.addWidget(table)
        
        # Custom buttons
        btn_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.setStyleSheet("background: blue; color: white;")
        btn_layout.addWidget(create_btn)
        layout.addLayout(btn_layout)
```

**After** (standard components):
```python
from dmelogic.ui.components import create_standard_page_layout, FilterRow
from dmelogic.ui.styling import apply_standard_table_style

class OrdersTab(QWidget):
    def __init__(self):
        # Standard layout
        layout, header, content, footer = create_standard_page_layout(
            title="Orders",
            subtitle="View and manage customer orders"
        )
        self.setLayout(layout)
        
        # Standard search
        filter_row, search_bar = create_filter_bar_with_search(
            search_label="Search:",
            search_placeholder="Patient, RX#..."
        )
        content.layout().addWidget(filter_row)
        
        # Table with standard styling
        table = QTableWidget()
        apply_standard_table_style(table)
        content.layout().addWidget(table, stretch=1)
        
        # Standard footer with buttons
        footer.setSummaryText("Total: 0 orders")
        footer.addPrimaryButton("Create Order", self.on_create)
```

**Result**: Cleaner code, consistent appearance, no custom styles!

---

## Support

For questions or clarification on UI standards:

1. Review example implementation: `dmelogic/ui/refill_screen.py`
2. Check component docstrings: `dmelogic/ui/components.py`
3. Consult theme reference: `THEME_QUICK_REFERENCE.md`
4. Review color coding: `dmelogic/ui/styling.py`

**Remember**: Consistency is key. When all screens follow the same patterns, the application feels professional and polished! 🎨
