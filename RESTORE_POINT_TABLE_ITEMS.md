# Restore Point: Table-Based Items Page

**Date:** December 7, 2025  
**Status:** Working - Commercial table-based items implementation

## Current Implementation

### Order Wizard Items Page
- **File:** `dmelogic/ui/order_wizard.py`
- **Architecture:** Table-based layout (QTableWidget)
- **Columns:** 6 columns - HCPCS/Item, Description, Qty, Refills, Days, Directions

### Key Features
1. **Table Layout:**
   - Clean, professional data grid with alternating row colors
   - Fixed column widths: HCPCS (150px), Description (260px), Qty/Refills/Days (70px each), Directions (260px)
   - Minimum table height: 160px for proper visual balance
   - Row height: 28px for comfortable spacing

2. **Spinbox Controls:**
   - Fully visible with 60px minimum width
   - Qty: 0-999 range, shows blank at 0
   - Refills: 0-99 range, shows blank at 0
   - Days: 1-365 range, default 30

3. **Layout & Styling:**
   - 30px horizontal margins, 20px vertical padding
   - Bold headers with #f5f5f5 background
   - Gridlines: #d0d7de color
   - Font size: 10pt

4. **Integration Points:**
   - `add_item_row()`: Adds new table rows with spinbox widgets
   - `remove_selected_items()`: Removes selected rows
   - `search_inventory_item()`: Populates rows from inventory search
   - `_collect_items()`: Extracts data from table for order creation
   - `_validate_items()`: Validates table rows before submission

### Data Flow
```
Table Row → QTableWidgetItem (HCPCS, Description, Directions)
         → QSpinBox widgets (Qty, Refills, Days)
         → _collect_items() → List[OrderItem]
         → OrderWizardResult
```

### Insurance Integration
- Patient insurance loaded from `PatientInsurance` dataclass
- Insurance combo populated in Step 4 (Review)
- Primary/Secondary insurance with policy numbers
- Address fields included for order creation

### Known Working State
- ✅ App launches without errors
- ✅ Items table displays properly with all columns
- ✅ Spinboxes fully visible and functional
- ✅ Add/Remove items working
- ✅ Inventory search integration functional
- ✅ Insurance loading from database
- ✅ Patient ID tracking through wizard
- ✅ Order creation with all fields

## Rental/Modifiers Status
**Note:** Previous per-item rental checkbox and modifier fields (Mod1-4) were removed in favor of clean table layout. If rental support is needed, it should be re-implemented as additional table columns or separate rental tracking.

## Files Modified
- `dmelogic/ui/order_wizard.py`: Lines 530-950 (items page implementation)
- `dmelogic/db/models.py`: PatientInsurance dataclass with address fields
- `dmelogic/db/patients.py`: fetch_patient_insurance() returns dataclass
- `dmelogic/ui/main_window.py`: Uses dataclass attributes for insurance
- `app_legacy.py`: Extracts patient_id from table UserRole

## Warnings (Non-Critical)
- FTS5 not available (search performance)
- Some OCR features unavailable (related to FTS5)

## To Restore This Point
1. Keep current `order_wizard.py` implementation
2. Maintain table-based `_build_items_page()` method
3. Preserve `add_item_row()`, `remove_selected_items()`, `search_inventory_item()`
4. Keep `_collect_items()` and `_validate_items()` table-reading logic
5. Retain PatientInsurance dataclass structure
