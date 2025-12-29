# Modern Dark Theme System - Complete Implementation

## Overview

The DME Logic application now has a unified, professional dark theme system based on VS Code's design language. All UI components use a centralized `theme.qss` file with consistent colors, spacing, and component styles.

## Key Principles

### 1. **Single Source of Truth**
- All styles defined in `assets/theme.qss`
- No inline `setStyleSheet()` calls
- Widget properties drive styling

### 2. **Consistent Design Language**
- Dark background: `#1E1E1E` (main), `#252526` (cards), `#2B2B2B` (tables)
- Primary accent: `#0078D4` (blue)
- Success: `#27ae60` (green)
- Danger: `#e74c3c` (red)
- Warning: `#f39c12` (orange)

### 3. **Component-Based Styling**
- Use properties: `widget.setProperty("class", "primary")`
- Use object names: `widget.setObjectName("OrderCard")`
- Let theme.qss handle appearance

## Color Palette

```python
# Background Colors
BACKGROUND_MAIN = "#1E1E1E"        # Main window background
BACKGROUND_CARD = "#252526"        # Cards, panels
BACKGROUND_TABLE = "#2B2B2B"       # Tables, lists
BACKGROUND_INPUT = "#1E1E1E"       # Text fields, combos
BACKGROUND_BUTTON = "#2B2B2B"      # Default buttons

# Border Colors
BORDER_MAIN = "#3A3A3A"            # Primary borders
BORDER_SEPARATOR = "#3D3D3D"       # Section separators
BORDER_HEADER = "#424242"          # Table headers

# Text Colors
TEXT_PRIMARY = "#E0E0E0"           # Main text
TEXT_SECONDARY = "#CCCCCC"         # Labels
TEXT_MUTED = "#808080"             # Disabled text
TEXT_WHITE = "#FFFFFF"             # Headings, selected

# Accent Colors
ACCENT_PRIMARY = "#0078D4"         # Primary actions (blue)
ACCENT_HOVER = "#106EBE"           # Hover state
ACCENT_SUCCESS = "#27ae60"         # Success (green)
ACCENT_DANGER = "#e74c3c"          # Danger (red)
ACCENT_WARNING = "#f39c12"         # Warning (orange)
```

## Component Styles

### Buttons

```python
from dmelogic.ui.theme_utils import (
    make_primary_button, make_secondary_button, make_danger_button
)

# Primary button (blue, for main actions)
save_btn = QPushButton("Save")
make_primary_button(save_btn)

# Secondary button (gray, for cancel/close)
cancel_btn = QPushButton("Cancel")
make_secondary_button(cancel_btn)

# Danger button (red, for delete/remove)
delete_btn = QPushButton("Delete")
make_danger_button(delete_btn)

# Or use convenience functions
from dmelogic.ui.theme_utils import create_primary_button
save_btn = create_primary_button("Save", parent=self)
```

### Labels

```python
from dmelogic.ui.theme_utils import (
    make_section_title, make_subsection_label, make_status_label
)

# Section title (large, bold)
title = QLabel("Patient Information")
make_section_title(title)

# Subsection (smaller, lighter)
subtitle = QLabel("Enter patient details")
make_subsection_label(subtitle)

# Status labels with color coding
status = QLabel("Success!")
make_status_label(status, "success")  # Green

error = QLabel("Error occurred")
make_status_label(error, "error")  # Red
```

### Cards & Panels

```python
from dmelogic.ui.theme_utils import make_card, make_section_header

# Card/panel with rounded corners
card = QWidget()
make_card(card, "OrderCard")

# Section header with bottom border
header = QFrame()
make_section_header(header)
```

### Tables

```python
from dmelogic.ui.theme_utils import setup_modern_table

# Tables automatically styled by theme.qss
table = QTableWidget()
setup_modern_table(table)  # Just configures behavior
# Appearance is handled by theme
```

## Usage Patterns

### Dialog/Window Setup

```python
class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Dialog")
        
        # No need to set background - theme.qss handles it
        layout = QVBoxLayout(self)
        
        # Title
        title = create_section_title("Dialog Title")
        layout.addWidget(title)
        
        # Content card
        card = QWidget()
        make_card(card)
        card_layout = QVBoxLayout(card)
        # ... add content ...
        layout.addWidget(card)
        
        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = create_primary_button("Save")
        cancel_btn = create_secondary_button("Cancel")
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
```

### Wizard Pages

```python
from dmelogic.ui.theme_utils import (
    make_wizard_title, make_wizard_subtitle, style_wizard_buttons
)

class WizardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Page title
        title = QLabel("Select Items")
        make_wizard_title(title)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Choose items to add to the order")
        make_wizard_subtitle(subtitle)
        layout.addWidget(subtitle)
        
        # ... content ...
        
        # Navigation buttons
        style_wizard_buttons(
            back_btn=self.back_button,
            next_btn=self.next_button,
            finish_btn=self.finish_button,
            cancel_btn=self.cancel_button
        )
```

### Search/Filter Bars

```python
from dmelogic.ui.theme_utils import make_search_container

# Search container with consistent styling
search_container = QWidget()
make_search_container(search_container)

search_layout = QHBoxLayout(search_container)
search_layout.addWidget(QLabel("Search:"))
search_layout.addWidget(QLineEdit())  # Styled by theme.qss

search_btn = create_primary_button("Search")
clear_btn = create_secondary_button("Clear")

search_layout.addWidget(search_btn)
search_layout.addWidget(clear_btn)
```

## Migration Guide

### Before (Inline Styles)

```python
# ❌ Old way - inline styles
self.title_label = QLabel("Order Editor")
self.title_label.setStyleSheet("""
    font-size: 14pt;
    font-weight: bold;
    color: white;
""")

self.save_button = QPushButton("Save")
self.save_button.setStyleSheet("""
    QPushButton {
        background-color: #0078D4;
        color: white;
        padding: 6px 14px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #106EBE;
    }
""")

self.orders_table = QTableWidget()
self.orders_table.setStyleSheet("""
    QTableWidget {
        background-color: #2B2B2B;
        color: white;
        selection-background-color: #0078D4;
    }
""")
```

### After (Theme Classes)

```python
# ✅ New way - theme classes
from dmelogic.ui.theme_utils import (
    make_wizard_title, make_primary_button, setup_modern_table
)

self.title_label = QLabel("Order Editor")
make_wizard_title(self.title_label)

self.save_button = QPushButton("Save")
make_primary_button(self.save_button)

self.orders_table = QTableWidget()
setup_modern_table(self.orders_table)
# Style comes from theme.qss automatically
```

## Component Reference

### Button Classes

| Class | Appearance | Use Case |
|-------|------------|----------|
| `primary` | Blue, bold | Save, Add, Create, Submit |
| `secondary` | Gray, normal | Cancel, Close, Back |
| `danger` | Red, bold | Delete, Remove, Clear |
| `success` | Green, bold | Complete, Confirm, Approve |
| `icon` | Transparent | Toolbar icons, minimal buttons |
| `folder-quick` | Gray, checkable | Quick folder navigation |
| `wizard-back` | Gray | Wizard back navigation |
| `wizard-next` | Blue | Wizard next navigation |
| `wizard-finish` | Green | Wizard completion |

### Label Classes

| Class | Appearance | Use Case |
|-------|------------|----------|
| `section-title` | 13px, bold, white | Section headings |
| `subsection` | 11px, lighter | Subsection text |
| `wizard-title` | 16px, bold | Wizard page titles |
| `wizard-subtitle` | 11px, light | Wizard descriptions |
| `status-success` | Green, bold | Success messages |
| `status-warning` | Orange, bold | Warning messages |
| `status-error` | Red, bold | Error messages |
| `status-info` | Blue, bold | Info messages |
| `badge` | Blue, pill-shaped | Notification counts |
| `badge-danger` | Red, pill-shaped | Alert counts |
| `highlight` | Blue text | Emphasized inline text |
| `monospace` | Courier font | IDs, codes, technical |
| `empty-state` | Large, muted | "No items" messages |
| `summary-main` | Bold, white | Bottom panel main text |
| `summary-sub` | Small, gray | Bottom panel secondary |

### Container Classes

| Object Name / Class | Appearance | Use Case |
|---------------------|------------|----------|
| `OrderCard` | Rounded, bordered | Content panels |
| `PageCard` | Same as OrderCard | Wizard pages |
| `ContentCard` | Same as OrderCard | General content |
| `section-header` | Bottom border | Section separators |
| `SearchContainer` | Bordered panel | Search/filter bars |
| `SummaryPanel` | Top border | Footer/summary areas |
| `StatusBadge` | Custom | Order status display |

## Theme File Structure

```
assets/theme.qss
├── BASE APPLICATION STYLES
│   ├── QMainWindow, QDialog, QWidget
│   └── Global font and colors
├── CARDS & PANELS
│   ├── OrderCard, PageCard
│   └── Section headers
├── GROUP BOXES
│   └── Legacy form sections
├── TABS
│   └── Main application tabs
├── INPUT CONTROLS
│   ├── QLineEdit, QComboBox, QTextEdit
│   └── Focus and disabled states
├── BUTTONS
│   ├── Default style
│   ├── Primary, secondary, danger, success
│   └── Hover and pressed states
├── TABLES
│   ├── QTableWidget, QTreeWidget
│   ├── Headers
│   └── Scrollbars
├── CHECKBOXES & RADIO BUTTONS
├── SLIDERS & PROGRESS BARS
├── MENUS & CONTEXT MENUS
├── TOOLTIPS
├── STATUS BAR
├── SPLITTERS
├── DOCK WIDGETS
└── CUSTOM COMPONENT STYLES
    ├── Status labels
    ├── Badges
    ├── Summary panels
    └── Wizard-specific
```

## Best Practices

### DO ✅

1. **Use theme utilities**
   ```python
   from dmelogic.ui.theme_utils import make_primary_button
   make_primary_button(my_button)
   ```

2. **Use widget properties**
   ```python
   button.setProperty("class", "primary")
   button.style().unpolish(button)
   button.style().polish(button)
   ```

3. **Use object names for unique components**
   ```python
   card.setObjectName("OrderCard")
   ```

4. **Let theme.qss handle appearance**
   - Tables, inputs, tabs all styled automatically

5. **Use convenience functions**
   ```python
   save_btn = create_primary_button("Save", parent=self)
   ```

### DON'T ❌

1. **Don't use inline setStyleSheet**
   ```python
   # ❌ Bad
   button.setStyleSheet("background-color: blue;")
   
   # ✅ Good
   make_primary_button(button)
   ```

2. **Don't hardcode colors**
   ```python
   # ❌ Bad
   label.setStyleSheet("color: #0078D4;")
   
   # ✅ Good
   make_highlight_label(label)
   ```

3. **Don't mix inline and theme styles**
   - Pick one approach and stick with it

4. **Don't override theme.qss with inline styles**
   - If theme needs changes, update theme.qss

## Testing the Theme

### Visual Inspection Checklist

- [ ] All buttons have consistent padding and border radius
- [ ] Primary actions are blue
- [ ] Danger actions are red
- [ ] Tables have dark background with blue selection
- [ ] Input fields have blue focus border
- [ ] Tabs have blue selected state
- [ ] All text is readable (sufficient contrast)
- [ ] Hover states work on all interactive elements
- [ ] Disabled states are visually distinct

### Test Script

```python
# test_theme.py
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from dmelogic.ui.theme_utils import *

app = QApplication([])

# Load theme
with open("assets/theme.qss", "r") as f:
    app.setStyleSheet(f.read())

dialog = QDialog()
layout = QVBoxLayout(dialog)

# Test all button types
layout.addWidget(create_primary_button("Primary Button"))
layout.addWidget(create_secondary_button("Secondary Button"))
layout.addWidget(create_danger_button("Danger Button"))

# Test labels
layout.addWidget(create_section_title("Section Title"))
layout.addWidget(create_wizard_title("Wizard Title"))

dialog.show()
app.exec()
```

## Troubleshooting

### Styles Not Applying

**Problem**: Widget doesn't show theme styles

**Solutions**:
1. Make sure theme is loaded in app.py
2. Call `widget.style().unpolish()` then `widget.style().polish()`
3. Check property spelling: `"class"` not `"className"`

### Colors Look Wrong

**Problem**: Some colors don't match palette

**Solution**: Check if widget has inline `setStyleSheet()` overriding theme

### Buttons Not Themed

**Problem**: Buttons look default, not styled

**Solution**: 
```python
# After setting property, refresh style:
button.setProperty("class", "primary")
button.style().unpolish(button)
button.style().polish(button)

# Or use helper:
make_primary_button(button)
```

## Theme Customization

To create a light theme variant:

1. Copy `theme.qss` to `theme_light.qss`
2. Update colors:
   ```css
   QMainWindow, QDialog, QWidget {
       background-color: #FFFFFF;  /* Light background */
       color: #333333;             /* Dark text */
   }
   ```
3. Switch themes at runtime:
   ```python
   with open("assets/theme_light.qss") as f:
       app.setStyleSheet(f.read())
   ```

## Files

- `assets/theme.qss` - Main theme stylesheet (800+ lines)
- `dmelogic/ui/theme_utils.py` - Theme utility functions (300+ lines)
- `dmelogic/ui/order_editor.py` - Example using theme (updated)
- `THEME_SYSTEM.md` - This documentation

## Related Documentation

- `UI_DESIGN_SYSTEM.md` - Overall UI architecture
- `UI_CONSISTENCY_SUMMARY.md` - UI consistency guidelines
- `ORDER_EDITOR_IMPLEMENTATION.md` - Modern editor implementation

---

**Status**: ✅ Complete and ready for use
**Last Updated**: December 6, 2025

