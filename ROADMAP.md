# DME Logic - Development Roadmap

## Current Status

**Phases 1-5 Complete** ✅

- ✅ Phase 1: Professional touches (tests, logging, migrations)
- ✅ Phase 2: Refill tracking system
- ✅ Phase 3: Unified dark theme
- ✅ Phase 4: UI consistency (2,770 lines of reusable components)
- ✅ Phase 5: OCR & NPI external services (caching, error handling)

**Architecture Summary**:
- Database: SQLite with proper connection management
- UI: PyQt6 with unified dark theme
- Services: NPI caching, OCR status checking
- Infrastructure: Logging, migrations, backups

---

## Path to Commercial Release

The following steps represent the critical path from current state to production-ready software. Each step builds on the previous one, moving from data layer → business logic → presentation layer → domain features.

---

## Step 1: Clean DB Usage 🏗️

**Goal**: Eliminate all direct `sqlite3.connect()` calls from UI layer. Enforce single connection management pattern.

**Priority**: **CRITICAL** - Foundation for all subsequent work  
**Estimated Effort**: 3-5 days  
**Dependencies**: None

### Issues to Fix

#### 1.1 Remove Direct Connections in MainWindow

**Current Problem**:
```python
# main_window.py - line ~2800
def create_order_from_wizard(self):
    conn = sqlite3.connect(self.orders_db_path)  # ❌ Direct connection
    cursor = conn.cursor()
    # ... raw SQL inserts
```

**Solution**:
```python
# Use order_workflow service instead
from dmelogic.workflows.order_workflow import create_order_with_items

def create_order_from_wizard(self):
    order_id = create_order_with_items(
        patient_id=self.wizard_data['patient_id'],
        prescriber_id=self.wizard_data['prescriber_id'],
        items=self.wizard_data['items'],
        notes=self.wizard_data.get('notes')
    )
    return order_id
```

**Files to Modify**:
- `dmelogic/ui/main_window.py` - Replace direct DB calls with `order_workflow.create_order_with_items()`
- `dmelogic/workflows/order_workflow.py` - Ensure complete order creation logic

**Benefits**:
- ✅ Single transaction for order + items
- ✅ Automatic audit logging
- ✅ Consistent error handling
- ✅ Easier testing

---

#### 1.2 Fix Deleted Orders Dialog

**Current Problem**:
```python
# Somewhere in deleted orders dialog
conn = sqlite3.connect(self.parent.orders_db_path)  # ❌ Direct connection
```

**Solution**:
```python
# Use get_connection() or repository
from dmelogic.db.base import get_connection

def load_deleted_orders(self):
    with get_connection('orders') as conn:
        # Query deleted orders
        cursor = conn.execute("""
            SELECT * FROM orders 
            WHERE deleted_at IS NOT NULL
            ORDER BY deleted_at DESC
        """)
        return cursor.fetchall()
```

**Better Solution** (use repository pattern):
```python
from dmelogic.db.orders import OrderRepository

def load_deleted_orders(self):
    repo = OrderRepository()
    return repo.get_deleted_orders()
```

**Files to Modify**:
- Search for deleted orders dialog (grep for "deleted.*order")
- Add `get_deleted_orders()` method to `dmelogic/db/orders.py`

---

#### 1.3 Fix sqlite3.Row `.get()` Bug

**Current Problem**:
```python
# sqlite3.Row doesn't have .get() method
name = row.get('patient_name')  # ❌ AttributeError
```

**Solutions**:

**Option A**: Convert to dict
```python
row_dict = dict(row)
name = row_dict.get('patient_name', 'Unknown')
```

**Option B**: Use column index
```python
name = row['patient_name']  # Works with sqlite3.Row
```

**Option C**: Use try/except
```python
try:
    name = row['patient_name']
except (KeyError, IndexError):
    name = 'Unknown'
```

**Recommended**: Option A for consistency
```python
def _row_to_dict(row) -> dict:
    """Convert sqlite3.Row to dict safely."""
    return dict(row) if row else {}
```

**Files to Search**:
```bash
grep -r "\.get\(" dmelogic/db/
grep -r "row\.get" dmelogic/ui/
```

**Fix Pattern**:
```python
# Before
patient = cursor.fetchone()
name = patient.get('name')  # ❌

# After
patient = cursor.fetchone()
patient_dict = dict(patient) if patient else {}
name = patient_dict.get('name', 'Unknown')  # ✅
```

---

### Step 1 Checklist

- [ ] **MainWindow.create_order_from_wizard** - Replace with `order_workflow.create_order_with_items()`
- [ ] **Deleted orders dialog** - Use `get_connection()` or repository
- [ ] **All `.get()` on sqlite3.Row** - Convert to dict or use indexing
- [ ] **Search all UI files** - Find remaining `sqlite3.connect()` calls
- [ ] **Add helper function** - `_row_to_dict(row)` in `dmelogic/db/base.py`
- [ ] **Update repositories** - Ensure all return dicts or domain models
- [ ] **Test connection pooling** - Verify `get_connection()` works everywhere
- [ ] **Document pattern** - Update `ARCHITECTURE.md` with DB access rules

---

## Step 2: Solidify Services & Unit of Work 🔧

**Goal**: Implement transactional workflows with UnitOfWork pattern. Enable multi-repository operations with proper rollback.

**Priority**: **HIGH** - Enables complex business logic  
**Estimated Effort**: 5-7 days  
**Dependencies**: Step 1 complete

### 2.1 Implement Unit of Work Pattern

**Purpose**: Coordinate multiple repository operations in a single transaction.

**Create**: `dmelogic/db/unit_of_work.py`

```python
"""
Unit of Work pattern for transactional operations.
"""
from contextlib import contextmanager
from typing import Optional
import sqlite3

class UnitOfWork:
    """
    Manages a database transaction across multiple repositories.
    
    Usage:
        with UnitOfWork() as uow:
            order_id = uow.orders.create_order(...)
            uow.order_items.add_item(order_id, ...)
            uow.audit_log.log_action(...)
            uow.commit()  # All or nothing
    """
    
    def __init__(self, db_path: Optional[str] = None):
        from dmelogic.paths import orders_db_path
        self.db_path = db_path or orders_db_path()
        self.conn: Optional[sqlite3.Connection] = None
        self._committed = False
    
    def __enter__(self):
        """Start transaction."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("BEGIN")
        
        # Initialize repositories with this connection
        from dmelogic.db.orders import OrderRepository
        from dmelogic.db.patients import PatientRepository
        from dmelogic.db.prescribers import PrescriberRepository
        
        self.orders = OrderRepository(conn=self.conn)
        self.patients = PatientRepository(conn=self.conn)
        self.prescribers = PrescriberRepository(conn=self.conn)
        
        return self
    
    def commit(self):
        """Commit transaction."""
        if self.conn and not self._committed:
            self.conn.commit()
            self._committed = True
    
    def rollback(self):
        """Rollback transaction."""
        if self.conn and not self._committed:
            self.conn.rollback()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection, rollback if exception."""
        try:
            if exc_type is not None:
                self.rollback()
            elif not self._committed:
                # Auto-commit if no exception and not already committed
                self.commit()
        finally:
            if self.conn:
                self.conn.close()
```

---

### 2.2 Update Repositories for UoW

**Pattern**: Repositories accept optional `conn` parameter.

**Example**: `dmelogic/db/orders.py`

```python
class OrderRepository:
    """Order data access with optional connection injection."""
    
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        """
        Initialize repository.
        
        Args:
            conn: Optional connection for UnitOfWork pattern.
                  If None, will create own connections per operation.
        """
        self._conn = conn
    
    @contextmanager
    def _get_connection(self):
        """Get connection (provided or create new)."""
        if self._conn:
            # Part of UoW - use provided connection
            yield self._conn
        else:
            # Standalone - create and manage connection
            with get_connection('orders') as conn:
                yield conn
    
    def create_order(self, patient_id: int, prescriber_id: int, 
                     order_date: str, notes: str = None) -> int:
        """Create order (participates in UoW if conn provided)."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO orders (patient_id, prescriber_id, order_date, notes)
                VALUES (?, ?, ?, ?)
            """, (patient_id, prescriber_id, order_date, notes))
            
            # If not in UoW, commit now
            if not self._conn:
                conn.commit()
            
            return cursor.lastrowid
    
    def get_order(self, order_id: int) -> Optional[dict]:
        """Fetch order by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM orders WHERE order_id = ?",
                (order_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
```

**Files to Update**:
- `dmelogic/db/orders.py` - OrderRepository
- `dmelogic/db/patients.py` - PatientRepository
- `dmelogic/db/prescribers.py` - PrescriberRepository
- `dmelogic/db/inventory.py` - InventoryRepository
- `dmelogic/db/insurance.py` - InsurancePolicyRepository

---

### 2.3 Refactor create_order_from_wizard

**Current**: Multiple separate database operations  
**Goal**: Single transaction with rollback on failure

**File**: `dmelogic/workflows/order_workflow.py`

```python
def create_order_with_items(
    patient_id: int,
    prescriber_id: int,
    items: list[dict],
    order_date: str = None,
    notes: str = None
) -> int:
    """
    Create order with items in a single transaction.
    
    Args:
        patient_id: Patient ID
        prescriber_id: Prescriber ID
        items: List of dicts with 'hcpcs', 'quantity', 'price'
        order_date: Order date (default: today)
        notes: Optional notes
    
    Returns:
        order_id: Created order ID
    
    Raises:
        ValueError: If patient/prescriber not found
        sqlite3.Error: If database operation fails
    """
    from datetime import date
    from dmelogic.db.unit_of_work import UnitOfWork
    
    order_date = order_date or date.today().isoformat()
    
    try:
        with UnitOfWork() as uow:
            # Validate patient exists
            patient = uow.patients.get_patient(patient_id)
            if not patient:
                raise ValueError(f"Patient {patient_id} not found")
            
            # Validate prescriber exists
            prescriber = uow.prescribers.get_prescriber(prescriber_id)
            if not prescriber:
                raise ValueError(f"Prescriber {prescriber_id} not found")
            
            # Create order
            order_id = uow.orders.create_order(
                patient_id=patient_id,
                prescriber_id=prescriber_id,
                order_date=order_date,
                notes=notes
            )
            
            # Add items
            for item in items:
                uow.order_items.add_item(
                    order_id=order_id,
                    hcpcs_code=item['hcpcs'],
                    quantity=item['quantity'],
                    unit_price=item['price']
                )
            
            # Log audit entry
            uow.audit_log.log_action(
                action='order_created',
                entity_type='order',
                entity_id=order_id,
                details=f"Order created with {len(items)} items"
            )
            
            # Commit transaction
            uow.commit()
            
            return order_id
            
    except Exception as e:
        # Rollback happens automatically
        raise RuntimeError(f"Failed to create order: {e}") from e
```

---

### 2.4 Refactor Refill Workflows

**File**: `dmelogic/workflows/refill_workflow.py`

```python
def process_refill(order_id: int, refill_date: str = None) -> int:
    """
    Process refill for an order in a single transaction.
    
    Returns:
        refill_id: Created refill record ID
    """
    from datetime import date
    from dmelogic.db.unit_of_work import UnitOfWork
    
    refill_date = refill_date or date.today().isoformat()
    
    with UnitOfWork() as uow:
        # Get original order
        order = uow.orders.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Check refill eligibility
        last_refill = uow.refills.get_last_refill(order_id)
        if not is_refill_due(last_refill, refill_date):
            raise ValueError("Refill not due yet")
        
        # Create refill record
        refill_id = uow.refills.create_refill(
            order_id=order_id,
            refill_date=refill_date,
            status='pending'
        )
        
        # Update order last_refill_date
        uow.orders.update_last_refill(order_id, refill_date)
        
        # Log audit entry
        uow.audit_log.log_action(
            action='refill_processed',
            entity_type='refill',
            entity_id=refill_id,
            details=f"Refill for order {order_id}"
        )
        
        uow.commit()
        return refill_id
```

---

### 2.5 Refactor Delete Order with Audit

**File**: `dmelogic/workflows/order_workflow.py`

```python
def delete_order(order_id: int, reason: str = None) -> bool:
    """
    Soft-delete order with audit trail.
    
    Returns:
        True if deleted successfully
    """
    from datetime import datetime
    from dmelogic.db.unit_of_work import UnitOfWork
    
    with UnitOfWork() as uow:
        # Get order (ensure exists)
        order = uow.orders.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        # Soft delete
        deleted_at = datetime.now().isoformat()
        uow.orders.soft_delete(order_id, deleted_at)
        
        # Log deletion
        uow.audit_log.log_action(
            action='order_deleted',
            entity_type='order',
            entity_id=order_id,
            details=f"Reason: {reason or 'No reason provided'}"
        )
        
        uow.commit()
        return True
```

---

### Step 2 Checklist

- [ ] **Create UnitOfWork class** - `dmelogic/db/unit_of_work.py`
- [ ] **Update OrderRepository** - Add `conn` parameter
- [ ] **Update PatientRepository** - Add `conn` parameter
- [ ] **Update PrescriberRepository** - Add `conn` parameter
- [ ] **Update InventoryRepository** - Add `conn` parameter
- [ ] **Refactor create_order_from_wizard** - Use UoW pattern
- [ ] **Refactor refill workflows** - Use UoW pattern
- [ ] **Refactor delete_order** - Use UoW with audit
- [ ] **Add unit tests** - Test UoW rollback behavior
- [ ] **Document UoW pattern** - Update `ARCHITECTURE.md`

---

## Step 3: Domain Models 📦

**Goal**: Introduce domain models (dataclasses) to represent business entities. Decouple business logic from database representation.

**Priority**: **MEDIUM** - Improves maintainability  
**Estimated Effort**: 4-6 days  
**Dependencies**: Steps 1-2 complete

### 3.1 Create Domain Models

**Create**: `dmelogic/models.py`

```python
"""
Domain models for DME Logic business entities.

These are pure Python dataclasses representing business concepts,
decoupled from database representation.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal


@dataclass
class Address:
    """Physical address."""
    street1: str
    street2: Optional[str] = None
    city: str = ""
    state: str = ""
    zip_code: str = ""
    
    def __str__(self) -> str:
        """Format address for display."""
        parts = [self.street1]
        if self.street2:
            parts.append(self.street2)
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return "\n".join(parts)


@dataclass
class Patient:
    """Patient domain model."""
    patient_id: int
    first_name: str
    last_name: str
    date_of_birth: date
    address: Address
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Get formatted full name."""
        return f"{self.last_name}, {self.first_name}"
    
    @property
    def age(self) -> int:
        """Calculate age from DOB."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < 
            (self.date_of_birth.month, self.date_of_birth.day)
        )


@dataclass
class Prescriber:
    """Prescriber domain model."""
    prescriber_id: int
    npi: str
    first_name: str
    last_name: str
    specialty: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    address: Optional[Address] = None
    credential: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get formatted full name with credential."""
        name = f"{self.first_name} {self.last_name}"
        if self.credential:
            name += f", {self.credential}"
        return name


@dataclass
class InsurancePolicy:
    """Insurance policy domain model."""
    policy_id: int
    patient_id: int
    payer_name: str
    policy_number: str
    group_number: Optional[str] = None
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    priority: int = 1  # 1=primary, 2=secondary
    
    @property
    def is_active(self) -> bool:
        """Check if policy is currently active."""
        today = date.today()
        if self.effective_date and today < self.effective_date:
            return False
        if self.termination_date and today > self.termination_date:
            return False
        return True


@dataclass
class InventoryItem:
    """Inventory item domain model."""
    item_id: int
    hcpcs_code: str
    description: str
    quantity_on_hand: int
    unit_price: Decimal
    reorder_point: int = 0
    supplier: Optional[str] = None
    
    @property
    def needs_reorder(self) -> bool:
        """Check if item needs to be reordered."""
        return self.quantity_on_hand <= self.reorder_point
    
    @property
    def value(self) -> Decimal:
        """Calculate total inventory value."""
        return Decimal(self.quantity_on_hand) * self.unit_price


@dataclass
class OrderItem:
    """Order line item domain model."""
    order_item_id: Optional[int]
    order_id: int
    hcpcs_code: str
    description: str
    quantity: int
    unit_price: Decimal
    
    @property
    def line_total(self) -> Decimal:
        """Calculate line item total."""
        return Decimal(self.quantity) * self.unit_price


@dataclass
class Order:
    """Order domain model."""
    order_id: int
    patient: Patient
    prescriber: Prescriber
    order_date: date
    items: List[OrderItem] = field(default_factory=list)
    notes: Optional[str] = None
    status: str = 'pending'
    created_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @property
    def is_deleted(self) -> bool:
        """Check if order is soft-deleted."""
        return self.deleted_at is not None
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate order total."""
        return sum(item.line_total for item in self.items)
    
    @property
    def item_count(self) -> int:
        """Get total item count."""
        return sum(item.quantity for item in self.items)


@dataclass
class Refill:
    """Refill domain model."""
    refill_id: int
    order: Order
    refill_date: date
    status: str = 'pending'
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @property
    def days_since_original(self) -> int:
        """Calculate days since original order."""
        delta = self.refill_date - self.order.order_date
        return delta.days
```

---

### 3.2 Add Model Mapping in Repositories

**Pattern**: Repositories return domain models, not raw dicts/rows.

**Example**: `dmelogic/db/patients.py`

```python
from dmelogic.models import Patient, Address

class PatientRepository:
    """Patient data access."""
    
    def get_patient(self, patient_id: int) -> Optional[Patient]:
        """
        Fetch patient by ID.
        
        Returns:
            Patient domain model or None
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    patient_id, first_name, last_name, date_of_birth,
                    street1, street2, city, state, zip_code,
                    phone, email, created_at
                FROM patients
                WHERE patient_id = ?
            """, (patient_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._map_to_model(row)
    
    def _map_to_model(self, row: sqlite3.Row) -> Patient:
        """Convert database row to Patient model."""
        from datetime import date, datetime
        
        return Patient(
            patient_id=row['patient_id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            date_of_birth=date.fromisoformat(row['date_of_birth']),
            address=Address(
                street1=row['street1'],
                street2=row.get('street2'),
                city=row['city'],
                state=row['state'],
                zip_code=row['zip_code']
            ),
            phone=row.get('phone'),
            email=row.get('email'),
            created_at=datetime.fromisoformat(row['created_at']) 
                if row.get('created_at') else None
        )
```

---

### 3.3 Update state_portal_view Mapping

**Current**: Works from raw database rows  
**Goal**: Work from domain models

**File**: Create `dmelogic/services/state_portal_service.py`

```python
"""
State portal integration service.
Maps domain models to state portal format.
"""
from dmelogic.models import Order, Patient, Prescriber

def format_order_for_portal(order: Order) -> dict:
    """
    Format Order model for state portal submission.
    
    Args:
        order: Order domain model with patient, prescriber, items
    
    Returns:
        dict: State portal format
    """
    return {
        'submission_type': 'dme_order',
        'order_id': order.order_id,
        'order_date': order.order_date.isoformat(),
        
        'patient': {
            'name': order.patient.full_name,
            'dob': order.patient.date_of_birth.isoformat(),
            'address': {
                'street': order.patient.address.street1,
                'street2': order.patient.address.street2,
                'city': order.patient.address.city,
                'state': order.patient.address.state,
                'zip': order.patient.address.zip_code
            },
            'phone': order.patient.phone
        },
        
        'prescriber': {
            'npi': order.prescriber.npi,
            'name': order.prescriber.full_name,
            'phone': order.prescriber.phone,
            'fax': order.prescriber.fax
        },
        
        'line_items': [
            {
                'hcpcs': item.hcpcs_code,
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.line_total)
            }
            for item in order.items
        ],
        
        'totals': {
            'item_count': order.item_count,
            'total_amount': float(order.total_amount)
        }
    }
```

---

### Step 3 Checklist

- [ ] **Create dmelogic/models.py** - Define all domain models
- [ ] **Update PatientRepository** - Return Patient models
- [ ] **Update PrescriberRepository** - Return Prescriber models
- [ ] **Update OrderRepository** - Return Order models with items
- [ ] **Update InventoryRepository** - Return InventoryItem models
- [ ] **Update InsuranceRepository** - Return InsurancePolicy models
- [ ] **Create state_portal_service** - Work from domain models
- [ ] **Update UI code** - Use model properties instead of dict keys
- [ ] **Add model validation** - Validate business rules in models
- [ ] **Add unit tests** - Test model properties and methods
- [ ] **Document models** - Add to `ARCHITECTURE.md`

---

## Step 4: Complete UI Unification 🎨

**Goal**: Apply unified theme and modern layout to all tabs and dialogs. Create consistent user experience.

**Priority**: **MEDIUM** - UX improvement  
**Estimated Effort**: 5-7 days  
**Dependencies**: Steps 1-3 complete

### 4.1 Apply Global Theme

**Files**:
- `assets/theme.qss` (Light theme)
- `assets/dark.qss` (Dark theme)

**Current**: Theme partially applied  
**Goal**: 100% coverage of all widgets

**Enhancement Areas**:

```css
/* QTableWidget - enhance current styles */
QTableWidget {
    background-color: #2b2b2b;
    alternate-row-color: #323232;
    selection-background-color: #0d47a1;
    gridline-color: #3d3d3d;
}

QTableWidget::item:hover {
    background-color: #3d3d3d;
}

QTableWidget::item:selected {
    background-color: #1565c0;
}

/* QHeaderView - add consistent header styling */
QHeaderView::section {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 8px;
    border: 1px solid #3d3d3d;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #2d2d2d;
}

/* QTreeWidget - for hierarchical data */
QTreeWidget {
    background-color: #2b2b2b;
    selection-background-color: #0d47a1;
    border: 1px solid #3d3d3d;
}

QTreeWidget::item:hover {
    background-color: #3d3d3d;
}

QTreeWidget::item:selected {
    background-color: #1565c0;
}

/* QPushButton - enhance current buttons */
QPushButton {
    background-color: #0d47a1;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1565c0;
}

QPushButton:pressed {
    background-color: #003c8f;
}

QPushButton:disabled {
    background-color: #424242;
    color: #757575;
}

/* QPushButton[danger="true"] - for delete actions */
QPushButton[danger="true"] {
    background-color: #c62828;
}

QPushButton[danger="true"]:hover {
    background-color: #d32f2f;
}

/* QPushButton[secondary="true"] - for cancel actions */
QPushButton[secondary="true"] {
    background-color: #424242;
}

QPushButton[secondary="true"]:hover {
    background-color: #616161;
}

/* QComboBox - enhance dropdowns */
QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px;
    color: white;
}

QComboBox:hover {
    border-color: #0d47a1;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    selection-background-color: #0d47a1;
}

/* QLineEdit - enhance text inputs */
QLineEdit {
    background-color: #2b2b2b;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px;
    color: white;
}

QLineEdit:focus {
    border-color: #0d47a1;
}

QLineEdit:disabled {
    background-color: #1e1e1e;
    color: #757575;
}

/* QTextEdit - for notes/descriptions */
QTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 8px;
    color: white;
}

QTextEdit:focus {
    border-color: #0d47a1;
}

/* QScrollBar - consistent scrollbars */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #616161;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
}

QScrollBar::handle:horizontal {
    background-color: #424242;
    border-radius: 6px;
    min-width: 30px;
}

/* QStatusBar - bottom status bar */
QStatusBar {
    background-color: #1e1e1e;
    color: #b0b0b0;
    border-top: 1px solid #3d3d3d;
}
```

---

### 4.2 Refactor Tabs to Modern Layout

**Current**: Mix of old and new layouts  
**Goal**: All tabs use consistent modern layout

**Pattern**: Use `ModernLayout` from `dmelogic/ui/layout.py`

**Example Refactor** - Patients Tab:

```python
from dmelogic.ui.layout import ModernLayout, create_section

class PatientsTab(QWidget):
    """Modern patients tab."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize modern UI layout."""
        layout = ModernLayout()
        
        # Header section
        header = create_section(
            "Patients",
            "Manage patient records",
            icon="👤"
        )
        layout.add_section(header)
        
        # Search section
        search_section = self._create_search_section()
        layout.add_section(search_section)
        
        # Table section
        table_section = self._create_table_section()
        layout.add_section(table_section)
        
        # Action buttons
        button_row = self._create_action_buttons()
        layout.add_widget(button_row)
        
        self.setLayout(layout)
    
    def _create_search_section(self) -> QWidget:
        """Create search controls."""
        section = QWidget()
        layout = QHBoxLayout(section)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search patients...")
        self.search_input.textChanged.connect(self.filter_table)
        layout.addWidget(self.search_input)
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.perform_search)
        layout.addWidget(search_btn)
        
        return section
    
    def _create_table_section(self) -> QTableWidget:
        """Create patients table."""
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Last Name", "First Name", "DOB",
            "Phone", "Address", "Actions"
        ])
        
        # Configure table
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        return self.table
    
    def _create_action_buttons(self) -> QWidget:
        """Create action button row."""
        button_row = QWidget()
        layout = QHBoxLayout(button_row)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Add button
        add_btn = QPushButton("➕ Add Patient")
        add_btn.clicked.connect(self.add_patient)
        layout.addWidget(add_btn)
        
        # Edit button
        edit_btn = QPushButton("✏️ Edit Patient")
        edit_btn.clicked.connect(self.edit_patient)
        layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete Patient")
        delete_btn.setProperty("danger", True)
        delete_btn.clicked.connect(self.delete_patient)
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        return button_row
```

**Tabs to Refactor**:
- [ ] Patients Tab
- [ ] Orders Tab
- [ ] Inventory Tab
- [ ] Prescribers Tab
- [ ] Insurance Tab
- [ ] Reports Tab

---

### 4.3 Modernize Dialogs

**Apply consistent dialog styling:**

```python
from dmelogic.ui.dialogs import ModernDialog

class PatientDialog(ModernDialog):
    """Modern patient edit dialog."""
    
    def __init__(self, patient_id: Optional[int] = None):
        super().__init__(title="Edit Patient" if patient_id else "Add Patient")
        self.patient_id = patient_id
        self.init_ui()
    
    def init_ui(self):
        """Build form UI."""
        layout = QFormLayout()
        
        # Personal info section
        layout.addRow(self.create_section_header("Personal Information"))
        
        self.first_name = QLineEdit()
        layout.addRow("First Name:", self.first_name)
        
        self.last_name = QLineEdit()
        layout.addRow("Last Name:", self.last_name)
        
        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        layout.addRow("Date of Birth:", self.dob)
        
        # Address section
        layout.addRow(self.create_section_header("Address"))
        
        self.street1 = QLineEdit()
        layout.addRow("Street:", self.street1)
        
        self.city = QLineEdit()
        layout.addRow("City:", self.city)
        
        # ... etc
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
```

---

### Step 4 Checklist

- [ ] **Enhance theme.qss** - Add missing widget styles
- [ ] **Enhance dark.qss** - Match light theme improvements
- [ ] **Refactor Patients tab** - Use ModernLayout
- [ ] **Refactor Orders tab** - Use ModernLayout
- [ ] **Refactor Inventory tab** - Use ModernLayout
- [ ] **Refactor Prescribers tab** - Use ModernLayout
- [ ] **Refactor Insurance tab** - Use ModernLayout
- [ ] **Refactor Reports tab** - Use ModernLayout
- [ ] **Modernize all dialogs** - Use ModernDialog base
- [ ] **Add theme switcher** - Toggle light/dark in UI
- [ ] **Test on different displays** - Verify scaling/DPI
- [ ] **Document UI patterns** - Update UI_COMPONENTS.md

---

## Step 5: Billing & CMS-1500 Preparation 💰

**Goal**: Build claim generation infrastructure for CMS-1500 forms and electronic submissions.

**Priority**: **LOW** (Future feature)  
**Estimated Effort**: 10-15 days  
**Dependencies**: Steps 1-4 complete

### 5.1 CMS-1500 Mapping Service

**Create**: `dmelogic/services/cms1500_service.py`

```python
"""
CMS-1500 claim form generation service.

Maps order data to CMS-1500 format (boxes 1-33).
"""
from dmelogic.models import Order, Patient, Prescriber, InsurancePolicy
from typing import Dict, Any
from datetime import date


class CMS1500Service:
    """Generate CMS-1500 claim forms from orders."""
    
    def generate_claim(
        self,
        order: Order,
        insurance: InsurancePolicy,
        diagnosis_codes: list[str],
        place_of_service: str = '12'  # Patient's home
    ) -> Dict[str, Any]:
        """
        Generate CMS-1500 claim from order.
        
        Args:
            order: Order with patient, prescriber, items
            insurance: Insurance policy information
            diagnosis_codes: List of ICD-10 codes
            place_of_service: POS code (default: 12 = home)
        
        Returns:
            dict: CMS-1500 field mapping
        """
        return {
            # Carrier information (boxes 1-13)
            'box_1': self._get_insurance_type(insurance),
            'box_1a': insurance.policy_number,
            'box_2': order.patient.full_name.upper(),
            'box_3': self._format_date(order.patient.date_of_birth),
            'box_4': '',  # Insured's name (if different)
            'box_5': str(order.patient.address),
            'box_6': 'SELF',  # Patient relationship
            'box_7': '',  # Insured's address (if different)
            'box_8': 'SINGLE',  # Patient status
            'box_9': '',  # Other insured's name
            'box_9a': '',  # Other insured's policy
            'box_9d': '',  # Insurance plan name
            'box_10a': 'X',  # Employment related? No
            'box_10b': '',  # Auto accident?
            'box_10c': '',  # Other accident?
            'box_10d': '',  # Claim codes
            'box_11': insurance.group_number or '',
            'box_11a': self._format_date(insurance.effective_date),
            'box_11b': '',  # Other claim ID
            'box_11c': insurance.payer_name,
            'box_11d': 'NO' if insurance.priority == 1 else 'YES',
            'box_12': 'SOF',  # Patient signature on file
            'box_13': 'SOF',  # Insured signature on file
            
            # Dates and diagnoses (boxes 14-23)
            'box_14': self._format_date(order.order_date),
            'box_15': '',  # Other date
            'box_16': '',  # Dates unable to work
            'box_17': order.prescriber.full_name,
            'box_17a': '',  # Prescriber ID qualifier
            'box_17b': order.prescriber.npi,
            'box_18': '',  # Hospitalization dates
            'box_19': '',  # Additional claim info
            'box_20': 'NO',  # Outside lab
            'box_21': self._format_diagnosis_codes(diagnosis_codes),
            'box_22': '',  # Resubmission code
            'box_23': '',  # Prior authorization
            
            # Service lines (boxes 24A-24J)
            'service_lines': self._map_service_lines(
                order, place_of_service, diagnosis_codes
            ),
            
            # Provider information (boxes 25-33)
            'box_25': '',  # Federal tax ID
            'box_26': str(order.order_id),  # Patient account number
            'box_27': 'X',  # Accept assignment
            'box_28': str(order.total_amount),  # Total charge
            'box_29': '0.00',  # Amount paid
            'box_30': '',  # Reserved
            'box_31': date.today().strftime('%m/%d/%Y'),  # Signature date
            'box_32': 'SAME',  # Service facility (patient's home)
            'box_32a': '',  # Service facility NPI
            'box_33': order.prescriber.phone,  # Billing provider phone
            'box_33a': order.prescriber.npi,  # Billing provider NPI
        }
    
    def _map_service_lines(
        self,
        order: Order,
        place_of_service: str,
        diagnosis_codes: list[str]
    ) -> list[dict]:
        """Map order items to service lines (box 24)."""
        lines = []
        
        for idx, item in enumerate(order.items, 1):
            lines.append({
                '24a_date_from': self._format_date(order.order_date),
                '24a_date_to': self._format_date(order.order_date),
                '24b_place': place_of_service,
                '24c_emg': '',  # Emergency
                '24d_procedures': item.hcpcs_code,
                '24d_modifiers': '',  # HCPCS modifiers
                '24e_diagnosis': '1' if diagnosis_codes else '',
                '24f_charges': str(item.line_total),
                '24g_units': str(item.quantity),
                '24h_epsdt': '',  # Family plan
                '24i_id_qual': '',  # ID qualifier
                '24j_rendering_npi': order.prescriber.npi
            })
        
        return lines
    
    def _format_date(self, d: date) -> str:
        """Format date as MM/DD/YYYY."""
        return d.strftime('%m/%d/%Y') if d else ''
    
    def _get_insurance_type(self, insurance: InsurancePolicy) -> str:
        """Determine insurance type for box 1."""
        # Logic to determine Medicare, Medicaid, etc.
        payer_lower = insurance.payer_name.lower()
        if 'medicare' in payer_lower:
            return 'MEDICARE'
        elif 'medicaid' in payer_lower:
            return 'MEDICAID'
        else:
            return 'OTHER'
    
    def _format_diagnosis_codes(self, codes: list[str]) -> dict:
        """Format diagnosis codes for box 21."""
        return {
            'a': codes[0] if len(codes) > 0 else '',
            'b': codes[1] if len(codes) > 1 else '',
            'c': codes[2] if len(codes) > 2 else '',
            'd': codes[3] if len(codes) > 3 else '',
        }
```

---

### 5.2 Reuse for State Portal

**Update**: `dmelogic/services/state_portal_service.py`

```python
def submit_to_portal(order: Order, insurance: InsurancePolicy) -> dict:
    """
    Submit order to state portal using CMS-1500 mapping.
    
    Args:
        order: Order with all related data
        insurance: Insurance policy
    
    Returns:
        dict: Submission result
    """
    from dmelogic.services.cms1500_service import CMS1500Service
    
    # Generate CMS-1500 claim
    cms_service = CMS1500Service()
    claim = cms_service.generate_claim(
        order=order,
        insurance=insurance,
        diagnosis_codes=['E11.9']  # Example ICD-10
    )
    
    # Convert to portal format
    portal_data = {
        'submission_id': f"SUB-{order.order_id}-{date.today().strftime('%Y%m%d')}",
        'claim_data': claim,
        'patient': {
            'id': order.patient.patient_id,
            'name': order.patient.full_name,
            'dob': order.patient.date_of_birth.isoformat()
        },
        'provider': {
            'npi': order.prescriber.npi,
            'name': order.prescriber.full_name
        }
    }
    
    # Submit to portal API
    # ... implementation
    
    return portal_data
```

---

### 5.3 Print CMS-1500

**Create**: `dmelogic/services/cms1500_printer.py`

```python
"""
CMS-1500 form printer using ReportLab or PyQt printing.
"""
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtCore import QRectF


class CMS1500Printer:
    """Print CMS-1500 forms."""
    
    def print_claim(self, claim: dict) -> bool:
        """
        Print CMS-1500 form.
        
        Args:
            claim: CMS-1500 field mapping from CMS1500Service
        
        Returns:
            True if printed successfully
        """
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer)
        
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter(printer)
            self._draw_cms1500(painter, claim, printer)
            painter.end()
            return True
        
        return False
    
    def _draw_cms1500(self, painter: QPainter, claim: dict, printer: QPrinter):
        """Draw CMS-1500 form on painter."""
        # Form dimensions (CMS-1500 is standardized)
        page_width = printer.pageRect().width()
        page_height = printer.pageRect().height()
        
        # Fonts
        regular_font = QFont("Courier New", 10)
        bold_font = QFont("Courier New", 10, QFont.Weight.Bold)
        
        painter.setFont(regular_font)
        
        # Draw header
        painter.setFont(bold_font)
        painter.drawText(100, 100, "HEALTH INSURANCE CLAIM FORM")
        
        # Draw box 1 (insurance type)
        painter.setFont(regular_font)
        self._draw_box(painter, 100, 150, 200, 50, f"Box 1: {claim['box_1']}")
        
        # ... draw all boxes (1-33) at correct positions
        # This requires precise positioning to match CMS-1500 template
        
        # Box 2: Patient name
        self._draw_box(painter, 100, 220, 400, 50, f"Patient: {claim['box_2']}")
        
        # ... continue for all boxes
    
    def _draw_box(self, painter: QPainter, x: int, y: int, 
                  width: int, height: int, text: str):
        """Draw a form box with text."""
        rect = QRectF(x, y, width, height)
        painter.drawRect(rect)
        painter.drawText(rect, text)
```

---

### Step 5 Checklist

- [ ] **Create CMS1500Service** - Map orders to CMS-1500 format
- [ ] **Add diagnosis code support** - ICD-10 code management
- [ ] **Create CMS1500Printer** - Print physical forms
- [ ] **Update state_portal_service** - Reuse CMS-1500 mapping
- [ ] **Add claim validation** - Validate required fields
- [ ] **Create claims repository** - Store submitted claims
- [ ] **Add claim tracking UI** - View claim status
- [ ] **Electronic submission** - Submit to clearinghouse
- [ ] **Add unit tests** - Test claim generation
- [ ] **Document billing process** - Add BILLING.md

---

## Implementation Timeline

### Sprint 1 (Week 1-2): Clean DB Usage
- Day 1-2: Audit all `sqlite3.connect()` calls
- Day 3-5: Refactor MainWindow.create_order_from_wizard
- Day 6-7: Fix deleted orders dialog
- Day 8-10: Fix all `.get()` on sqlite3.Row bugs

### Sprint 2 (Week 3-4): Unit of Work
- Day 1-3: Implement UnitOfWork class
- Day 4-6: Update all repositories with `conn` parameter
- Day 7-9: Refactor order workflows
- Day 10-12: Refactor refill workflows
- Day 13-14: Add unit tests

### Sprint 3 (Week 5-6): Domain Models
- Day 1-3: Create all domain models in models.py
- Day 4-7: Add model mapping in repositories
- Day 8-10: Update state_portal_service
- Day 11-12: Update UI code to use models
- Day 13-14: Add unit tests

### Sprint 4 (Week 7-8): UI Unification
- Day 1-2: Enhance theme.qss and dark.qss
- Day 3-5: Refactor Patients/Orders tabs
- Day 6-8: Refactor Inventory/Prescribers tabs
- Day 9-11: Modernize all dialogs
- Day 12-14: Testing and polish

### Sprint 5 (Week 9-12): Billing (Optional)
- Week 9: CMS-1500 service and mapping
- Week 10: Printing and validation
- Week 11: State portal integration
- Week 12: Testing and documentation

---

## Success Metrics

### Code Quality
- [ ] Zero direct `sqlite3.connect()` in UI layer
- [ ] All database operations use repositories or UoW
- [ ] All functions return domain models (not raw dicts)
- [ ] 80%+ test coverage on business logic
- [ ] No `.get()` calls on sqlite3.Row objects

### Architecture
- [ ] Clear separation: UI → Services → Repositories → Database
- [ ] Transactional workflows using UnitOfWork
- [ ] Domain models represent all business entities
- [ ] State portal and billing use same underlying models

### User Experience
- [ ] Consistent dark theme across all tabs
- [ ] Modern layout on all screens
- [ ] Clear error messages
- [ ] Fast and responsive UI

### Business Features
- [ ] Complete order lifecycle (create → refill → delete → audit)
- [ ] CMS-1500 claim generation
- [ ] State portal submission
- [ ] Claim tracking

---

## Risk Mitigation

### Technical Risks

**Risk**: Breaking existing functionality during refactoring  
**Mitigation**: 
- Write tests before refactoring
- Refactor incrementally (one file at a time)
- Keep old code commented until new code verified

**Risk**: UnitOfWork performance overhead  
**Mitigation**:
- Use UoW only for multi-repository operations
- Keep simple queries as single repository calls
- Profile before/after to measure impact

**Risk**: Model mapping complexity  
**Mitigation**:
- Start with simple models (Patient, Prescriber)
- Add complexity gradually (Order with items)
- Use dataclasses for automatic __init__ and __repr__

### Schedule Risks

**Risk**: Underestimating refactoring effort  
**Mitigation**:
- Add 25% buffer to all estimates
- Prioritize Step 1 (critical foundation)
- Steps 4-5 can be deferred if needed

**Risk**: Scope creep  
**Mitigation**:
- Stick to roadmap steps
- Document future enhancements separately
- Get signoff before adding features

---

## Conclusion

This roadmap takes DME Logic from its current state to a production-ready system with:

✅ **Clean Architecture**: Repositories, services, domain models  
✅ **Transactional Workflows**: UnitOfWork for complex operations  
✅ **Consistent UI**: Unified theme and modern layouts  
✅ **Business Features**: Billing, claims, state portal  

**Critical Path**: Steps 1-2 are foundational. Complete these before moving to Steps 3-5.

**Next Action**: Start Step 1 by auditing all direct database connections in UI layer.

---

## Resources

**Documentation**:
- `ARCHITECTURE.md` - Current architecture overview
- `DATABASE.md` - Database schema and migrations
- `UI_COMPONENTS.md` - UI component library
- `OCR_EXTERNAL_SERVICES.md` - OCR and NPI services

**Code References**:
- `dmelogic/db/base.py` - Connection management
- `dmelogic/workflows/order_workflow.py` - Order workflows
- `dmelogic/ui/layout.py` - Modern UI components
- `assets/dark.qss` - Dark theme stylesheet

**Testing**:
- `tests/test_repositories.py` - Repository tests
- `tests/test_workflows.py` - Workflow tests
- `tests/test_ui_components.py` - UI tests

---

*Roadmap created: December 5, 2025*  
*Target completion: Q1 2026 (Steps 1-4), Q2 2026 (Step 5)*
