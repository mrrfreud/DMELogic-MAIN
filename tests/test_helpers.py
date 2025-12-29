"""
Test helpers for DME Logic unit tests.

Provides:
- In-memory SQLite database setup
- Schema initialization for all tables
- Test fixtures and sample data
- Cleanup utilities
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


# ============================================================================
# In-Memory Database Setup
# ============================================================================

def create_in_memory_db() -> sqlite3.Connection:
    """
    Create an in-memory SQLite database connection.
    
    Returns:
        sqlite3.Connection: In-memory database connection
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def in_memory_db():
    """
    Context manager for in-memory database.
    
    Usage:
        with in_memory_db() as conn:
            cursor = conn.cursor()
            # ... run tests
    """
    conn = create_in_memory_db()
    try:
        yield conn
    finally:
        conn.close()


# ============================================================================
# Schema Initialization
# ============================================================================

def init_patients_schema(conn: sqlite3.Connection) -> None:
    """Initialize patients.db schema in memory."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            ssn TEXT,
            phone TEXT,
            secondary_contact TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            primary_insurance TEXT,
            policy_number TEXT,
            group_number TEXT,
            secondary_insurance TEXT,
            secondary_insurance_id TEXT,
            primary_insurance_id TEXT,
            notes TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def init_prescribers_schema(conn: sqlite3.Connection) -> None:
    """Initialize prescribers.db schema in memory."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            title TEXT,
            npi_number TEXT UNIQUE,
            license_number TEXT,
            specialty TEXT,
            phone TEXT,
            fax TEXT,
            email TEXT,
            practice_name TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            dea_number TEXT,
            tax_id TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Active',
            notes TEXT
        )
    """)
    conn.commit()


def init_insurance_schema(conn: sqlite3.Connection) -> None:
    """Initialize insurance_names.db schema in memory."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insurance_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def init_inventory_schema(conn: sqlite3.Connection) -> None:
    """Initialize inventory.db schema in memory."""
    cursor = conn.cursor()
    
    # Inventory items
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hcpcs_code TEXT,
            description TEXT NOT NULL,
            category TEXT,
            cost REAL,
            retail_price REAL,
            brand TEXT,
            supplier TEXT,
            stock_quantity INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 0,
            item_number TEXT,
            notes TEXT,
            created_date TEXT,
            updated_date TEXT,
            last_used_date TEXT,
            last_restocked_date TEXT
        )
    """)
    
    # Inventory transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            transaction_type TEXT,
            quantity INTEGER,
            reference_id TEXT,
            transaction_date TEXT,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES inventory (item_id)
        )
    """)
    
    # Categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            active INTEGER DEFAULT 1,
            sort_order INTEGER,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()


def init_orders_schema(conn: sqlite3.Connection) -> None:
    """Initialize orders.db schema in memory."""
    cursor = conn.cursor()
    
    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rx_date TEXT NOT NULL,
            order_date TEXT NOT NULL,
            patient_last_name TEXT NOT NULL,
            patient_first_name TEXT NOT NULL,
            patient_dob TEXT,
            patient_address TEXT,
            patient_phone TEXT,
            patient_id INTEGER,
            patient_name TEXT,
            patient_secondary_contact TEXT,
            icd_code_1 TEXT,
            icd_code_2 TEXT,
            icd_code_3 TEXT,
            icd_code_4 TEXT,
            icd_code_5 TEXT,
            prescriber_name TEXT NOT NULL,
            prescriber_npi TEXT NOT NULL,
            prescriber_id INTEGER,
            primary_insurance TEXT,
            primary_insurance_id TEXT,
            secondary_insurance TEXT,
            secondary_insurance_id TEXT,
            billing_selection TEXT,
            order_status TEXT DEFAULT 'Pending',
            delivery_date TEXT,
            tracking_number TEXT,
            parent_order_id INTEGER,
            refill_number INTEGER DEFAULT 0,
            billed INTEGER DEFAULT 0,
            paid INTEGER DEFAULT 0,
            paid_date TEXT,
            notes TEXT,
            is_pickup INTEGER DEFAULT 0,
            pickup_date TEXT,
            doctor_directions TEXT,
            attached_rx_files TEXT,
            attached_signed_ticket_files TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Order items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            rx_no TEXT,
            hcpcs_code TEXT,
            description TEXT,
            item_number TEXT,
            refills TEXT,
            day_supply TEXT,
            qty TEXT,
            cost_ea TEXT,
            total TEXT,
            pa_number TEXT,
            directions TEXT,
            last_filled_date TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    """)
    
    # RX control table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rx_control (
            last_rx_no INTEGER
        )
    """)
    
    # RX log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rx_log (
            rx_no INTEGER PRIMARY KEY,
            order_id INTEGER,
            order_item_id INTEGER,
            action TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        )
    """)
    
    conn.commit()


def init_all_schemas(conn: sqlite3.Connection) -> None:
    """
    Initialize all database schemas in a single connection.
    Useful for testing cross-database operations.
    """
    init_patients_schema(conn)
    init_prescribers_schema(conn)
    init_insurance_schema(conn)
    init_inventory_schema(conn)
    init_orders_schema(conn)


# ============================================================================
# Test Fixtures - Sample Data
# ============================================================================

def create_sample_patient(conn: sqlite3.Connection, **overrides: Any) -> int:
    """
    Create a sample patient record and return the patient ID.
    
    Args:
        conn: Database connection
        **overrides: Override default values
        
    Returns:
        int: Patient ID
    """
    defaults = {
        "last_name": "Smith",
        "first_name": "John",
        "dob": "1980-05-15",
        "gender": "M",
        "ssn": "123-45-6789",
        "phone": "555-1234",
        "address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "90210",
        "primary_insurance": "Blue Cross",
        "policy_number": "BC123456",
        "group_number": "GRP001",
    }
    defaults.update(overrides)
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patients (
            last_name, first_name, dob, gender, ssn, phone,
            address, city, state, zip_code,
            primary_insurance, policy_number, group_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        defaults["last_name"], defaults["first_name"], defaults["dob"],
        defaults["gender"], defaults["ssn"], defaults["phone"],
        defaults["address"], defaults["city"], defaults["state"], defaults["zip_code"],
        defaults["primary_insurance"], defaults["policy_number"], defaults["group_number"]
    ))
    conn.commit()
    return cursor.lastrowid


def create_sample_prescriber(conn: sqlite3.Connection, **overrides: Any) -> int:
    """
    Create a sample prescriber record and return the prescriber ID.
    
    Args:
        conn: Database connection
        **overrides: Override default values
        
    Returns:
        int: Prescriber ID
    """
    defaults = {
        "first_name": "Jane",
        "last_name": "Doe",
        "title": "MD",
        "npi_number": "1234567890",
        "specialty": "General Practice",
        "phone": "555-5678",
        "practice_name": "Doe Medical Group",
        "status": "Active",
    }
    defaults.update(overrides)
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prescribers (
            first_name, last_name, title, npi_number, specialty, phone, practice_name, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        defaults["first_name"], defaults["last_name"], defaults["title"],
        defaults["npi_number"], defaults["specialty"], defaults["phone"],
        defaults["practice_name"], defaults["status"]
    ))
    conn.commit()
    return cursor.lastrowid


def create_sample_insurance(conn: sqlite3.Connection, name: str = "Blue Cross") -> int:
    """
    Create a sample insurance company and return the insurance ID.
    
    Args:
        conn: Database connection
        name: Insurance company name
        
    Returns:
        int: Insurance ID
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO insurance_names (name, usage_count) VALUES (?, ?)
    """, (name, 1))
    conn.commit()
    return cursor.lastrowid


def create_sample_inventory_item(conn: sqlite3.Connection, **overrides: Any) -> int:
    """
    Create a sample inventory item and return the item ID.
    
    Args:
        conn: Database connection
        **overrides: Override default values
        
    Returns:
        int: Item ID
    """
    defaults = {
        "hcpcs_code": "E0143",
        "description": "Walker, folding, wheeled, adjustable",
        "category": "Walkers",
        "cost": 45.00,
        "retail_price": 89.99,
        "brand": "Drive Medical",
        "supplier": "DME Wholesale",
        "stock_quantity": 10,
        "reorder_level": 3,
    }
    defaults.update(overrides)
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO inventory (
            hcpcs_code, description, category, cost, retail_price,
            brand, supplier, stock_quantity, reorder_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        defaults["hcpcs_code"], defaults["description"], defaults["category"],
        defaults["cost"], defaults["retail_price"], defaults["brand"],
        defaults["supplier"], defaults["stock_quantity"], defaults["reorder_level"]
    ))
    conn.commit()
    return cursor.lastrowid


def create_sample_order(conn: sqlite3.Connection, **overrides: Any) -> int:
    """
    Create a sample order and return the order ID.
    
    Args:
        conn: Database connection
        **overrides: Override default values
        
    Returns:
        int: Order ID
    """
    defaults = {
        "rx_date": date.today().isoformat(),
        "order_date": date.today().isoformat(),
        "patient_last_name": "Smith",
        "patient_first_name": "John",
        "patient_dob": "1980-05-15",
        "prescriber_name": "Dr. Jane Doe",
        "prescriber_npi": "1234567890",
        "primary_insurance": "Blue Cross",
        "billing_selection": "Primary Insurance",
        "order_status": "Pending",
        "icd_code_1": "M54.5",
    }
    defaults.update(overrides)
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (
            rx_date, order_date, patient_last_name, patient_first_name, patient_dob,
            prescriber_name, prescriber_npi, primary_insurance, billing_selection,
            order_status, icd_code_1
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        defaults["rx_date"], defaults["order_date"],
        defaults["patient_last_name"], defaults["patient_first_name"], defaults["patient_dob"],
        defaults["prescriber_name"], defaults["prescriber_npi"],
        defaults["primary_insurance"], defaults["billing_selection"],
        defaults["order_status"], defaults["icd_code_1"]
    ))
    conn.commit()
    return cursor.lastrowid


def create_sample_order_item(conn: sqlite3.Connection, order_id: int, **overrides: Any) -> int:
    """
    Create a sample order item and return the item ID.
    
    Args:
        conn: Database connection
        order_id: Parent order ID
        **overrides: Override default values
        
    Returns:
        int: Order item ID
    """
    defaults = {
        "rx_no": "1001",
        "hcpcs_code": "E0143",
        "description": "Walker, folding, wheeled, adjustable",
        "qty": "1",
        "day_supply": "99",
        "refills": "3",
        "cost_ea": "45.00",
        "total": "45.00",
        "last_filled_date": None,
    }
    defaults.update(overrides)
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO order_items (
            order_id, rx_no, hcpcs_code, description, qty, day_supply, refills, cost_ea, total
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id, defaults["rx_no"], defaults["hcpcs_code"], defaults["description"],
        defaults["qty"], defaults["day_supply"], defaults["refills"],
        defaults["cost_ea"], defaults["total"]
    ))
    conn.commit()
    item_id = cursor.lastrowid

    # Apply optional last_filled_date if provided by tests
    if defaults["last_filled_date"] is not None:
        cursor.execute(
            "UPDATE order_items SET last_filled_date = ? WHERE id = ?",
            (defaults["last_filled_date"], item_id),
        )
        conn.commit()

    return item_id


# ============================================================================
# Mock Connection Provider
# ============================================================================

class MockConnectionProvider:
    """
    Mock connection provider for testing repository functions.
    
    Returns a non-closing wrapper around the in-memory connection.
    This prevents repository functions from closing the connection,
    allowing multiple operations on the same in-memory database.
    
    Usage:
        with in_memory_db() as conn:
            init_patients_schema(conn)
            provider = MockConnectionProvider(conn)
            
            # Monkey-patch the repository's get_connection
            import dmelogic.db.patients as patients_module
            patients_module.get_connection = provider.get_connection
            
            # Now repository functions use the in-memory DB
            patients = patients_module.fetch_all_patients()
    """
    
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
    
    def get_connection(self, db_name: str, folder_path: Optional[str] = None) -> "NonClosingConnection":
        """Return a non-closing wrapper around the in-memory connection."""
        return NonClosingConnection(self.conn)


class NonClosingConnection:
    """
    Wrapper around a sqlite3.Connection that ignores close() calls.
    
    This allows repository functions to call conn.close() without
    actually closing the underlying in-memory database.
    """
    
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
    
    def __getattr__(self, name: str):
        """Forward all attribute access to the real connection."""
        return getattr(self._conn, name)
    
    def close(self) -> None:
        """Ignore close() calls - we'll close when the test is done."""
        pass


# ============================================================================
# Test Data Validation Helpers
# ============================================================================

def assert_patient_fields(row: sqlite3.Row, expected: Dict[str, Any]) -> None:
    """Assert that patient row matches expected fields."""
    for key, value in expected.items():
        assert row[key] == value, f"Patient field {key}: expected {value}, got {row[key]}"


def assert_order_fields(row: sqlite3.Row, expected: Dict[str, Any]) -> None:
    """Assert that order row matches expected fields."""
    for key, value in expected.items():
        assert row[key] == value, f"Order field {key}: expected {value}, got {row[key]}"


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    """Count rows in a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]
