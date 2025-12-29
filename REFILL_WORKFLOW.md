# Refill Workflow - DME Logic

## Overview

The Refill Workflow manages automatic reordering of DME supplies that require periodic refills (e.g., diabetic supplies, oxygen, CPAP supplies). The system:

1. **Tracks refills remaining** on each order item
2. **Calculates next refill due date** based on last fill + day supply
3. **Shows refills due** in a dedicated screen
4. **Creates new orders** automatically from refillable items
5. **Decrements refill counters** and updates tracking

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Refill Due Screen (UI)              │
│  - Shows items due for refill                        │
│  - User selects items                                │
│  - Clicks "Create Orders"                            │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│            refill_service.process_refills()          │
│  - Loops through selected items                      │
│  - Each in its own UnitOfWork                        │
│  - Calls repository functions                        │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│        Repository Functions (dmelogic/db/orders.py)  │
│  - fetch_order_item_with_header()                    │
│  - create_refill_order_from_source()                 │
│  - mark_refill_used()                                │
└────────────────────┬─────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────┐
│         Database (orders.db)                         │
│  - order_items table (refills, last_filled_date)    │
│  - orders table (new refill orders)                  │
│  - Indexes for performance                           │
└──────────────────────────────────────────────────────┘
```

---

## Database Schema

### order_items Table

Key columns for refill tracking:

```sql
CREATE TABLE order_items (
    rowid INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    hcpcs_code TEXT,
    description TEXT,
    qty INTEGER,
    day_supply INTEGER,          -- Days supply per fill
    refills INTEGER,              -- REMAINING refills (decremented)
    last_filled_date TEXT,        -- Last fill date 'YYYY-MM-DD'
    -- ... other columns ...
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

### Indexes for Performance

```sql
-- Optimized index for refill queries
CREATE INDEX idx_order_items_refill_tracking
ON order_items(last_filled_date, day_supply, refills)
WHERE last_filled_date IS NOT NULL
  AND last_filled_date != ''
  AND CAST(refills AS INTEGER) > 0;

-- Patient name sorting index
CREATE INDEX idx_orders_patient_name
ON orders(patient_last_name, patient_first_name);
```

**Performance Impact**:
- Without indexes: Full table scan on `order_items` (slow for large datasets)
- With indexes: Direct index lookup (fast even with 100K+ items)

---

## Business Rules

### 1. Refill Counter Semantics

**`refills` field = REMAINING refills, not total prescribed**

| Scenario | Initial Refills | After 1st Fill | After 2nd Fill | After 12th Fill |
|----------|-----------------|----------------|----------------|-----------------|
| 1 year supply (12 fills) | 11 | 10 | 9 | 0 (no more refills) |

**Example**:
```python
# Original prescription: 12 fills (1 initial + 11 refills)
item = OrderItem(
    hcpcs_code="A4253",
    description="Blood glucose test strips",
    quantity=100,
    day_supply=30,
    refills=11,  # 11 refills remaining (12 total fills)
    last_filled_date=date(2025, 1, 1),
)

# After processing first refill
item.refills = 10  # Decremented
item.last_filled_date = date(2025, 2, 1)  # Updated
```

### 2. Next Refill Due Calculation

**Formula**: `next_refill_due = last_filled_date + day_supply`

```sql
-- SQLite calculation
SELECT
    last_filled_date,
    day_supply,
    date(last_filled_date, printf('+%d days', day_supply)) AS next_refill_due
FROM order_items;
```

**Examples**:

| Last Filled | Day Supply | Next Due | Eligible After |
|-------------|------------|----------|----------------|
| 2025-01-01 | 30 | 2025-01-31 | 2025-01-31 |
| 2025-01-01 | 90 | 2025-04-01 | 2025-04-01 |
| 2025-01-15 | 7 | 2025-01-22 | 2025-01-22 |

### 3. Refill Eligibility Rules

An item is eligible for refill when **ALL** conditions are met:

1. ✅ `refills > 0` (has refills remaining)
2. ✅ `last_filled_date IS NOT NULL` (has been filled at least once)
3. ✅ `next_refill_due <= today` (due date has passed)
4. ✅ Item is part of an active order (not cancelled)

**SQL Query** (from `fetch_refills_due`):
```sql
WHERE
    oi.last_filled_date IS NOT NULL
    AND oi.last_filled_date != ''
    AND CAST(oi.refills AS INTEGER) > 0
    AND date(oi.last_filled_date, printf('+%d days', oi.day_supply)) BETWEEN ? AND ?
```

### 4. Insurance-Specific Rules

Different payers have different refill timing rules:

| Insurance Type | Refill Allowed At | Notes |
|----------------|-------------------|-------|
| **Medicare** | 75% through supply | E.g., day 23 of 30-day supply |
| **Medicaid** | 75% through supply | Same as Medicare |
| **Commercial** | 80% through supply | More lenient |
| **Private Pay** | Anytime | No restrictions |

**Implementation** (in `InsurancePolicy` domain model):
```python
def get_refill_earliest_date(self, last_filled: date, day_supply: int) -> date:
    """Calculate earliest refill date based on payer rules."""
    if self.is_government:  # Medicare/Medicaid
        days_until_refill = int(day_supply * 0.75)
    else:  # Commercial
        days_until_refill = int(day_supply * 0.80)
    
    return last_filled + timedelta(days=days_until_refill)
```

---

## Workflow Steps

### Step 1: Query Refills Due

**UI**: User opens "Refills Due" screen and selects date range

**Backend**: `dmelogic.db.refills.fetch_refills_due()`

```python
from dmelogic.db.refills import fetch_refills_due

refills = fetch_refills_due(
    start_date="2025-12-01",
    end_date="2025-12-31",
    today="2025-12-05",
    folder_path=folder_path,
)

for refill in refills:
    print(f"{refill['patient_name']}: {refill['hcpcs_code']}")
    print(f"  Next due: {refill['next_refill_due']}")
    print(f"  Days until: {refill['days_until_due']}")
    print(f"  Refills remaining: {refill['refills_remaining']}")
```

**Returns** `RefillRow` TypedDict:
```python
class RefillRow(TypedDict):
    order_item_id: int          # rowid in order_items
    order_id: int               # original order ID
    patient_name: str           # For display
    patient_dob: str
    patient_phone: str
    hcpcs_code: str
    description: str
    refills_remaining: int      # How many refills left
    day_supply: int
    last_filled_date: str       # 'YYYY-MM-DD'
    next_refill_due: str        # Calculated date
    days_until_due: int         # Negative = overdue
    prescriber_name: str
```

### Step 2: Display in Grid

**UI**: Populate QTableWidget with refills

```python
def populate_refills_table(self, refills: List[RefillRow]):
    """Display refills in table with color coding."""
    self.table.setRowCount(len(refills))
    
    for row_idx, refill in enumerate(refills):
        # Patient name
        self.table.setItem(row_idx, 0, QTableWidgetItem(refill['patient_name']))
        
        # HCPCS code
        self.table.setItem(row_idx, 1, QTableWidgetItem(refill['hcpcs_code']))
        
        # Next due date
        due_date_item = QTableWidgetItem(refill['next_refill_due'])
        
        # Color code by urgency
        days_until = refill['days_until_due']
        if days_until < 0:
            # Overdue - red
            due_date_item.setBackground(QColor(255, 200, 200))
        elif days_until <= 7:
            # Due soon - yellow
            due_date_item.setBackground(QColor(255, 255, 200))
        
        self.table.setItem(row_idx, 2, due_date_item)
        
        # Refills remaining
        self.table.setItem(row_idx, 3, QTableWidgetItem(str(refill['refills_remaining'])))
```

### Step 3: User Selection

**UI**: User selects rows and clicks "Create Refill Orders"

```python
def on_create_refills_clicked(self):
    """Process selected refills."""
    selected_rows = self.table.selectionModel().selectedRows()
    if not selected_rows:
        QMessageBox.warning(self, "No Selection", "Please select refills to process")
        return
    
    # Get order_item_ids from selected rows
    item_ids = []
    for row in selected_rows:
        refill = self.refills_data[row.row()]
        item_ids.append(refill['order_item_id'])
    
    # Confirm action
    msg = f"Create refill orders for {len(item_ids)} items?"
    reply = QMessageBox.question(self, "Confirm", msg)
    if reply != QMessageBox.StandardButton.Yes:
        return
    
    # Process via service
    self.process_selected_refills(item_ids)
```

### Step 4: Process Refills (Service Layer)

**Service**: `refill_service.process_refills()`

```python
from dmelogic.services.refill_service import process_refills

def process_selected_refills(self, item_ids: List[int]):
    """Process refills using service layer."""
    try:
        # Get fill date (default today)
        fill_date = date.today().strftime("%Y-%m-%d")
        
        # Process refills
        folder_path = getattr(self, "current_folder", None)
        success_count = process_refills(
            selected_item_ids=item_ids,
            refill_fill_date=fill_date,
            folder_path=folder_path,
        )
        
        # Show result
        QMessageBox.information(
            self,
            "Success",
            f"Created {success_count} refill orders out of {len(item_ids)} selected"
        )
        
        # Refresh table
        self.refresh_refills_table()
        
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to process refills: {e}")
        debug_log(f"Refill processing error: {e}")
```

### Step 5: Service Processes Each Refill

**Service Implementation**:

```python
def process_refills(
    selected_item_ids: Iterable[int],
    refill_fill_date: Optional[str] = None,
    folder_path: Optional[str] = None,
) -> int:
    """Process refills with individual UoW for isolation."""
    if refill_fill_date is None:
        refill_fill_date = date.today().strftime("%Y-%m-%d")
    
    processed_count = 0
    
    # Each refill in its own transaction
    for item_id in selected_item_ids:
        try:
            with UnitOfWork(folder_path=folder_path) as uow:
                orders_conn = uow.connection("orders.db")
                
                # 1. Fetch source item + order details
                src = fetch_order_item_with_header(
                    order_item_rowid=item_id,
                    conn=orders_conn,
                )
                
                if not src:
                    debug_log(f"Refill skipped: item {item_id} not found")
                    continue
                
                # 2. Create new order from source
                new_order_id = create_refill_order_from_source(
                    src,
                    fill_date=refill_fill_date,
                    conn=orders_conn,
                )
                
                # 3. Decrement refills and update last_filled_date
                mark_refill_used(
                    order_item_rowid=item_id,
                    new_last_filled_date=refill_fill_date,
                    conn=orders_conn,
                )
                
                processed_count += 1
                debug_log(f"Refill: item {item_id} -> order {new_order_id}")
                
        except Exception as e:
            # Log and continue with next item
            debug_log(f"Refill failed for item {item_id}: {e}")
            continue
    
    return processed_count
```

**Key Pattern**: Each refill in its own UnitOfWork
- ✅ If one fails, others still process
- ✅ Each is atomic (all or nothing)
- ✅ Prevents partial state

### Step 6: Repository Operations

**1. Fetch Source Data**:
```python
def fetch_order_item_with_header(
    order_item_rowid: int,
    conn: Optional[sqlite3.Connection] = None,
    folder_path: Optional[str] = None,
) -> Optional[dict]:
    """Load order item with its parent order details."""
    # Returns dict with all fields needed for refill
```

**2. Create New Order**:
```python
def create_refill_order_from_source(
    source: dict,
    fill_date: str,
    conn: Optional[sqlite3.Connection] = None,
    folder_path: Optional[str] = None,
) -> int:
    """Create new order copying patient, prescriber, insurance from source."""
    # INSERT INTO orders (...) VALUES (...)
    # INSERT INTO order_items (...) VALUES (...)
    # Returns new order_id
```

**3. Update Source Item**:
```python
def mark_refill_used(
    order_item_rowid: int,
    new_last_filled_date: str,
    conn: Optional[sqlite3.Connection] = None,
    folder_path: Optional[str] = None,
) -> None:
    """Decrement refills and update last_filled_date."""
    UPDATE order_items
    SET refills = CAST(refills AS INTEGER) - 1,
        last_filled_date = ?
    WHERE rowid = ?
```

---

## Data Flow Example

### Initial State

```
Order #123 - Smith, John - Medicare Part B
├─ Item #1: A4253 - Blood Glucose Strips
│  ├─ Quantity: 100
│  ├─ Day Supply: 30
│  ├─ Refills: 11 (remaining)
│  └─ Last Filled: 2025-01-01
```

**Next Refill Due**: 2025-01-31 (30 days after last fill)

### After Processing Refill on 2025-02-01

**New Order Created** (Order #456):
```
Order #456 - Smith, John - Medicare Part B
└─ Item #1: A4253 - Blood Glucose Strips
   ├─ Quantity: 100
   ├─ Day Supply: 30
   ├─ Refills: 10 (one less than source)
   └─ Last Filled: 2025-02-01
```

**Source Order Updated** (Order #123):
```
Order #123 - Smith, John - Medicare Part B
└─ Item #1: A4253 - Blood Glucose Strips
   ├─ Quantity: 100
   ├─ Day Supply: 30
   ├─ Refills: 10 (decremented from 11)
   └─ Last Filled: 2025-02-01 (updated)
```

**Next Refill Due**: 2025-03-03 (30 days after new fill)

---

## Performance Optimization

### 1. Database Indexes

```sql
-- Refill tracking index (partial index)
CREATE INDEX idx_order_items_refill_tracking
ON order_items(last_filled_date, day_supply, refills)
WHERE last_filled_date IS NOT NULL
  AND refills > 0;

-- Patient sorting index
CREATE INDEX idx_orders_patient_name
ON orders(patient_last_name, patient_first_name);
```

**Benefits**:
- Fast refill queries (< 50ms even with 100K items)
- Efficient patient name sorting
- Partial index only includes refillable items

### 2. Query Optimization

```sql
-- Efficient query using indexes
SELECT
    oi.rowid,
    date(oi.last_filled_date, '+' || oi.day_supply || ' days') AS next_due
FROM order_items oi
USE INDEX (idx_order_items_refill_tracking)  -- Hint to use index
WHERE oi.last_filled_date IS NOT NULL
  AND oi.refills > 0
  AND next_due BETWEEN ? AND ?;
```

### 3. Batch Processing

```python
# ❌ Bad: One transaction for all refills
with UnitOfWork() as uow:
    for item_id in item_ids:
        process_refill(item_id, conn=uow.connection())
    # If any fails, all roll back!

# ✅ Good: One transaction per refill
for item_id in item_ids:
    try:
        with UnitOfWork() as uow:
            process_refill(item_id, conn=uow.connection())
    except Exception:
        continue  # Others still process
```

---

## Error Handling

### Service Layer

```python
def process_refills(...) -> int:
    """Returns count of successful refills."""
    processed_count = 0
    
    for item_id in selected_item_ids:
        try:
            with UnitOfWork() as uow:
                # ... process refill ...
                processed_count += 1
        except ValueError as e:
            # Business rule violation
            debug_log(f"Refill {item_id} validation failed: {e}")
            continue
        except sqlite3.IntegrityError as e:
            # Database constraint violation
            debug_log(f"Refill {item_id} DB error: {e}")
            continue
        except Exception as e:
            # Unexpected error
            debug_log(f"Refill {item_id} unexpected error: {e}")
            continue
    
    return processed_count
```

### UI Layer

```python
def process_selected_refills(self, item_ids: List[int]):
    """Process refills with user feedback."""
    try:
        success_count = process_refills(item_ids, ...)
        
        if success_count == len(item_ids):
            QMessageBox.information(
                self, "Success",
                f"All {success_count} refills processed successfully"
            )
        elif success_count > 0:
            QMessageBox.warning(
                self, "Partial Success",
                f"Processed {success_count} of {len(item_ids)} refills.\n"
                f"Check logs for errors on failed items."
            )
        else:
            QMessageBox.critical(
                self, "Failed",
                "No refills were processed. Check logs for details."
            )
        
        self.refresh_refills_table()
        
    except Exception as e:
        QMessageBox.critical(
            self, "Error",
            f"Refill processing failed: {e}"
        )
```

---

## Testing

### Unit Tests for Refill Queries

```python
import unittest
from datetime import date, timedelta
from dmelogic.db.refills import fetch_refills_due

class TestRefillQueries(unittest.TestCase):
    def test_refill_due_calculation(self):
        """Test that next_refill_due is calculated correctly."""
        # Setup test data
        last_filled = "2025-01-01"
        day_supply = 30
        
        # Query refills due between Jan 31 - Feb 10
        refills = fetch_refills_due(
            start_date="2025-01-31",
            end_date="2025-02-10",
            today="2025-01-25",
        )
        
        # Should include items with next_due = 2025-01-31
        self.assertTrue(any(r['next_refill_due'] == "2025-01-31" for r in refills))
    
    def test_only_items_with_refills_remaining(self):
        """Test that items with refills=0 are excluded."""
        refills = fetch_refills_due("2025-01-01", "2025-12-31", "2025-06-01")
        
        # All returned items should have refills > 0
        self.assertTrue(all(r['refills_remaining'] > 0 for r in refills))
```

### Integration Tests for Refill Processing

```python
class TestRefillProcessing(unittest.TestCase):
    def test_process_refill_decrements_counter(self):
        """Test that processing refill decrements remaining refills."""
        # Create test order with refillable item
        order_id = create_test_order(refills=3, last_filled="2025-01-01")
        item_id = get_item_id(order_id)
        
        # Process refill
        success_count = process_refills([item_id], refill_fill_date="2025-02-01")
        self.assertEqual(success_count, 1)
        
        # Verify source item updated
        item = fetch_order_item(item_id)
        self.assertEqual(item['refills'], 2)  # Decremented from 3
        self.assertEqual(item['last_filled_date'], "2025-02-01")
        
        # Verify new order created
        new_orders = fetch_orders_by_patient(...)
        self.assertEqual(len(new_orders), 2)  # Original + refill
```

---

## Best Practices

### ✅ DO

- Use `fetch_refills_due()` to query eligible refills
- Process refills through `refill_service.process_refills()`
- Use individual UoW per refill for isolation
- Update both new order and source item atomically
- Show user feedback on success/failure counts
- Color-code refills by urgency (overdue, due soon, future)
- Run migrations to ensure indexes exist

### ❌ DON'T

- Query refills with direct SQL in UI
- Process refills without UnitOfWork
- Forget to decrement source item refills
- Forget to update last_filled_date
- Use single transaction for all refills (prevents partial success)
- Treat refills as "total prescribed" instead of "remaining"
- Skip index creation (performance suffers)

---

## Future Enhancements

1. **Automatic Refill Processing**
   - Background job to process refills automatically
   - Email/SMS notifications to patients
   - Auto-submit to insurance

2. **Inventory Integration**
   - Reserve inventory when refill is due
   - Alert if stock insufficient
   - Auto-order from supplier

3. **Insurance Eligibility Checks**
   - Verify coverage before processing
   - Check refill timing rules
   - Validate prior authorizations

4. **Patient Portal**
   - Patients request refills online
   - View refill history
   - Track delivery status

5. **Analytics Dashboard**
   - Refills due this week/month
   - Compliance metrics
   - Revenue forecasting

---

## Resources

- **Refill Queries**: `dmelogic/db/refills.py`
- **Refill Service**: `dmelogic/services/refill_service.py`
- **Order Repository**: `dmelogic/db/orders.py`
- **Migrations**: `dmelogic/db/migrations.py` (Migration005)
- **Domain Models**: `dmelogic/models/order.py` (refill methods)
- **Architecture**: `ARCHITECTURE.md`
- **UnitOfWork Guide**: `UNITOFWORK_GUIDE.md`
