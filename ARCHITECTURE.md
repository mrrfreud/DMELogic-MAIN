# DME Logic Architecture

## Overview

DME Logic follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│              UI Layer (PyQt6)                   │
│  - Main window, dialogs, wizards                │
│  - Event handlers                               │
│  - Display formatting                           │
└──────────────────┬──────────────────────────────┘
                   │ calls
                   ↓
┌─────────────────────────────────────────────────┐
│           Service Layer                         │
│  - Business logic orchestration                 │
│  - Multi-DB coordination via UnitOfWork         │
│  - Transaction boundaries                       │
│  - Workflow enforcement                         │
└──────────────────┬──────────────────────────────┘
                   │ uses
                   ↓
┌─────────────────────────────────────────────────┐
│         Repository Layer (Data Access)          │
│  - CRUD operations                              │
│  - SQL queries                                  │
│  - Connection management (injected or owned)    │
│  - Type conversions                             │
└──────────────────┬──────────────────────────────┘
                   │ reads/writes
                   ↓
┌─────────────────────────────────────────────────┐
│           Database Layer (SQLite)               │
│  - patients.db, orders.db, inventory.db, etc.  │
│  - Schema definitions                           │
│  - Indexes, constraints                         │
└─────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. **No Direct SQL in UI**
- UI code NEVER opens database connections
- UI code NEVER writes SQL queries
- All database access goes through service or repository layers

### 2. **Service Layer Orchestration**
- Services coordinate multiple repository calls
- Services define transaction boundaries
- Services enforce business rules
- Services use UnitOfWork for multi-DB operations

### 3. **Repository Pattern**
- Each database has its own repository module
- Repositories provide CRUD operations
- Repositories accept optional `conn` parameter for UoW injection
- Repositories own connection lifecycle when `conn=None`

### 4. **UnitOfWork Pattern**
- Coordinates operations across multiple databases
- Provides transactional semantics (commit/rollback)
- Manages connection lifecycle
- Auto-commit on success, auto-rollback on exception

---

## Database Structure

DME Logic uses **7 separate SQLite databases**:

| Database | Purpose | Key Tables |
|----------|---------|------------|
| `orders.db` | Order management | `orders`, `order_items` |
| `patients.db` | Patient records | `patients` |
| `prescribers.db` | Provider directory | `prescribers` |
| `insurance_names.db` | Insurance companies | `insurance_names` |
| `inventory.db` | Product catalog | `inventory` |
| `suppliers.db` | Vendor management | `suppliers` |
| `billing.db` | Billing/claims | `billing` |

### Database Configuration

All databases use optimized PRAGMAs:
```sql
PRAGMA foreign_keys = ON;         -- Enforce referential integrity
PRAGMA journal_mode = WAL;        -- Write-Ahead Logging for concurrency
PRAGMA synchronous = NORMAL;      -- Balanced performance/safety
```

---

## Repository Pattern Implementation

### Pattern: Optional Connection Injection

Repositories follow this pattern:

```python
def create_something(
    data: SomeInput,
    conn: Optional[sqlite3.Connection] = None,
    folder_path: Optional[str] = None,
) -> int:
    """
    Create a record in the database.
    
    Args:
        data: Input data for creation
        conn: Optional injected connection (from UoW)
        folder_path: Database folder path
        
    Returns:
        New record ID
    """
    owns_connection = conn is None
    if owns_connection:
        conn = get_connection("database.db", folder_path=folder_path)
    
    try:
        cur = conn.cursor()
        # ... perform operation ...
        
        # Only commit if we own the connection
        if owns_connection:
            conn.commit()
            
        return record_id
        
    finally:
        if owns_connection and conn:
            conn.close()
```

### Key Points:
- **`conn=None`**: Repository creates and owns the connection (standalone operation)
- **`conn=injected`**: UoW manages lifecycle (multi-DB transaction)
- **Commit only if owner**: Prevents premature commits in UoW scenarios
- **Always close if owner**: Prevents connection leaks

---

## UnitOfWork Pattern

### Usage Example

```python
from dmelogic.db.base import UnitOfWork

def complex_operation(folder_path: Optional[str] = None) -> None:
    """Multi-database operation with transactional guarantees."""
    with UnitOfWork(folder_path=folder_path) as uow:
        # Get connections from UoW (reused within scope)
        orders_conn = uow.connection("orders.db")
        inventory_conn = uow.connection("inventory.db")
        
        # Call repositories with injected connections
        order_id = create_order(data, conn=orders_conn)
        reserve_inventory(hcpcs, qty, conn=inventory_conn)
        
        # On success: UoW auto-commits both databases
        # On exception: UoW auto-rolls back both databases
```

### Context Manager Protocol

```python
class UnitOfWork:
    def __enter__(self) -> "UnitOfWork":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()  # Exception occurred
        elif not self._committed:
            self.commit()    # Success path
        self.close()         # Always cleanup
        return False         # Don't suppress exceptions
```

### Limitations

⚠️ **SQLite Multi-DB Atomicity**: SQLite cannot guarantee true ACID atomicity across multiple `.db` files. UnitOfWork provides **best-effort coordination**:
- Same connection pool for related operations
- Single commit/rollback decision point
- Reduces (but doesn't eliminate) partial-commit scenarios

For strict atomicity, consider:
- Consolidating related tables into one database
- Using ATTACH DATABASE for multi-DB transactions
- Accepting eventual consistency for cross-DB operations

---

## Service Layer

Services coordinate multiple repositories and define business workflows.

### Service Examples

#### Order Creation Service

```python
def create_order_with_enrichment(
    result: OrderWizardResult,
    folder_path: Optional[str] = None,
) -> int:
    """
    Create order with enriched data from multiple sources.
    
    Workflow:
    1. Read insurance from patients.db
    2. Read pricing from inventory.db  
    3. Create order in orders.db
    4. Update items with enriched data
    
    Uses UnitOfWork to coordinate 3 databases.
    """
    with UnitOfWork(folder_path=folder_path) as uow:
        # Read insurance (patients.db)
        insurance_data = fetch_patient_insurance(...)
        
        # Create order (orders.db)
        orders_conn = uow.connection("orders.db")
        order_id = create_order_from_wizard_result_uow(result, conn=orders_conn)
        
        # Enrich items with inventory data
        for item in result.items:
            inv_row = fetch_latest_item_by_hcpcs(item.hcpcs, folder_path)
            update_order_item(order_id, item.id, inv_row, conn=orders_conn)
        
        return order_id
```

#### Refill Processing Service

```python
def process_refills(
    selected_item_ids: Iterable[int],
    refill_fill_date: str,
    folder_path: Optional[str] = None,
) -> int:
    """
    Process multiple refill orders.
    
    For each item:
    1. Create new order from source
    2. Update source item refills/last_filled_date
    3. Reserve inventory (future)
    
    Each refill uses its own UoW for isolation.
    """
    processed = 0
    for item_id in selected_item_ids:
        try:
            with UnitOfWork(folder_path=folder_path) as uow:
                orders_conn = uow.connection("orders.db")
                
                src = fetch_order_item_with_header(item_id, conn=orders_conn)
                new_order_id = create_refill_order_from_source(src, conn=orders_conn)
                mark_refill_used(item_id, refill_fill_date, conn=orders_conn)
                
                processed += 1
        except Exception as e:
            debug_log(f"Refill {item_id} failed: {e}")
            continue
    
    return processed
```

#### Order Deletion with Audit

```python
def delete_order_with_audit(
    order_id: int,
    reason: str,
    deleted_by: str,
    folder_path: Optional[str] = None,
) -> None:
    """
    Delete order and log to audit trail.
    
    Workflow:
    1. Delete order_items (FK constraint)
    2. Delete order header
    3. Insert audit log entry
    
    All atomic via UnitOfWork.
    """
    with UnitOfWork(folder_path=folder_path) as uow:
        orders_conn = uow.connection("orders.db")
        
        # Cascading delete
        delete_order_items(order_id, conn=orders_conn)
        delete_order(order_id, conn=orders_conn)
        
        # Audit trail (future: separate audit.db)
        log_deletion(order_id, reason, deleted_by, conn=orders_conn)
```

---

## UI Integration

UI code should only call service layer, never repositories directly.

### ❌ Anti-Pattern (Direct Repository Call)

```python
def create_order_from_wizard(self, result):
    # BAD: UI calling repository directly
    order_id = create_order_from_wizard_result(result, folder_path=self.folder)
    self.edit_order_by_id(order_id)
```

### ✅ Correct Pattern (Service Layer)

```python
def create_order_from_wizard(self, result):
    # GOOD: UI calling service
    try:
        order_id = create_order_with_enrichment(result, folder_path=self.folder)
        self.refresh_orders_table()
        self.edit_order_by_id(order_id)
        self.statusBar().showMessage(f"Order {order_id} created", 5000)
    except Exception as e:
        QMessageBox.warning(self, "Error", f"Failed to create order: {e}")
```

### UI Responsibilities

- ✅ Gather user input
- ✅ Call service functions
- ✅ Display results
- ✅ Handle errors with user-friendly messages
- ✅ Refresh UI after changes

### UI Must NOT

- ❌ Open database connections
- ❌ Write SQL queries
- ❌ Manage transactions
- ❌ Perform business logic calculations
- ❌ Coordinate multiple repository calls

---

## Error Handling

### Repository Layer
- Raise exceptions with descriptive messages
- Use `debug_log()` for diagnostic information
- Let exceptions bubble up to service layer

### Service Layer
- Catch repository exceptions
- Log errors with context
- Re-raise or convert to domain exceptions
- Provide meaningful error messages for UI

### UI Layer
- Catch service exceptions
- Display user-friendly error dialogs
- Log errors for support
- Don't expose technical details to users

Example:
```python
try:
    order_id = create_order_with_enrichment(result, folder_path)
except ValueError as e:
    # Validation error (user fixable)
    QMessageBox.warning(self, "Validation Error", str(e))
except sqlite3.IntegrityError as e:
    # Database constraint violation
    QMessageBox.critical(self, "Database Error", "Failed to create order: duplicate record")
    debug_log(f"Order creation failed: {e}")
except Exception as e:
    # Unexpected error
    QMessageBox.critical(self, "Error", "An unexpected error occurred")
    debug_log(f"Unexpected error in order creation: {e}")
    import traceback
    traceback.print_exc()
```

---

## Testing Strategy

### Repository Tests
- Use in-memory SQLite (`:memory:`)
- Test CRUD operations in isolation
- Verify connection lifecycle (own vs injected)
- Test edge cases (null values, missing data)

### Service Tests
- Mock repositories or use in-memory DBs
- Test business logic
- Verify UoW commit/rollback behavior
- Test error handling and recovery

### Integration Tests
- Use test database files
- Test full workflows end-to-end
- Verify multi-DB coordination
- Test concurrent operations (WAL mode)

---

## Migration Path

To convert legacy code to this architecture:

1. **Identify direct SQL in UI**
   - Search for `sqlite3.connect()` in UI files
   - Search for `cursor.execute()` in UI files

2. **Create repository function**
   - Move SQL to appropriate `dmelogic/db/*.py` module
   - Add optional `conn` parameter
   - Implement own/inject pattern

3. **Create service function (if multi-DB)**
   - Create function in `dmelogic/services/*.py`
   - Use UnitOfWork if multiple databases involved
   - Inject connections into repositories

4. **Update UI to call service**
   - Replace direct SQL with service call
   - Add proper error handling
   - Update UI after operation

---

## Best Practices

### ✅ DO

- Use services for all multi-DB workflows
- Use UnitOfWork for transactional boundaries
- Inject connections from UoW into repositories
- Close connections when you own them
- Log errors with context
- Use type hints
- Write docstrings for public functions
- Test repository functions with in-memory DB

### ❌ DON'T

- Open database connections in UI code
- Write SQL queries in UI code
- Commit inside repository if `conn` is injected
- Forget to close owned connections
- Suppress exceptions without logging
- Use broad exception handlers
- Leave transactions open
- Access multiple DBs without UoW

---

## Future Enhancements

### Planned Features

1. **Audit Database**
   - Dedicated `audit.db` for all changes
   - Track who/when/what for compliance
   - Integrate with delete_order_with_audit service

2. **Connection Pooling**
   - Reuse connections across operations
   - Reduce overhead for high-frequency queries
   - Consider `sqlite3.Connection` pool wrapper

3. **Read Replicas**
   - Separate read-only connections for reporting
   - Reduce contention on main databases
   - Use WAL mode reader connections

4. **Event Sourcing**
   - Store domain events (OrderCreated, RefillProcessed)
   - Rebuild state from events
   - Enable audit trails and analytics

5. **Repository Base Class**
   - Common CRUD operations
   - Standardized connection handling
   - Reduce boilerplate

6. **Service Base Class**
   - Common UoW setup
   - Standard error handling
   - Logging integration

---

## Architecture Decision Records

### ADR-001: Separate Databases per Domain
**Status**: Accepted  
**Context**: Legacy monolithic database was hard to maintain  
**Decision**: Split into 7 domain-specific databases  
**Consequences**: Better modularity, need UoW for cross-DB operations

### ADR-002: UnitOfWork Pattern
**Status**: Accepted  
**Context**: Need transactional guarantees across multiple databases  
**Decision**: Implement UnitOfWork pattern for multi-DB coordination  
**Consequences**: Best-effort atomicity, cleaner service code

### ADR-003: Optional Connection Injection
**Status**: Accepted  
**Context**: Repositories need to work standalone and in UoW context  
**Decision**: Repositories accept optional `conn` parameter  
**Consequences**: Flexible usage, own/inject pattern

### ADR-004: Service Layer for Business Logic
**Status**: Accepted  
**Context**: Complex workflows were scattered across UI  
**Decision**: Create service layer for orchestration  
**Consequences**: Clear separation of concerns, testable business logic

### ADR-005: No SQL in UI
**Status**: Accepted  
**Context**: UI code had direct database access  
**Decision**: UI can only call services, never repositories  
**Consequences**: Cleaner UI code, easier to test, better maintainability

---

## Contributing

When adding new features:

1. **Database changes**: Add migrations in `dmelogic/db/migrations.py`
2. **New tables**: Add repository functions in `dmelogic/db/*.py`
3. **Multi-DB workflows**: Add service in `dmelogic/services/*.py`
4. **UI features**: Call services from UI, handle errors gracefully
5. **Tests**: Add repository tests and service tests
6. **Documentation**: Update this file with patterns and ADRs

---

## Questions?

For architecture questions or patterns not covered here:
- Check existing service implementations in `dmelogic/services/`
- Review repository patterns in `dmelogic/db/`
- Read UnitOfWork implementation in `dmelogic/db/base.py`
- Search for similar patterns in the codebase
