# Step 1 Complete: Clean Database Usage

## ✅ What Was Accomplished

### 1. Helper Functions for Safe Row Conversion

**File**: `dmelogic/db/base.py`

Added two helper functions to safely convert `sqlite3.Row` objects to dictionaries:

```python
def row_to_dict(row: Optional[sqlite3.Row]) -> Dict[str, Any]:
    """
    Safely convert a sqlite3.Row to a dict.
    Returns empty dict if row is None.
    """
    if row is None:
        return {}
    return dict(row)

def rows_to_dicts(rows: list[sqlite3.Row]) -> list[Dict[str, Any]]:
    """
    Convert a list of sqlite3.Row objects to list of dicts.
    """
    return [dict(row) for row in rows]
```

**Why This Matters**:
- `sqlite3.Row` objects don't have a `.get()` method
- Calling `row.get('field')` causes `AttributeError`
- These helpers ensure safe conversion to regular Python dicts

---

### 2. Repository Classes with UnitOfWork Support

**File**: `dmelogic/db/repositories.py` (NEW - 450 lines)

Created repository classes following the Repository pattern:
- `PatientRepository`
- `PrescriberRepository`
- `OrderRepository`
- `InventoryRepository`

**Key Features**:
- ✅ Optional `conn` parameter for UnitOfWork participation
- ✅ Automatic connection management in standalone mode
- ✅ All methods return Python dicts (not sqlite3.Row)
- ✅ Comprehensive error logging
- ✅ Context manager pattern for safe resource handling

---

## 📖 Usage Guide

### Standalone Usage (Auto-Commit)

```python
from dmelogic.db.repositories import PatientRepository

# Create repository
repo = PatientRepository()

# Fetch all patients (returns list of dicts)
patients = repo.get_all()

for patient in patients:
    # Safe .get() usage on dict
    name = patient.get('first_name', 'Unknown')
    print(f"Patient: {name}")

# Fetch single patient
patient = repo.get_by_id(123)
if patient:
    print(f"Found: {patient['last_name']}, {patient['first_name']}")
```

---

### Transactional Usage (UnitOfWork)

```python
from dmelogic.db.base import UnitOfWork
from dmelogic.db.repositories import PatientRepository, OrderRepository

# Multiple operations in single transaction
with UnitOfWork() as uow:
    # Get connections for each database
    patient_conn = uow.connection("patients.db")
    order_conn = uow.connection("orders.db")
    
    # Create repositories with shared connections
    patient_repo = PatientRepository(conn=patient_conn)
    order_repo = OrderRepository(conn=order_conn)
    
    # Perform operations
    patient = patient_repo.get_by_id(123)
    order = order_repo.get_by_id(456)
    
    # Modify data...
    order_repo.soft_delete(456, deleted_by="user123")
    
    # Commit all changes atomically
    uow.commit()
    
    # If exception occurs, automatic rollback
```

---

### Migration Pattern: Old vs New

**❌ OLD (Direct Connection)**:
```python
def load_deleted_orders(self):
    conn = sqlite3.connect(self.parent.orders_db_path)  # Direct connection
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM deleted_orders
        ORDER BY deleted_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # rows are sqlite3.Row objects
    # Calling row.get('field') would fail!
```

**✅ NEW (Repository)**:
```python
def load_deleted_orders(self):
    from dmelogic.db.repositories import OrderRepository
    
    repo = OrderRepository()
    orders = repo.get_deleted_orders()
    
    # orders is list of dicts
    # Safe to use .get()
    for order in orders:
        name = order.get('patient_last_name', 'Unknown')
```

---

## 📊 Repository API Reference

### PatientRepository

```python
repo = PatientRepository(conn=None, folder_path=None)

# Methods
patients = repo.get_all()                          # -> List[Dict]
patient = repo.get_by_id(123)                      # -> Dict | None
patients = repo.search_by_name("Smith", "John")    # -> List[Dict]
patients = repo.search_by_name("Smith", "John", dob="1980-01-15")
```

### PrescriberRepository

```python
repo = PrescriberRepository(conn=None, folder_path=None)

# Methods
prescribers = repo.get_all()                       # -> List[Dict]
prescriber = repo.get_by_id(456)                   # -> Dict | None
prescriber = repo.get_by_npi("1234567890")         # -> Dict | None
```

### OrderRepository

```python
repo = OrderRepository(conn=None, folder_path=None)

# Methods
order = repo.get_by_id(789)                        # -> Dict | None
deleted = repo.get_deleted_orders()                # -> List[Dict]
success = repo.soft_delete(789, deleted_by="user") # -> bool
```

### InventoryRepository

```python
repo = InventoryRepository(conn=None, folder_path=None)

# Methods
items = repo.get_all()                             # -> List[Dict]
item = repo.get_by_hcpcs("E0601")                  # -> Dict | None
```

---

## 🔧 Advanced UnitOfWork Examples

### Example 1: Create Order with Items

```python
from dmelogic.db.base import UnitOfWork
from dmelogic.db.repositories import OrderRepository, InventoryRepository

def create_order_transactional(patient_id: int, items: list):
    """Create order and update inventory in single transaction."""
    
    with UnitOfWork() as uow:
        order_conn = uow.connection("orders.db")
        inv_conn = uow.connection("inventory.db")
        
        order_repo = OrderRepository(conn=order_conn)
        inv_repo = InventoryRepository(conn=inv_conn)
        
        # Create order
        cursor = order_conn.cursor()
        cursor.execute("""
            INSERT INTO orders (patient_id, order_date)
            VALUES (?, ?)
        """, (patient_id, "2025-12-05"))
        order_id = cursor.lastrowid
        
        # Add items and update inventory
        for item in items:
            hcpcs = item['hcpcs']
            quantity = item['quantity']
            
            # Insert order item
            cursor.execute("""
                INSERT INTO order_items (order_id, hcpcs_code, quantity)
                VALUES (?, ?, ?)
            """, (order_id, hcpcs, quantity))
            
            # Update inventory (using separate connection)
            inv_cursor = inv_conn.cursor()
            inv_cursor.execute("""
                UPDATE inventory 
                SET quantity_on_hand = quantity_on_hand - ?
                WHERE hcpcs_code = ?
            """, (quantity, hcpcs))
        
        # Commit both databases atomically
        uow.commit()
        
        return order_id
```

### Example 2: Refill Workflow

```python
def process_refill_transactional(order_id: int, fill_date: str):
    """Process refill with audit log in single transaction."""
    
    with UnitOfWork() as uow:
        conn = uow.connection("orders.db")
        order_repo = OrderRepository(conn=conn)
        
        # Get original order
        original = order_repo.get_by_id(order_id)
        if not original:
            raise ValueError(f"Order {order_id} not found")
        
        # Create refill order
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (
                patient_id, prescriber_id, order_date,
                original_order_id, status
            ) VALUES (?, ?, ?, ?, 'Refill')
        """, (
            original['patient_id'],
            original['prescriber_id'],
            fill_date,
            order_id
        ))
        refill_id = cursor.lastrowid
        
        # Update refill count
        cursor.execute("""
            UPDATE orders
            SET refills_processed = refills_processed + 1,
                last_refill_date = ?
            WHERE order_id = ?
        """, (fill_date, order_id))
        
        # Log audit entry
        cursor.execute("""
            INSERT INTO audit_log (action, entity_type, entity_id, timestamp)
            VALUES ('refill_processed', 'order', ?, ?)
        """, (refill_id, fill_date))
        
        # Commit all changes atomically
        uow.commit()
        
        return refill_id
```

---

## 🎯 Benefits

### 1. Type Safety
- All repository methods return `Dict[str, Any]` or `List[Dict[str, Any]]`
- IDE autocomplete works better
- `.get()` method always available (no AttributeError)

### 2. Testability
```python
# Easy to mock repositories in tests
def test_load_deleted_orders(mocker):
    mock_repo = mocker.Mock()
    mock_repo.get_deleted_orders.return_value = [
        {'id': 1, 'patient_name': 'Test'},
    ]
    
    # Test code that uses mock_repo
```

### 3. Transaction Safety
```python
# If any operation fails, all are rolled back
try:
    with UnitOfWork() as uow:
        # ... multiple database operations ...
        if error_condition:
            raise ValueError("Something wrong")
        uow.commit()
except ValueError:
    # All changes automatically rolled back
```

### 4. No More Direct Connections in UI
```python
# ❌ BAD (UI directly accessing database)
conn = sqlite3.connect(self.parent.orders_db_path)

# ✅ GOOD (UI uses repository)
repo = OrderRepository()
orders = repo.get_deleted_orders()
```

---

## 📝 Migration Checklist

When updating existing code:

- [ ] Replace `sqlite3.connect()` with repository calls
- [ ] Remove manual `conn.close()` (repositories handle it)
- [ ] Change `row['field']` to `dict.get('field', default)`
- [ ] Use `with UnitOfWork()` for multi-step operations
- [ ] Convert `conn.row_factory = sqlite3.Row` usage to repository methods
- [ ] Remove try/except around connection management (handled by repos)

---

## 🔄 Backward Compatibility

**Existing code continues to work**:
- Old functions like `fetch_all_patients()` still exist
- Repositories are **additive**, not replacing
- Migrate incrementally as needed
- No breaking changes

**Recommended Migration Path**:
1. New code → Use repositories from day one
2. Bug fixes → Convert affected functions to repositories
3. Refactoring → Gradually migrate old code
4. Eventually → Deprecate old direct-connection functions

---

## 🚀 Next Steps (Roadmap Step 2)

Now that Step 1 is complete, we can move to **Step 2: Solidify Services & UoW**:

1. Create workflow services that use repositories
2. Implement `create_order_with_items()` service
3. Implement `process_refill()` service
4. Add audit logging to all workflows
5. Update UI to call services instead of direct DB access

---

## 📚 Related Documentation

- `ROADMAP.md` - Full development roadmap (Steps 1-5)
- `UNITOFWORK_GUIDE.md` - Detailed UnitOfWork pattern guide
- `ARCHITECTURE.md` - Overall system architecture
- `DATABASE.md` - Database schema reference

---

*Step 1 completed: December 5, 2025*  
*Foundation ready for Step 2: Services & Workflows*
