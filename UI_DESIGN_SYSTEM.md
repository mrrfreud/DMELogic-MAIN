# DME Logic UI Design System

## Complete Enterprise-Grade UI Standards

This document defines the complete visual identity and UI standards for DME Logic,
ensuring a professional, consistent appearance across all screens and modules.

---

## 1. Color Palette

### Primary Colors
- **Primary Blue**: `#007acc` - Primary actions, selections, links, focus states
- **Success Green**: `#28a745` - Success messages, positive indicators, save actions
- **Warning Yellow**: `#ffc107` - Warnings, attention needed, pending states
- **Danger Red**: `#dc3545` - Errors, delete actions, critical alerts

### Background Colors
- **Main Background**: `#1e1e1e` - Application window background
- **Surface**: `#2b2b2b` - Cards, panels, table backgrounds
- **Hover State**: `#2d2d2d` - Interactive element hover
- **Selected**: `#007acc` - Selected items

### Border Colors
- **Default Border**: `#3a3a3a` - Subtle borders, dividers
- **Focus Border**: `#007acc` - Focused input fields
- **Table Grid**: `#3a3a3a` - Table cell borders

### Text Colors
- **Primary Text**: `#e5e5e5` - Main content text
- **Secondary Text**: `#cfcfcf` - Headers, labels, less emphasis
- **Muted Text**: `#888888` - Disabled, hints, placeholders
- **Inverse Text**: `#ffffff` - Text on colored backgrounds

---

## 2. Typography

### Font Family
- **Primary**: Segoe UI (Windows), -apple-system (Mac), Arial (fallback)
- **Monospace**: Consolas, Courier New (for codes, IDs)

### Font Sizes
- **Base**: 9pt (body text, table cells)
- **Small**: 8pt (status badges, footnotes)
- **Medium**: 10pt (input fields, buttons)
- **Large**: 11pt (section headers)
- **XLarge**: 12pt (page titles)

### Font Weights
- **Normal**: 400 - Body text
- **Medium**: 500 - Form labels, important text
- **Semibold**: 600 - Section headers
- **Bold**: 700 - Table headers, emphasis

### Text Transforms
- **Table Headers**: UPPERCASE, bold, letter-spacing: 0.5px
- **Status Badges**: UPPERCASE, semibold
- **HCPCS Codes**: UPPERCASE, monospace
- **Patient Names**: Sentence case, bold in tables

---

## 3. Spacing System

### Base Unit: 4px
All spacing should be multiples of 4px for consistency.

### Standard Spacing
- **Small**: 8px - Compact spacing, icon padding
- **Medium**: 12px - Default element spacing
- **Large**: 16px - Section padding
- **XLarge**: 24px - Major section separation

### Component Spacing
- **Button Padding**: 10px (v) × 16px (h)
- **Input Padding**: 8px (v) × 12px (h)
- **Table Cell Padding**: 8px (v) × 12px (h)
- **Form Label Margin**: 12px right
- **Section Header Margin**: 24px top, 12px bottom

---

## 4. Layout Standards

### Grid System
Use 12-column responsive grid:
- 1 column = ~8.33% width
- Gutter: 16px between columns
- Container padding: 24px

### Common Layouts

#### Module Header
```
┌────────────────────────────────────────────────────────┐
│ [Icon] Page Title        [Filters...]    [Actions...]  │
└────────────────────────────────────────────────────────┘
```
- Height: 60px
- Background: `#2b2b2b`
- Border-bottom: 1px solid `#3a3a3a`

#### Data Table Screen
```
┌────────────────────────────────────────────────────────┐
│ Module Header (filters, search, date range)           │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Data Table (sortable, selectable)                    │
│                                                        │
├────────────────────────────────────────────────────────┤
│ Actions: [Primary] [Secondary] [Danger]      [Close]  │
└────────────────────────────────────────────────────────┘
```

#### Form Layout
```
┌──────────────────────────────┬─────────────────────────┐
│ Label (right-aligned)        │ Input Field             │
│ Another Label                │ Dropdown                │
│ Long Label                   │ Text Area               │
└──────────────────────────────┴─────────────────────────┘
```
- Label width: 120-150px
- Label alignment: Right
- Input width: Flexible, min 200px

---

## 5. Table Standards

### All tables across all modules follow these rules:

#### Table Dimensions
- **Row Height**: 32px minimum
- **Header Height**: 36px
- **Cell Padding**: 8px vertical, 12px horizontal
- **Border**: 1px solid `#3a3a3a`

#### Table Styling
- **Background**: `#1e1e1e`
- **Alternate Rows**: `#242424` (optional, for dense tables)
- **Grid Lines**: `#3a3a3a`
- **Selection**: `#007acc` background, `#ffffff` text
- **Hover**: `#2d2d2d` background

#### Table Headers
- **Background**: `#2b2b2b`
- **Text**: `#cfcfcf`, UPPERCASE, bold
- **Border-bottom**: 2px solid `#007acc`
- **Sortable**: Show arrow icon on hover
- **Padding**: 10px vertical, 12px horizontal

#### Column Alignment Rules
- **Text/Names**: Left-aligned
- **Dates**: Center-aligned
- **Numbers/Qty**: Right-aligned
- **Money**: Right-aligned, show $ symbol
- **Status**: Center-aligned
- **Actions**: Center-aligned

#### Special Column Styling
- **Patient Name**: Always bold, `#e5e5e5`
- **HCPCS Code**: Monospace font (Consolas), uppercase
- **Order ID**: Monospace, clickable link style
- **Phone**: Format as (XXX) XXX-XXXX
- **Money**: Right-align, 2 decimals, green if positive
- **Dates**: Format as YYYY-MM-DD or MM/DD/YYYY

---

## 6. Button Standards

### Button Types

#### Primary Button
- **Use**: Main action (Save, Submit, Create)
- **Background**: `#007acc`
- **Hover**: `#279bff`
- **Text**: `#ffffff`, medium weight
- **Min Width**: 80px

#### Success Button
- **Use**: Positive actions (Approve, Complete)
- **Background**: `#28a745`
- **Hover**: `#34ce57`
- **Text**: `#ffffff`

#### Danger Button
- **Use**: Destructive actions (Delete, Cancel Order)
- **Background**: `#dc3545`
- **Hover**: `#e4606d`
- **Text**: `#ffffff`

#### Secondary Button
- **Use**: Less important actions (Close, Back)
- **Background**: `#2b2b2b`
- **Border**: 1px solid `#555555`
- **Hover**: `#3a3a3a`, border `#007acc`
- **Text**: `#e5e5e5`

### Button Sizing
- **Default**: 32px height, 10px/16px padding
- **Small**: 28px height, 8px/12px padding
- **Large**: 40px height, 12px/20px padding

### Button States
- **Default**: Normal appearance
- **Hover**: Lighter background
- **Pressed**: Darker background
- **Disabled**: `#3a3a3a` background, `#888888` text
- **Loading**: Show spinner, text "Loading..."

---

## 7. Form Standards

### Input Fields
- **Height**: 32px minimum
- **Padding**: 8px (v) × 12px (h)
- **Background**: `#2b2b2b`
- **Border**: 1px solid `#3a3a3a`
- **Focus Border**: 1px solid `#007acc`
- **Border Radius**: 4px

### Dropdowns / ComboBoxes
- Same styling as input fields
- Down arrow: 32px width on right
- Dropdown menu: `#2b2b2b` background, `#007acc` selection

### Date Pickers
- Same styling as input fields
- Calendar icon on right
- Calendar popup: Dark themed

### Checkboxes & Radio Buttons
- **Size**: 18px × 18px
- **Border**: 2px solid `#555555`
- **Checked**: `#007acc` background
- **Border Radius**: 3px (checkbox), 9px (radio)

### Text Areas
- Same styling as input fields
- Min height: 80px
- Vertical scrollbar if needed

---

## 8. Status Indicators

### Status Badges
Small pill-shaped indicators for order/item status.

#### Active / Approved
- **Background**: `rgba(40, 167, 69, 0.2)`
- **Border**: 1px solid `#28a745`
- **Text**: `#28a745`, uppercase, bold

#### Pending / In Progress
- **Background**: `rgba(255, 193, 7, 0.2)`
- **Border**: 1px solid `#ffc107`
- **Text**: `#ffc107`, uppercase, bold

#### Completed
- **Background**: `rgba(0, 122, 204, 0.2)`
- **Border**: 1px solid `#007acc`
- **Text**: `#007acc`, uppercase, bold

#### Cancelled / Error
- **Background**: `rgba(220, 53, 69, 0.2)`
- **Border**: 1px solid `#dc3545`
- **Text**: `#dc3545`, uppercase, bold

#### Inactive / Disabled
- **Background**: `rgba(136, 136, 136, 0.2)`
- **Border**: 1px solid `#888888`
- **Text**: `#888888`, uppercase

### Status Badge Sizing
- **Padding**: 4px (v) × 12px (h)
- **Font**: 8pt, semibold, uppercase
- **Border Radius**: 12px (full pill shape)

---

## 9. Icons

### Icon Set
Use **Feather Icons** or **Material Icons** for consistency.

### Icon Sizing
- **Small**: 16px (in-line with text)
- **Medium**: 20px (buttons, toolbar)
- **Large**: 24px (page headers)

### Icon Colors
- **Default**: `#e5e5e5`
- **Hover**: `#007acc`
- **Disabled**: `#888888`
- **Success**: `#28a745`
- **Error**: `#dc3545`

### Common Icons
- **Search**: Magnifying glass
- **Add/Create**: Plus circle
- **Edit**: Pencil
- **Delete**: Trash can
- **Save**: Check circle
- **Cancel**: X circle
- **Settings**: Gear
- **Calendar**: Calendar icon
- **User**: User icon
- **Orders**: Shopping cart
- **Inventory**: Package
- **Reports**: Bar chart

---

## 10. Module-Specific Standards

### Patient Management
- **Patient Name**: Always bold in tables
- **DOB**: Format as MM/DD/YYYY
- **Phone**: Format as (XXX) XXX-XXXX
- **Insurance**: Show primary in bold, secondary in normal

### Order Management
- **Order ID**: Monospace, clickable
- **Status**: Use status badge
- **Date**: Format as YYYY-MM-DD
- **Total**: Right-aligned, currency format

### Refill Tracking
- **Next Due Date**: Highlight if ≤ 7 days (yellow), overdue (red)
- **Days Until Due**: Color-coded: red (≤0), yellow (≤7), normal (>7)
- **Refills Remaining**: Right-aligned number

### Inventory
- **HCPCS Code**: Uppercase, monospace
- **Quantity**: Right-aligned
- **Price**: Right-aligned, currency format
- **Stock Level**: Color-coded: red (low), yellow (medium), green (good)

### Billing
- **Amount**: Right-aligned, currency, 2 decimals
- **Balance**: Green if paid, red if overdue
- **Claim Status**: Use status badge

---

## 11. Responsive Behavior

### Window Resize
- **Min Width**: 1024px
- **Min Height**: 768px
- **Preferred**: 1366px × 768px or larger

### Table Behavior
- **Horizontal Scroll**: If table width > window width
- **Column Resize**: User can resize columns
- **Column Priority**: Hide less important columns first on narrow screens

---

## 12. Accessibility

### Color Contrast
- All text must have 4.5:1 contrast ratio minimum
- Primary buttons: 4.8:1 contrast
- Links: Underline on hover

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order: Top to bottom, left to right
- Enter to submit forms
- Escape to close dialogs
- Arrow keys to navigate tables

### Screen Reader Support
- All buttons have aria-labels
- All form inputs have labels
- Table headers properly marked
- Status changes announced

---

## 13. Animation & Transitions

### Hover Transitions
- Duration: 150ms
- Easing: ease-in-out

### Button Press
- Duration: 100ms
- Scale: 0.98 (slight press effect)

### Dialog/Modal Appearance
- Duration: 200ms
- Fade in with slight scale (0.95 → 1.0)

### Avoid
- No auto-playing animations
- No unnecessary motion
- Respect user's motion preferences

---

## 14. Error Handling & Messages

### Error Messages
- **Color**: `#dc3545`
- **Icon**: X circle
- **Position**: Above form or in dialog
- **Dismissible**: Show X button

### Success Messages
- **Color**: `#28a745`
- **Icon**: Check circle
- **Duration**: Auto-dismiss after 3 seconds

### Warning Messages
- **Color**: `#ffc107`
- **Icon**: Alert triangle
- **Requires**: User acknowledgment

### Info Messages
- **Color**: `#007acc`
- **Icon**: Info circle

---

## 15. Implementation Checklist

When creating a new screen or updating an existing one:

- [ ] Apply `dark.qss` theme via `apply_theme(app, "dark")`
- [ ] Use `ThemeColors` constants for custom styling
- [ ] Follow spacing system (multiples of 4px)
- [ ] Set proper table row height (32px)
- [ ] Bold patient names in tables
- [ ] Uppercase table headers
- [ ] Right-align numeric columns
- [ ] Use status badges for status fields
- [ ] Format dates consistently (YYYY-MM-DD)
- [ ] Format phone numbers ((XXX) XXX-XXXX)
- [ ] Format currency ($X,XXX.XX)
- [ ] Add hover states to interactive elements
- [ ] Ensure keyboard navigation works
- [ ] Test with minimum window size (1024×768)
- [ ] Verify color contrast ratios
- [ ] Add proper tooltips
- [ ] Handle loading/disabled states

---

## 16. Code Examples

### Apply Theme to Application
```python
from theme_manager import apply_theme

app = QApplication(sys.argv)
apply_theme(app, "dark")
```

### Create Status Badge
```python
status_label = QLabel("PENDING")
status_label.setProperty("class", "status-badge")
status_label.setProperty("status", "pending")
```

### Style a Primary Button
```python
btn = QPushButton("Create Order")
# Theme automatically applies primary styling
```

### Style a Success Button
```python
btn_save = QPushButton("Save")
btn_save.setProperty("class", "success")
```

### Style a Table Programmatically
```python
from theme_manager import ThemeSpacing

table.verticalHeader().setDefaultSectionSize(ThemeSpacing.TABLE_ROW_HEIGHT)
table.horizontalHeader().setDefaultSectionSize(ThemeSpacing.TABLE_CELL_PADDING * 10)
```

---

## Conclusion

Following this design system ensures that DME Logic presents a unified, professional,
enterprise-grade appearance that builds user confidence and matches the quality of
commercial DME systems like Brightree and Kareo.

**Consistency = Professionalism = User Trust**
