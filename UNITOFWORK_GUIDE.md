# UnitOfWork Pattern - Quick Reference

## When to Use UnitOfWork

Use UnitOfWork when your operation touches **multiple databases**:

- ✅ Create order + reserve inventory
- ✅ Process refill + update source order
- ✅ Delete order + write audit log
- ✅ Update patient + sync insurance

Don't use UnitOfWork for **single-database operations**:

- ❌ Fetch all patients
- ❌ Search orders by status
- ❌ Update single order field
- ❌ Insert single inventory item

---

## Service Layer Pattern

### Template: Multi-DB Service with UoW

```python
from dmelogic.db.base import UnitOfWork
from dmelogic.db import orders, inventory
from dmelogic.config import debug_log

def your_business_operation(
    input_data: YourInput,
    folder_path: Optional[str] = None,
) -> YourResult:
    """
    Your business operation that touches multiple databases.
    
    Workflow:
    1. Read from database A
    2. Write to database B
    3. Update database A
    
    Args:
        input_data: Your input DTO
        folder_path: Database folder path
        
    Returns:
        Your result data
        
    Raises:
        ValueError: If validation fails
        Exception: If operation fails
    """
    try:
        with UnitOfWork(folder_path=folder_path) as uow:
            # Get connections from UoW (one per database)
            orders_conn = uow.connection("orders.db")
            inventory_conn = uow.connection("inventory.db")
            
            # Call repositories with injected connections
            order = orders.fetch_order_by_id(input_data.order_id, conn=orders_conn)
            if not order:
                raise ValueError(f"Order {input_data.order_id} not found")
            
            # Perform operations
            item_id = inventory.reserve_item(
                hcpcs=order["hcpcs"],
                quantity=order["qty"],
                conn=inventory_conn,
            )
            
            orders.mark_order_fulfilled(
                order_id=input_data.order_id,
                item_id=item_id,
                conn=orders_conn,
            )
            
            # UoW auto-commits on successful exit
            debug_log(f"Operation completed: order {input_data.order_id}")
            return YourResult(order_id=input_data.order_id, item_id=item_id)
            
    except Exception as e:
        debug_log(f"Operation failed: {e}")
        raise
```

---

## Repository Layer Pattern

### Template: UoW-Aware Repository Function

```python
from dmelogic.db.base import get_connection
from dmelogic.config import debug_log
import sqlite3
from typing import Optional

def your_repository_operation(
    input_data: YourInput,
    conn: Optional[sqlite3.Connection] = None,
    folder_path: Optional[str] = None,
) -> YourResult:
    """
    Your repository operation with optional connection injection.
    
    Can be used two ways:
    1. Standalone: Pass conn=None, function owns connection
    2. UoW-aware: Pass conn from UoW, caller manages lifecycle
    
    Args:
        input_data: Your input parameters
        conn: Optional injected connection (from UoW)
        folder_path: Database folder path (ignored if conn provided)
        
    Returns:
        Your result data
        
    Raises:
        ValueError: If validation fails
        sqlite3.Error: If database operation fails
    """
    # Determine ownership
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection("your_database.db", folder_path=folder_path)
    
    try:
        cur = conn.cursor()
        
        # Your database operations
        cur.execute(
            "INSERT INTO your_table (field1, field2) VALUES (?, ?)",
            (input_data.field1, input_data.field2)
        )
        result_id = cur.lastrowid
        
        # Only commit if we own the connection
        if owns_connection:
            conn.commit()
            
        debug_log(f"Operation successful: {result_id}")
        return YourResult(id=result_id)
        
    except Exception as e:
        debug_log(f"Operation failed: {e}")
        raise
        
    finally:
        # Only close if we own the connection
        if owns_connection and conn:
            conn.close()
```

---

## Common Patterns

### Pattern 1: Create with Enrichment

```python
def create_entity_with_enrichment(
    base_data: BaseData,
    folder_path: Optional[str] = None,
) -> int:
    """Create entity with data from multiple sources."""
    with UnitOfWork(folder_path=folder_path) as uow:
        # Read enrichment data (may be different DB)
        enrichment = fetch_enrichment_data(base_data.ref_id)
        
        # Create main entity
        main_conn = uow.connection("main.db")
        entity_id = create_entity(base_data, enrichment, conn=main_conn)
        
        # Update related records
        related_conn = uow.connection("related.db")
        update_related(entity_id, conn=related_conn)
        
        return entity_id
```

### Pattern 2: Delete with Audit

```python
def delete_entity_with_audit(
    entity_id: int,
    reason: str,
    user: str,
    folder_path: Optional[str] = None,
) -> None:
    """Delete entity and log to audit trail."""
    with UnitOfWork(folder_path=folder_path) as uow:
        main_conn = uow.connection("main.db")
        
        # Verify exists
        entity = fetch_entity(entity_id, conn=main_conn)
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")
        
        # Cascading delete
        delete_entity_children(entity_id, conn=main_conn)
        delete_entity(entity_id, conn=main_conn)
        
        # Audit log (future: separate audit.db)
        log_deletion(entity_id, reason, user, conn=main_conn)
```

### Pattern 3: Batch Processing

```python
def process_batch(
    item_ids: List[int],
    folder_path: Optional[str] = None,
) -> tuple[int, int]:
    """Process multiple items, each in its own transaction."""
    success_count = 0
    failure_count = 0
    
    # Each item gets its own UoW for isolation
    for item_id in item_ids:
        try:
            with UnitOfWork(folder_path=folder_path) as uow:
                conn = uow.connection("main.db")
                process_item(item_id, conn=conn)
                success_count += 1
        except Exception as e:
            debug_log(f"Item {item_id} failed: {e}")
            failure_count += 1
            # Continue with next item
    
    return success_count, failure_count
```

### Pattern 4: Read-Only Multi-DB Query

```python
def get_aggregated_report(
    start_date: str,
    end_date: str,
    folder_path: Optional[str] = None,
) -> ReportData:
    """Aggregate data from multiple databases (read-only)."""
    # For read-only, UoW is optional but provides consistency
    with UnitOfWork(folder_path=folder_path) as uow:
        orders_conn = uow.connection("orders.db")
        inventory_conn = uow.connection("inventory.db")
        billing_conn = uow.connection("billing.db")
        
        orders = fetch_orders_in_range(start_date, end_date, conn=orders_conn)
        inventory = fetch_inventory_snapshot(conn=inventory_conn)
        billing = fetch_billing_summary(start_date, end_date, conn=billing_conn)
        
        return aggregate_report(orders, inventory, billing)
```

---

## Error Handling

### Service Layer Error Handling

```python
def your_service_operation(data, folder_path=None):
    """Service with comprehensive error handling."""
    try:
        with UnitOfWork(folder_path=folder_path) as uow:
            # ... your operations ...
            return result
            
    except ValueError as e:
        # Validation error (user fixable)
        debug_log(f"Validation failed: {e}")
        raise  # Re-raise for UI to handle
        
    except sqlite3.IntegrityError as e:
        # Database constraint violation
        debug_log(f"Integrity error: {e}")
        raise ValueError(f"Database constraint violated: {e}")
        
    except sqlite3.Error as e:
        # Database error
        debug_log(f"Database error: {e}")
        raise RuntimeError(f"Database operation failed: {e}")
        
    except Exception as e:
        # Unexpected error
        debug_log(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise
```

### UI Error Handling

```python
def ui_button_handler(self):
    """UI handler with user-friendly error messages."""
    try:
        result = your_service_operation(data, folder_path=self.folder)
        QMessageBox.information(self, "Success", f"Operation completed: {result}")
        self.refresh_data()
        
    except ValueError as e:
        # Validation error - show to user
        QMessageBox.warning(self, "Validation Error", str(e))
        
    except RuntimeError as e:
        # Database error - generic message
        QMessageBox.critical(self, "Error", "Database operation failed. Please try again.")
        debug_log(f"Operation failed: {e}")
        
    except Exception as e:
        # Unexpected error - generic message
        QMessageBox.critical(self, "Error", "An unexpected error occurred.")
        debug_log(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
```

---

## Testing

### Test UoW-Aware Repository

```python
import unittest
import sqlite3
from dmelogic.db.your_module import your_function

class TestYourRepository(unittest.TestCase):
    def setUp(self):
        """Create in-memory test database."""
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE TABLE your_table (id INTEGER PRIMARY KEY, name TEXT)")
        
    def tearDown(self):
        """Close test database."""
        self.conn.close()
        
    def test_with_injected_connection(self):
        """Test repository with injected connection (UoW pattern)."""
        # Arrange
        test_data = YourInput(name="test")
        
        # Act
        result = your_function(test_data, conn=self.conn)
        
        # Assert - verify but don't commit (UoW will do that)
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM your_table WHERE id = ?", (result.id,))
        row = cur.fetchone()
        self.assertEqual(row[0], "test")
        
    def test_standalone_operation(self):
        """Test repository as standalone (no UoW)."""
        # This would use get_connection internally
        # For testing, pass conn to avoid file system
        test_data = YourInput(name="test")
        result = your_function(test_data, conn=self.conn)
        
        # Should auto-commit in standalone mode
        self.conn.commit()  # Explicitly commit for test
        
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM your_table")
        count = cur.fetchone()[0]
        self.assertEqual(count, 1)
```

### Test Service with UoW

```python
import unittest
from unittest.mock import patch, MagicMock
from dmelogic.services.your_service import your_service_function

class TestYourService(unittest.TestCase):
    @patch('dmelogic.services.your_service.UnitOfWork')
    def test_service_commits_on_success(self, mock_uow_class):
        """Test that service commits on successful operation."""
        # Arrange
        mock_uow = MagicMock()
        mock_uow_class.return_value.__enter__.return_value = mock_uow
        mock_conn = MagicMock()
        mock_uow.connection.return_value = mock_conn
        
        # Act
        result = your_service_function(test_data)
        
        # Assert
        mock_uow.commit.assert_called_once()
        self.assertIsNotNone(result)
        
    @patch('dmelogic.services.your_service.UnitOfWork')
    def test_service_rolls_back_on_error(self, mock_uow_class):
        """Test that service rolls back on exception."""
        # Arrange
        mock_uow = MagicMock()
        mock_uow_class.return_value.__enter__.return_value = mock_uow
        mock_conn = MagicMock()
        mock_uow.connection.return_value = mock_conn
        
        # Simulate repository raising exception
        mock_uow.connection.side_effect = Exception("Test error")
        
        # Act & Assert
        with self.assertRaises(Exception):
            your_service_function(test_data)
        
        # rollback called via __exit__
        mock_uow.rollback.assert_called()
```

---

## Checklist for New Features

When adding a new feature:

- [ ] **Identify databases involved**
  - Single DB? Use repository directly or simple service
  - Multiple DBs? Use UnitOfWork

- [ ] **Create/update repository functions**
  - Add `conn: Optional[sqlite3.Connection] = None` parameter
  - Implement owns_connection pattern
  - Only commit if owns_connection
  - Only close if owns_connection

- [ ] **Create service function (if needed)**
  - Use UnitOfWork context manager
  - Get connections via `uow.connection("db_name.db")`
  - Pass connections to repository calls
  - Let UoW handle commit/rollback

- [ ] **Update UI to call service**
  - Remove any direct SQL
  - Call service function
  - Handle errors with QMessageBox
  - Refresh UI after success

- [ ] **Add error handling**
  - Service: catch specific exceptions, re-raise with context
  - UI: catch exceptions, show user-friendly messages

- [ ] **Write tests**
  - Repository: test with injected and owned connections
  - Service: test commit/rollback behavior
  - Integration: test full workflow

- [ ] **Update documentation**
  - Add docstrings to all functions
  - Document business rules
  - Update ARCHITECTURE.md if needed

---

## Performance Tips

1. **Batch Operations**: Use single UoW for related operations
   ```python
   with UnitOfWork() as uow:
       conn = uow.connection("main.db")
       for item in items:
           process_item(item, conn=conn)
   # Single commit for all items
   ```

2. **Read-Only Queries**: Don't need UoW for simple reads
   ```python
   # No UoW needed - just read
   conn = get_connection("main.db")
   try:
       rows = conn.execute("SELECT * FROM table").fetchall()
   finally:
       conn.close()
   ```

3. **Connection Reuse**: UoW reuses connections within scope
   ```python
   with UnitOfWork() as uow:
       conn = uow.connection("main.db")  # Opens connection
       # ... operations ...
       conn2 = uow.connection("main.db")  # Returns same connection
       assert conn is conn2
   ```

4. **WAL Mode**: Enabled by default for concurrency
   - Multiple readers don't block
   - Single writer doesn't block readers
   - Checkpointing happens automatically

---

## Common Mistakes

### ❌ Committing Inside UoW-Aware Repository

```python
def bad_repository_function(data, conn=None):
    if conn is None:
        conn = get_connection("main.db")
    
    cur = conn.cursor()
    cur.execute("INSERT INTO table VALUES (?)", (data,))
    conn.commit()  # ❌ WRONG! Always commits, even if injected
    conn.close()   # ❌ WRONG! Closes injected connection
```

### ✅ Correct: Only Commit/Close If Owner

```python
def good_repository_function(data, conn=None):
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection("main.db")
    
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO table VALUES (?)", (data,))
        
        if owns_connection:  # ✅ Correct
            conn.commit()
    finally:
        if owns_connection:  # ✅ Correct
            conn.close()
```

### ❌ Not Using UoW for Multi-DB Operations

```python
def bad_service(data):
    # ❌ No coordination between DBs
    conn1 = get_connection("db1.db")
    conn2 = get_connection("db2.db")
    
    update_db1(conn1)
    conn1.commit()
    
    # If this fails, db1 is committed but db2 is not!
    update_db2(conn2)
    conn2.commit()
```

### ✅ Correct: Use UoW for Coordination

```python
def good_service(data):
    with UnitOfWork() as uow:  # ✅ Correct
        conn1 = uow.connection("db1.db")
        conn2 = uow.connection("db2.db")
        
        update_db1(conn1)
        update_db2(conn2)
        
        # Both commit or both rollback
```

---

## Quick Reference

| Scenario | Pattern | Example |
|----------|---------|---------|
| Single DB read | Direct repo | `fetch_patients(folder_path)` |
| Single DB write | Direct repo | `create_patient(data, folder_path)` |
| Multi-DB read | UoW + repos | `get_report(start, end, folder_path)` |
| Multi-DB write | UoW + repos | `create_order_with_inventory(...)` |
| Batch process | Loop UoW | `for item: with UoW(): process(item)` |
| UI integration | Service call | `try: service(...) except: QMessageBox` |

---

## Resources

- **Full Architecture**: See `ARCHITECTURE.md`
- **UoW Implementation**: See `dmelogic/db/base.py`
- **Service Examples**: See `dmelogic/services/*.py`
- **Repository Examples**: See `dmelogic/db/*.py`
- **Test Examples**: See `tests/test_repositories.py`
