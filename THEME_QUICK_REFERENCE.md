# UI Consistency Quick Reference

## 🎨 Apply Theme (Do This First!)

```python
from theme_manager import apply_theme

app = QApplication(sys.argv)
apply_theme(app, "dark")  # Apply once at app startup
```

---

## 📊 Table Styling

```python
from theme_manager import ThemeSpacing

# Set standard row height
table.verticalHeader().setDefaultSectionSize(ThemeSpacing.TABLE_ROW_HEIGHT)

# Enable alternating row colors (optional)
table.setAlternatingRowColors(True)

# Enable selection
table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
```

**Headers**: Automatically styled as UPPERCASE, bold, with blue bottom border

---

## 🔘 Button Types

```python
# Primary Button (automatic - default styling)
btn_create = QPushButton("Create Order")

# Success Button (green)
btn_save = QPushButton("Save")
btn_save.setProperty("class", "success")

# Danger Button (red)
btn_delete = QPushButton("Delete")
btn_delete.setProperty("class", "danger")

# Secondary Button (gray)
btn_cancel = QPushButton("Cancel")
btn_cancel.setProperty("class", "secondary")

# Warning Button (yellow)
btn_warning = QPushButton("Warning")
btn_warning.setProperty("class", "warning")
```

---

## 🏷️ Status Badges

```python
status = QLabel("PENDING")
status.setProperty("class", "status-badge")
status.setProperty("status", "pending")  # pending, active, completed, cancelled
```

**Available Status Types**:
- `active` - Green
- `pending` - Yellow
- `completed` - Blue
- `cancelled` - Red
- `inactive` - Gray

---

## 📝 Form Layouts

```python
from theme_manager import ThemeSpacing

form_layout = QFormLayout()
form_layout.setHorizontalSpacing(ThemeSpacing.MEDIUM)
form_layout.setVerticalSpacing(ThemeSpacing.MEDIUM)
form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

# Labels automatically styled
label = QLabel("Patient Name:")
label.setProperty("class", "form-label")
form_layout.addRow(label, name_input)
```

---

## 🎨 Using Theme Colors in Code

```python
from theme_manager import ThemeColors
from PyQt6.QtGui import QColor

# Set custom colors
item.setBackground(QColor(ThemeColors.BG_SURFACE))
item.setForeground(QColor(ThemeColors.TEXT_PRIMARY))

# Highlight conditions
if condition:
    item.setBackground(QColor(ThemeColors.WARNING))
```

**Available Colors**:
- `ThemeColors.PRIMARY` - `#007acc`
- `ThemeColors.SUCCESS` - `#28a745`
- `ThemeColors.WARNING` - `#ffc107`
- `ThemeColors.DANGER` - `#dc3545`
- `ThemeColors.BG_DARK` - `#1e1e1e`
- `ThemeColors.BG_SURFACE` - `#2b2b2b`
- `ThemeColors.TEXT_PRIMARY` - `#e5e5e5`
- `ThemeColors.TEXT_MUTED` - `#888888`

---

## 📏 Spacing

```python
from theme_manager import ThemeSpacing

# Use consistent spacing
layout.setSpacing(ThemeSpacing.MEDIUM)
layout.setContentsMargins(
    ThemeSpacing.LARGE,   # left
    ThemeSpacing.LARGE,   # top
    ThemeSpacing.LARGE,   # right
    ThemeSpacing.LARGE    # bottom
)

# Add spacing between sections
layout.addSpacing(ThemeSpacing.XLARGE)
```

**Spacing Values**:
- `SMALL` = 8px
- `MEDIUM` = 12px
- `LARGE` = 16px
- `XLARGE` = 24px

---

## 📋 Table Column Alignment

```python
# Right-align numeric columns (quantity, price)
for row in range(table.rowCount()):
    item = table.item(row, qty_column)
    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

# Center-align dates and status
for row in range(table.rowCount()):
    item = table.item(row, date_column)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

# Left-align text (names, descriptions) - default
```

---

## ✨ Special Formatting

### Patient Names - Always Bold
```python
patient_item = QTableWidgetItem("John Smith")
font = patient_item.font()
font.setBold(True)
patient_item.setFont(font)
```

### HCPCS Codes - Monospace, Uppercase
```python
hcpcs_item = QTableWidgetItem("E0601")
font = QFont("Consolas", 9)
hcpcs_item.setFont(font)
```

### Money - Formatted with $
```python
price_item = QTableWidgetItem(f"${amount:,.2f}")
price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
```

### Dates - Consistent Format
```python
date_item = QTableWidgetItem(date_str)  # Use YYYY-MM-DD format
date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
```

---

## 🚀 Module Header Pattern

Every module screen should have this structure:

```python
header_layout = QHBoxLayout()

# Left: Icon + Title
title = QLabel("Refill Due Tracking")
title.setProperty("class", "section-header")
header_layout.addWidget(title)

# Center: Filters/Controls
header_layout.addWidget(QLabel("From:"))
header_layout.addWidget(from_date)
header_layout.addWidget(QLabel("To:"))
header_layout.addWidget(to_date)
header_layout.addWidget(generate_btn)

# Right: Spacer + Actions
header_layout.addStretch()
header_layout.addWidget(action_btn)
```

---

## ⚠️ Common Mistakes to Avoid

❌ **Don't** mix custom colors with theme - use theme colors
❌ **Don't** hard-code spacing - use `ThemeSpacing`
❌ **Don't** vary row heights - use `TABLE_ROW_HEIGHT`
❌ **Don't** use mixed font sizes - use theme defaults
❌ **Don't** apply theme multiple times - once at startup
❌ **Don't** skip button classes - always set class for colored buttons

✅ **Do** use `apply_theme()` once at app startup
✅ **Do** use `ThemeColors` constants
✅ **Do** use `ThemeSpacing` for layout
✅ **Do** follow table column alignment rules
✅ **Do** bold patient names
✅ **Do** use status badges for status fields
✅ **Do** right-align money and numbers

---

## 🧪 Testing Your Screen

**Consistency Checklist**:
- [ ] Theme applied at startup
- [ ] Table headers are UPPERCASE and bold
- [ ] Table row height is 32px
- [ ] Patient names are bold
- [ ] Numeric columns right-aligned
- [ ] Date columns center-aligned
- [ ] Status uses status badge
- [ ] Buttons have proper colors (success/danger)
- [ ] Spacing uses multiples of 4px
- [ ] Forms use 12px spacing
- [ ] Hover states work on buttons
- [ ] Selection color is blue (#007acc)

---

## 📖 Full Documentation

See `UI_DESIGN_SYSTEM.md` for complete standards.

---

## 💡 Need Help?

**Problem**: Colors don't match
**Solution**: Make sure `apply_theme(app, "dark")` is called before creating widgets

**Problem**: Buttons look wrong
**Solution**: Use `setProperty("class", "success")` after creating button

**Problem**: Table looks inconsistent
**Solution**: Set row height with `ThemeSpacing.TABLE_ROW_HEIGHT`

**Problem**: Spacing looks off
**Solution**: Use `ThemeSpacing` constants, not hard-coded pixel values
