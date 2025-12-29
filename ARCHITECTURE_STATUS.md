# DMELogic Architecture Status
**Date**: December 6, 2025

## ✅ Completed: Domain Model Architecture

### Single Source of Truth
We have successfully established a clean domain model architecture with **Order** and **OrderItem** as the single source of truth for all order data.

**Domain Layer** (`dmelogic/db/`):
```
Order (dataclass)
├── Core Fields: id, order_date, order_status, billing_type
├── Snapshot Fields: patient_name_at_order_time, patient_dob_at_order_time, etc.
├── Foreign Keys: patient_id, prescriber_id, insurance_id
├── Clinical: icd_codes (list), doctor_directions
└── Items: list[OrderItem] with Decimal precision

Repository: fetch_order_with_items(order_id, folder_path) → Order | None
```

### ✅ Two View Layers Implemented

#### 1. State Portal Export (`dmelogic/db/state_portal_view.py`)
**Purpose**: Export orders to state Medicaid portal

**Architecture**:
```
Order → StatePortalOrderView → JSON/CSV
```

**Features**:
- ✅ Complete field mapping to portal format
- ✅ Date formatting (YYYY-MM-DD)
- ✅ JSON export with `to_portal_json()`
- ✅ CSV export with `to_csv_row()`
- ✅ UI button: "📤 Export to Portal"
- ✅ Handler: `export_order_to_state_portal()`

**Test Status**: Working ✅

#### 2. HCFA-1500 Claim Forms (`dmelogic/claims_1500.py` + `dmelogic/printing/`)
**Purpose**: Generate CMS-1500 insurance claim forms

**Architecture**:
```
Order → Hcfa1500Claim → PDF (ReportLab)
```

**Features**:
- ✅ Complete CMS-1500 data structure (all 33 boxes)
- ✅ Service line mapping (Box 24 A-J)
- ✅ ICD-10 diagnosis codes (Box 21)
- ✅ Coordinate-based PDF rendering
- ✅ Preprinted form support
- ✅ Optional background image mode
- ✅ UI buttons:
  - "📄 Generate 1500 JSON" (preview)
  - "🖨️ Print HCFA-1500" (PDF)
- ✅ Handlers:
  - `generate_1500_for_selected()` (JSON preview)
  - `print_1500_for_selected_order()` (PDF generation)

**Test Status**: Working ✅
- Test Order 1 (LOPEZ, ANA): 1,741 byte PDF generated successfully
- All fields mapped correctly
- PDF opens automatically in system viewer

### ✅ Clean Separation of Concerns

**NO SQL in View Layers**:
- ✅ StatePortalOrderView: Pure transformation, no queries
- ✅ Hcfa1500Claim: Pure transformation, no queries
- ✅ PDF Generator: Pure rendering, no queries

**All data flows through repository**:
```python
order = fetch_order_with_items(order_id, folder_path)  # Only SQL query
view = StatePortalOrderView.from_order(order)          # Pure transform
claim = hcfa1500_from_order(order)                     # Pure transform
pdf = render_hcfa1500_pdf(claim)                       # Pure render
```

### ✅ Snapshot Fields for Audit Trail

Order captures point-in-time data:
- `patient_name_at_order_time`
- `patient_dob_at_order_time`
- `patient_address_at_order_time`
- `prescriber_name_at_order_time`
- `prescriber_npi_at_order_time`
- `insurance_name_at_order_time`
- `insurance_id_at_order_time`

**Benefit**: Claims remain accurate even if patient/prescriber records change later.

### ✅ UI Integration Complete

**Orders Tab Buttons**:
1. ✅ New Order
2. ✅ Edit Order
3. ✅ Update Status
4. ✅ Delivery Report
5. ✅ Clear Delivery
6. ✅ Process Refill
7. ✅ **Export to Portal** (NEW - State Medicaid)
8. ✅ **Generate 1500 JSON** (NEW - Preview claim)
9. ✅ **Print HCFA-1500** (NEW - Generate PDF)
10. ✅ Delete Order
11. ✅ Link to Patient

**All buttons wired and tested** ✅

---

## 🎯 Next Steps: Two Major Paths

### Path A: Business Rules & Claims Intelligence 📋

**Focus**: Tighten medical billing rules and automation

#### 1. Per-Payer Rules Engine
```python
# dmelogic/billing/payer_rules.py
class PayerRules:
    """Per-payer business rules for HCPCS billing."""
    
    def validate_hcpcs(self, payer: str, hcpcs: str) -> ValidationResult
    def get_max_units(self, payer: str, hcpcs: str) -> int
    def get_frequency_limits(self, payer: str, hcpcs: str) -> FrequencyLimit
    def requires_prior_auth(self, payer: str, hcpcs: str) -> bool
```

**Examples**:
- Medicare: L0637 (lumbar orthosis) limited to 1 per 5 years
- Medicaid: A4495 (compression stockings) 4 pairs per 6 months
- Commercial: May allow more frequent replacements

#### 2. Rental vs Purchase Logic
```python
# dmelogic/billing/rental_purchase.py
class RentalPurchaseEngine:
    """Handle rental vs purchase billing logic."""
    
    def determine_billing_code(self, item: str, month: int) -> str:
        # NU = New purchase
        # RR = Rental
        # MS = 6-month maintenance
```

**Examples**:
- CPAP machines: Rental for 13 months, then purchase (capped rental)
- Hospital beds: Monthly rental with modifiers (KH, KI, KJ)
- Wheelchairs: Purchase vs rental based on payer and need

#### 3. Modifier Management
```python
# dmelogic/billing/modifiers.py
class ModifierEngine:
    """Auto-apply billing modifiers based on context."""
    
    MODIFIERS = {
        'LT': 'Left side',
        'RT': 'Right side',
        'KX': 'Requirements met',
        'KH': 'Initial rental month',
        'KI': 'Rental months 2-3',
        'KJ': 'Rental months 4+',
        'RR': 'Rental',
        'NU': 'New equipment',
    }
```

**Auto-apply logic**:
- Bilateral items (A4495): Require LT/RT modifiers
- Rentals: Auto-add KH/KI/KJ based on rental month
- Prior auth: Auto-add KX when auth exists

#### 4. Multi-Diagnosis Pointers
```python
# Currently: Single diagnosis pointer per line (A, B, C, or D)
# Enhanced: Multiple pointers per line (AB, ABC, ABCD)

class ServiceLine:
    diagnosis_pointers: str  # "AB" for two diagnoses, "ABCD" for all
```

**Business logic**:
- Diabetic supplies → Link to both diabetes (E11.9) and neuropathy (E11.42)
- Wound care → Link to both wound (L89.xxx) and underlying condition

#### 5. Re-Supply Calendar
```python
# dmelogic/billing/resupply.py
class ResupplyCalendar:
    """Track when items are eligible for re-supply."""
    
    def get_next_eligible_date(self, hcpcs: str, last_fill: date) -> date
    def check_too_soon(self, hcpcs: str, last_fill: date) -> bool
    def get_remaining_days(self, hcpcs: str, last_fill: date) -> int
```

**Examples**:
- A4253 (blood glucose strips): 90-day supply, refill at day 75
- A4396 (lancets): 90-day supply
- A4495 (compression stockings): 180-day supply

#### 6. Claim Validation
```python
# dmelogic/billing/claim_validator.py
class ClaimValidator:
    """Validate claims before submission."""
    
    def validate_claim(self, claim: Hcfa1500Claim) -> List[ValidationError]:
        # Check required fields
        # Check date logic (DOS before today, not in future)
        # Check NPI format (10 digits)
        # Check ICD-10 format
        # Check HCPCS format
        # Check payer-specific rules
```

---

### Path B: UI Migration & Polish 🎨

**Focus**: Complete migration from `app_legacy.py` to clean `MainWindow`

#### 1. Systematic Method Migration
Currently: 30,660 lines in `app_legacy.py`
Goal: Extract into organized modules

```
app_legacy.py (30,660 lines)
    ↓ Extract
dmelogic/ui/
├── main_window.py (current: 792 lines)
├── order_wizard.py (multi-step order creation)
├── inventory_search_dialog.py
├── prescriber_search_dialog.py
└── dialogs/
    ├── order_status_dialog.py
    ├── delivery_report_dialog.py
    ├── refill_dialog.py
    └── patient_link_dialog.py
```

#### 2. Orders Tab Completion
- ✅ Button layout complete
- ✅ Export/Print working
- 🔄 Extract order editing logic
- 🔄 Extract status update logic
- 🔄 Extract delivery tracking logic
- 🔄 Extract refill processing logic

#### 3. Other Tabs Migration
```
TODO:
├── Patients Tab (search, add, edit)
├── Prescribers Tab (NPI lookup, add, edit)
├── Inventory Tab (search, add, edit, tracking)
├── Insurance Tab (add, edit, coverage rules)
├── Fax Manager Tab (OCR, indexing, viewing)
├── Reports Tab (revenue, payer mix, charts)
└── Settings Tab (configuration, backup, about)
```

#### 4. Dialog System Refactoring
Extract all dialog classes from app_legacy:
- OrderWizard (already extracted but could be enhanced)
- StatusUpdateDialog
- DeliveryReportDialog
- RefillDialog
- PatientLinkDialog
- InventorySearchDialog (already extracted)
- PrescriberSearchDialog (already extracted)

#### 5. Event Handler Organization
```python
# Pattern: Signal → Handler → Business Logic → UI Update

# Current: All mixed in app_legacy
# Goal: Clear separation

dmelogic/ui/handlers/
├── order_handlers.py
├── patient_handlers.py
├── inventory_handlers.py
└── report_handlers.py
```

#### 6. State Management
```python
# dmelogic/ui/state_manager.py
class AppState:
    """Centralized application state."""
    
    current_order_id: int | None
    selected_patient_id: int | None
    filter_status: OrderStatus | None
    folder_path: str
```

---

## 📊 Migration Progress

### Domain Model: **100%** ✅
- Order/OrderItem dataclasses
- Repository pattern
- Snapshot fields
- Type safety

### View Layers: **100%** ✅
- State Portal Export
- HCFA-1500 Claims
- PDF Generation

### UI Migration: **~15%** 🔄
- Orders tab buttons: ✅ Complete
- Dialog extraction: 🔄 Partial (3/10 dialogs)
- Tab migration: 🔄 1/7 tabs fully migrated
- Event handlers: 🔄 Minimal extraction

### Business Rules: **~20%** 🔄
- Order workflow: ✅ Complete
- Payer rules: ❌ Not started
- Modifiers: ❌ Not started
- Re-supply logic: ❌ Not started
- Claim validation: ❌ Not started

---

## 🤔 Decision Point: What Next?

### Option 1: Business Rules (Path A)
**Pros**:
- Immediate business value
- Reduces billing errors
- Automates complex logic
- Demonstrates domain expertise

**Time estimate**: 2-4 weeks for comprehensive rules engine

**Impact**: High - directly affects billing accuracy and compliance

### Option 2: UI Migration (Path B)
**Pros**:
- Cleaner codebase
- Easier maintenance
- Better separation of concerns
- Enables team development

**Time estimate**: 6-8 weeks for complete migration

**Impact**: Medium - mostly internal quality improvements

### Hybrid Approach
Start with **high-value business rules** while **gradually extracting UI**:

1. **Week 1-2**: Payer rules engine + Modifier automation
2. **Week 3-4**: Re-supply calendar + Claim validation
3. **Week 5-6**: Extract Patients tab + dialogs
4. **Week 7-8**: Extract Inventory tab + dialogs

---

## 📋 Immediate Recommendations

### If You Choose Path A (Business Rules):
Start here:
1. **Modifier automation** (quick win, immediate value)
2. **Per-payer HCPCS limits** (prevents denials)
3. **Claim validation** (catch errors before submission)
4. **Re-supply calendar** (reduces too-soon rejections)

### If You Choose Path B (UI Migration):
Start here:
1. **Extract Patients tab** (cleanest separation)
2. **Extract status update dialog** (simple, self-contained)
3. **Extract delivery tracking** (isolated feature)
4. **Extract refill wizard** (already partially done)

### What I Recommend:
**Modified Hybrid**: Start with **modifier automation** (1 day, high value) + **claim validation** (2 days, prevents errors), THEN begin **Patients tab extraction** (5 days, clear improvement).

This gives you:
- ✅ Immediate business value (better billing)
- ✅ Visible quality improvements (cleaner UI code)
- ✅ Momentum in both directions

---

## 🎯 Your Call

**What matters most to you right now?**

Type:
- **"business rules"** → I'll start with payer rules, modifiers, and validation
- **"ui migration"** → I'll start extracting Patients tab and dialogs
- **"hybrid"** → I'll do modifier automation + Patients tab extraction
- **"next"** → I'll pick what I think is best (probably hybrid)

**Current status**: Architecture is solid ✅, ready for either direction!
