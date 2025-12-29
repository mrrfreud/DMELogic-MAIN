# Order Fetching Integration - Complete

## Summary

✅ **Complete domain model integration for order fetching and export**

All components are in place for clean, typed order data access:

1. **Repository function**: `fetch_order_with_items()`
2. **Domain models**: Rich `Order` and `OrderItem` types
3. **Service layer**: High-level export functions
4. **View models**: State Portal transformation

## Architecture

### 1. Repository Layer (`dmelogic/db/orders.py`)

```python
def fetch_order_with_items(
    order_id: int,
    folder_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Order]:
    """
    Load a full Order aggregate (header + items) as a domain model.
    
    - Single source of truth for order data
    - Returns typed Order with items list populated
    - Handles connection management
    - Uses converters for clean row → model mapping
    """
```

**Usage:**
```python
from dmelogic.db import fetch_order_with_items

order = fetch_order_with_items(order_id=123, folder_path=data_path)
if order:
    print(f"Patient: {order.patient_full_name}")
    print(f"Status: {order.order_status.value}")
    print(f"Items: {len(order.items)}")
```

### 2. Domain Models (`dmelogic/db/models.py`)

**Order Model:**
```python
@dataclass
class Order:
    id: int
    
    # Foreign keys
    patient_id: Optional[int]
    prescriber_id: Optional[int]
    
    # Snapshot fields (audit trail)
    patient_name_at_order_time: Optional[str]
    patient_dob_at_order_time: Optional[date]
    prescriber_name_at_order_time: Optional[str]
    prescriber_npi_at_order_time: Optional[str]
    
    # Status and workflow
    order_status: OrderStatus  # Enum!
    billing_type: BillingType  # Enum!
    
    # Items
    items: list[OrderItem]
    
    # Computed properties
    @property
    def patient_full_name(self) -> str: ...
    
    @property
    def icd_codes(self) -> list[str]: ...
```

**OrderItem Model:**
```python
@dataclass
class OrderItem:
    id: int
    order_id: int
    
    hcpcs_code: str
    description: str
    quantity: int
    refills: int
    days_supply: int
    
    cost_ea: Optional[Decimal]
    total_cost: Optional[Decimal]
```

### 3. Service Layer (`dmelogic/db/order_workflow.py`)

High-level functions that coordinate repository + view models:

```python
def build_state_portal_json_for_order(
    order_id: int,
    folder_path: Optional[str] = None,
) -> dict:
    """
    Load order + transform to State Portal JSON format.
    
    Returns:
        Dict ready for POST to state portal API
    """
    order = fetch_order_with_items(order_id, folder_path)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    
    view = StatePortalOrderView.from_order(order, folder_path)
    return view.to_portal_json()
```

```python
def build_state_portal_csv_row_for_order(
    order_id: int,
    folder_path: Optional[str] = None,
) -> List[str]:
    """
    Load order + transform to State Portal CSV row.
    
    Returns:
        List of string values for CSV export
    """
```

### 4. View Models (`dmelogic/db/state_portal_view.py`)

Transforms domain models to external formats:

```python
class StatePortalOrderView:
    @classmethod
    def from_order(cls, order: Order, folder_path: Optional[str] = None):
        """Create view from domain Order model."""
        
    def to_portal_json(self) -> dict:
        """Transform to JSON for API submission."""
        
    def to_csv_row(self) -> List[str]:
        """Transform to CSV row for bulk upload."""
```

## Benefits

### ✅ Single Source of Truth
- **Before**: SQL scattered across UI, dialogs, reports
- **After**: One function `fetch_order_with_items()` for all order access

### ✅ Type Safety
```python
order = fetch_order_with_items(123, folder_path)
# IDE autocomplete works!
order.patient_full_name  # ✓ Known field
order.order_status.value  # ✓ Enum
order.items[0].quantity  # ✓ Int
```

### ✅ Clean Separation
```
UI Layer          → Service Layer → Repository → Database
(buttons, tables)   (business ops)  (data access) (SQL)
```

### ✅ Testable
Each layer can be tested independently:
- Repository: Test data hydration
- Domain models: Test business logic
- Service layer: Test coordination
- View models: Test transformations

### ✅ Extensible
Adding HCFA-1500 form generation follows the same pattern:

```python
# Future implementation
def build_1500_for_order(order_id: int, folder_path: Optional[str] = None):
    order = fetch_order_with_items(order_id, folder_path)
    return Hcfa1500ClaimView.from_order(order)
```

## Usage Examples

### Example 1: Display Order in UI
```python
from dmelogic.db import fetch_order_with_items

def load_order_details(self, order_id: int):
    order = fetch_order_with_items(order_id, self.current_folder)
    if not order:
        return
    
    # Rich domain model with typed fields
    self.patient_label.setText(order.patient_full_name)
    self.status_combo.setCurrentText(order.order_status.value)
    
    # Items are fully hydrated
    for item in order.items:
        row = [
            item.hcpcs_code,
            item.description,
            str(item.quantity),
            f"${item.cost_ea or 0}",
        ]
        self.items_table.addRow(row)
```

### Example 2: Export to State Portal
```python
from dmelogic.db import build_state_portal_json_for_order

def export_to_state_portal(self, order_id: int):
    try:
        json_data = build_state_portal_json_for_order(
            order_id, 
            folder_path=self.current_folder
        )
        
        # Post to API
        response = requests.post(
            PORTAL_API_URL,
            json=json_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        
        self.show_success("Order submitted to state portal")
        
    except ValueError as e:
        self.show_error(str(e))
```

### Example 3: Batch CSV Export
```python
from dmelogic.db import build_state_portal_csv_row_for_order
import csv

def export_orders_to_csv(self, order_ids: List[int], output_path: str):
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header (from StatePortalOrderView.CSV_HEADERS)
        writer.writerow(StatePortalOrderView.CSV_HEADERS)
        
        for order_id in order_ids:
            try:
                row = build_state_portal_csv_row_for_order(
                    order_id,
                    folder_path=self.current_folder
                )
                writer.writerow(row)
            except ValueError as e:
                print(f"Skipping order {order_id}: {e}")
```

## Migration Path

### Phase 1: Replace Direct SQL in UI ✅ READY
Anywhere you currently do:
```python
# OLD WAY
cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
order_row = cur.fetchone()
cur.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
item_rows = cur.fetchall()
```

Replace with:
```python
# NEW WAY
from dmelogic.db import fetch_order_with_items

order = fetch_order_with_items(order_id, folder_path=self.current_folder)
# order.items is already populated!
```

### Phase 2: Wire Export Buttons ✅ READY
State Portal export buttons should call:
```python
from dmelogic.db import (
    build_state_portal_json_for_order,
    build_state_portal_csv_row_for_order,
)
```

### Phase 3: Add HCFA-1500 Generation (Next)
Follow same pattern:
1. Create `Hcfa1500ClaimView` class
2. Add `from_order()` class method
3. Create service function `build_1500_for_order()`
4. Wire to UI export button

## Testing

### Run the Demo
```powershell
python demo_domain_integration.py
```

Shows:
1. Domain model fetching with rich types
2. State Portal JSON export
3. State Portal CSV export
4. Architecture overview

### Verify Integration
```python
from dmelogic.db import fetch_order_with_items

# Test basic fetch
order = fetch_order_with_items(1, r"C:\FaxManagerData\Data")
print(f"Patient: {order.patient_full_name}")
print(f"Status: {order.order_status.value}")
print(f"Items: {len(order.items)}")
print(f"ICD Codes: {order.icd_codes}")
```

## Files Modified

### Core Implementation
- ✅ `dmelogic/db/orders.py` - Added `fetch_order_with_items()`
- ✅ `dmelogic/db/converters.py` - Row converters for Order/OrderItem
- ✅ `dmelogic/db/models.py` - Domain models
- ✅ `dmelogic/db/order_workflow.py` - Service layer functions
- ✅ `dmelogic/db/state_portal_view.py` - View model transformations
- ✅ `dmelogic/db/__init__.py` - Public API exports

### Documentation & Demos
- ✅ `demo_domain_integration.py` - Complete integration demo
- ✅ `FETCH_ORDER_INTEGRATION.md` - This file

## Public API

All components are exported via `dmelogic.db`:

```python
from dmelogic.db import (
    # Repository
    fetch_order_with_items,
    
    # Domain models
    Order,
    OrderItem,
    OrderStatus,
    BillingType,
    
    # Service layer
    build_state_portal_json_for_order,
    build_state_portal_csv_row_for_order,
    
    # Converters (if needed)
    row_to_order,
    row_to_order_item,
)
```

## Next Steps

1. **Replace SQL in UI code**
   - Find all `SELECT * FROM orders WHERE id = ?`
   - Replace with `fetch_order_with_items()`

2. **Wire State Portal buttons**
   - "Export to JSON" → `build_state_portal_json_for_order()`
   - "Export to CSV" → `build_state_portal_csv_row_for_order()`

3. **Add HCFA-1500 generation**
   - Create `dmelogic/forms/hcfa1500.py`
   - Add `Hcfa1500ClaimView` class
   - Follow same view model pattern

4. **Add unit tests**
   - Test converters
   - Test repository functions
   - Test service layer
   - Test view transformations

## Summary

✅ **Repository function**: `fetch_order_with_items()` - single source of truth  
✅ **Domain models**: Rich, typed `Order` and `OrderItem`  
✅ **Service layer**: High-level business operations  
✅ **View models**: Clean domain → external format transformations  
✅ **Public API**: All exports via `dmelogic.db`  
✅ **Demo script**: `demo_domain_integration.py` shows it all working  

**The foundation is complete. Now just wire UI buttons to use these clean APIs instead of raw SQL!**
