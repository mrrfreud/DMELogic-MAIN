"""
Unit tests for repository functions using in-memory SQLite databases.

Tests all CRUD operations for:
- Patients (patients.py)
- Prescribers (prescribers.py)
- Insurance (insurance.py)
- Inventory (inventory.py)
- Orders (orders.py)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import date, datetime
from tests.test_helpers import (
    in_memory_db,
    init_patients_schema,
    init_prescribers_schema,
    init_insurance_schema,
    init_inventory_schema,
    init_orders_schema,
    create_sample_patient,
    create_sample_prescriber,
    create_sample_insurance,
    create_sample_inventory_item,
    create_sample_order,
    create_sample_order_item,
    MockConnectionProvider,
    count_rows,
)


# ============================================================================
# Test Patients Repository
# ============================================================================

def test_patients_crud():
    """Test patient CRUD operations."""
    print("\n" + "=" * 70)
    print("TEST: Patients Repository")
    print("=" * 70)
    
    with in_memory_db() as conn:
        init_patients_schema(conn)
        
        # Mock get_connection to use in-memory DB
        import dmelogic.db.patients as patients
        from dmelogic.db.converters import row_to_patient
        
        original_get_connection = patients.get_connection
        provider = MockConnectionProvider(conn)
        patients.get_connection = provider.get_connection
        
        try:
            # Test 1: fetch_all_patients (empty)
            all_patients = patients.fetch_all_patients()
            assert len(all_patients) == 0, "Should start with no patients"
            print("✓ fetch_all_patients() empty database")
            
            # Test 2: Create sample patients
            patient1_id = create_sample_patient(conn, last_name="Smith", first_name="John")
            patient2_id = create_sample_patient(conn, last_name="Doe", first_name="Jane")
            patient3_id = create_sample_patient(conn, last_name="Anderson", first_name="Bob")
            print(f"✓ Created 3 sample patients (IDs: {patient1_id}, {patient2_id}, {patient3_id})")
            
            # Test 3: fetch_all_patients (with data)
            all_patients = patients.fetch_all_patients()
            assert len(all_patients) == 3, f"Expected 3 patients, got {len(all_patients)}"
            # Check sort order (by last_name)
            assert all_patients[0].last_name == "Anderson", "First should be Anderson"
            assert all_patients[1].last_name == "Doe", "Second should be Doe"
            assert all_patients[2].last_name == "Smith", "Third should be Smith"
            print("✓ fetch_all_patients() returns sorted results")
            
            # Test 4: fetch_patient_by_id
            patient = patients.fetch_patient_by_id(patient1_id)
            assert patient is not None, "Patient should exist"
            assert patient.last_name == "Smith", "Last name should match"
            assert patient.first_name == "John", "First name should match"
            # DOB is converted to date object
            assert str(patient.dob) == "1980-05-15", "DOB should match"
            print(f"✓ fetch_patient_by_id({patient1_id}) returns correct data")
            
            # Test 5: fetch_patient_by_id (not found)
            patient = patients.fetch_patient_by_id(9999)
            assert patient is None, "Non-existent patient should return None"
            print("✓ fetch_patient_by_id(9999) returns None")
            
            # Test 6: fetch_patient_insurance (with DOB)
            insurance = patients.fetch_patient_insurance("Smith", "John", "1980-05-15")
            assert insurance is not None, "Insurance should be found"
            assert insurance.primary_insurance == "Blue Cross", "Primary insurance should match"
            assert insurance.policy_number == "BC123456", "Policy number should match"
            print("✓ fetch_patient_insurance() with DOB")
            
            # Test 7: fetch_patient_insurance (without DOB)
            insurance = patients.fetch_patient_insurance("Doe", "Jane")
            assert insurance is not None, "Insurance should be found without DOB"
            assert insurance.primary_insurance == "Blue Cross", "Primary insurance should match"
            print("✓ fetch_patient_insurance() without DOB")
            
            # Test 8: fetch_patient_insurance (not found)
            insurance = patients.fetch_patient_insurance("NotFound", "Person")
            assert insurance is None, "Non-existent patient should return None"
            print("✓ fetch_patient_insurance() returns None for non-existent patient")
            
            print("\n✓✓✓ PASS: All patients repository tests")
            
        finally:
            patients.get_connection = original_get_connection


# ============================================================================
# Test Prescribers Repository
# ============================================================================

def test_prescribers_crud():
    """Test prescriber CRUD operations."""
    print("\n" + "=" * 70)
    print("TEST: Prescribers Repository")
    print("=" * 70)
    
    with in_memory_db() as conn:
        init_prescribers_schema(conn)
        
        import dmelogic.db.prescribers as prescribers
        
        original_get_connection = prescribers.get_connection
        provider = MockConnectionProvider(conn)
        prescribers.get_connection = provider.get_connection
        
        try:
            # Test 1: fetch_all_prescribers (empty)
            all_prescribers = prescribers.fetch_all_prescribers()
            assert len(all_prescribers) == 0, "Should start with no prescribers"
            print("✓ fetch_all_prescribers() empty database")
            
            # Test 2: Create sample prescribers
            prescriber1_id = create_sample_prescriber(conn, last_name="Doe", npi_number="1234567890")
            prescriber2_id = create_sample_prescriber(conn, last_name="Smith", npi_number="0987654321")
            print(f"✓ Created 2 sample prescribers (IDs: {prescriber1_id}, {prescriber2_id})")
            
            # Test 3: fetch_all_prescribers (with data)
            all_prescribers = prescribers.fetch_all_prescribers()
            assert len(all_prescribers) == 2, f"Expected 2 prescribers, got {len(all_prescribers)}"
            print("✓ fetch_all_prescribers() returns data")
            
            # Test 4: fetch_prescriber_by_id
            prescriber = prescribers.fetch_prescriber_by_id(prescriber1_id)
            assert prescriber is not None, "Prescriber should exist"
            assert prescriber["last_name"] == "Doe", "Last name should match"
            assert prescriber["npi_number"] == "1234567890", "NPI should match"
            print(f"✓ fetch_prescriber_by_id({prescriber1_id}) returns correct data")
            
            # Test 5: fetch_prescriber_by_npi
            prescriber = prescribers.fetch_prescriber_by_npi("1234567890")
            assert prescriber is not None, "Prescriber should be found by NPI"
            assert prescriber["last_name"] == "Doe", "Last name should match"
            print("✓ fetch_prescriber_by_npi() finds prescriber")
            
            # Test 6: fetch_prescriber_by_npi (not found)
            prescriber = prescribers.fetch_prescriber_by_npi("9999999999")
            assert prescriber is None, "Non-existent NPI should return None"
            print("✓ fetch_prescriber_by_npi() returns None for non-existent NPI")
            
            print("\n✓✓✓ PASS: All prescribers repository tests")
            
        finally:
            prescribers.get_connection = original_get_connection


# ============================================================================
# Test Insurance Repository
# ============================================================================

def test_insurance_crud():
    """Test insurance CRUD operations."""
    print("\n" + "=" * 70)
    print("TEST: Insurance Repository")
    print("=" * 70)
    
    with in_memory_db() as conn:
        init_insurance_schema(conn)
        
        import dmelogic.db.insurance as insurance
        
        original_get_connection = insurance.get_connection
        provider = MockConnectionProvider(conn)
        insurance.get_connection = provider.get_connection
        
        try:
            # Test 1: fetch_all_insurance_names (empty)
            all_insurance = insurance.fetch_all_insurance_names()
            assert len(all_insurance) == 0, "Should start with no insurance companies"
            print("✓ fetch_all_insurance_names() empty database")
            
            # Test 2: Create sample insurance companies
            ins1_id = create_sample_insurance(conn, "Blue Cross")
            ins2_id = create_sample_insurance(conn, "Aetna")
            ins3_id = create_sample_insurance(conn, "United Healthcare")
            print(f"✓ Created 3 insurance companies (IDs: {ins1_id}, {ins2_id}, {ins3_id})")
            
            # Test 3: fetch_all_insurance_names (with data)
            all_insurance = insurance.fetch_all_insurance_names()
            assert len(all_insurance) == 3, f"Expected 3 companies, got {len(all_insurance)}"
            print("✓ fetch_all_insurance_names() returns data")
            
            # Test 4: Increment usage count
            insurance.increment_insurance_usage("Blue Cross")
            cursor = conn.cursor()
            cursor.execute("SELECT usage_count FROM insurance_names WHERE name = ?", ("Blue Cross",))
            row = cursor.fetchone()
            assert row[0] == 2, f"Usage count should be 2, got {row[0]}"
            print("✓ increment_insurance_usage() updates count")
            
            print("\n✓✓✓ PASS: All insurance repository tests")
            
        finally:
            insurance.get_connection = original_get_connection


# ============================================================================
# Test Inventory Repository
# ============================================================================

def test_inventory_crud():
    """Test inventory CRUD operations."""
    print("\n" + "=" * 70)
    print("TEST: Inventory Repository")
    print("=" * 70)
    
    with in_memory_db() as conn:
        init_inventory_schema(conn)
        
        import dmelogic.db.inventory as inventory
        
        original_get_connection = inventory.get_connection
        provider = MockConnectionProvider(conn)
        inventory.get_connection = provider.get_connection
        
        try:
            # Test 1: fetch_all_inventory (empty)
            all_items = inventory.fetch_all_inventory()
            assert len(all_items) == 0, "Should start with no inventory"
            print("✓ fetch_all_inventory() empty database")
            
            # Test 2: Create sample inventory items
            item1_id = create_sample_inventory_item(conn, hcpcs_code="E0143", description="Walker")
            item2_id = create_sample_inventory_item(conn, hcpcs_code="E0130", description="Cane")
            item3_id = create_sample_inventory_item(conn, hcpcs_code="E0185", description="Commode")
            print(f"✓ Created 3 inventory items (IDs: {item1_id}, {item2_id}, {item3_id})")
            
            # Test 3: fetch_all_inventory (with data)
            all_items = inventory.fetch_all_inventory()
            assert len(all_items) == 3, f"Expected 3 items, got {len(all_items)}"
            print("✓ fetch_all_inventory() returns data")
            
            # Test 4: fetch_inventory_by_id
            item = inventory.fetch_inventory_by_id(item1_id)
            assert item is not None, "Item should exist"
            assert item["hcpcs_code"] == "E0143", "HCPCS should match"
            assert item["description"] == "Walker", "Description should match"
            print(f"✓ fetch_inventory_by_id({item1_id}) returns correct data")
            
            # Test 5: search_inventory (by HCPCS)
            results = inventory.search_inventory("E0143")
            assert len(results) >= 1, "Should find walker by HCPCS"
            assert any(r["hcpcs_code"] == "E0143" for r in results), "Walker should be in results"
            print("✓ search_inventory() finds by HCPCS code")
            
            # Test 6: search_inventory (by description)
            results = inventory.search_inventory("Cane")
            assert len(results) >= 1, "Should find cane by description"
            assert any("Cane" in r["description"] for r in results), "Cane should be in results"
            print("✓ search_inventory() finds by description")
            
            print("\n✓✓✓ PASS: All inventory repository tests")
            
        finally:
            inventory.get_connection = original_get_connection


# ============================================================================
# Test Orders Repository
# ============================================================================

def test_orders_crud():
    """Test order CRUD operations."""
    print("\n" + "=" * 70)
    print("TEST: Orders Repository")
    print("=" * 70)
    
    with in_memory_db() as conn:
        init_orders_schema(conn)
        
        import dmelogic.db.orders as orders
        
        original_get_connection = orders.get_connection
        provider = MockConnectionProvider(conn)
        orders.get_connection = provider.get_connection
        
        try:
            # Test 1: fetch_all_orders (empty)
            all_orders = orders.fetch_all_orders()
            assert len(all_orders) == 0, "Should start with no orders"
            print("✓ fetch_all_orders() empty database")
            
            # Test 2: Create sample orders
            order1_id = create_sample_order(conn, patient_last_name="Smith", order_status="Pending")
            order2_id = create_sample_order(conn, patient_last_name="Doe", order_status="Ready")
            order3_id = create_sample_order(conn, patient_last_name="Anderson", order_status="Delivered")
            print(f"✓ Created 3 sample orders (IDs: {order1_id}, {order2_id}, {order3_id})")
            
            # Test 3: fetch_all_orders (with data)
            all_orders = orders.fetch_all_orders()
            assert len(all_orders) == 3, f"Expected 3 orders, got {len(all_orders)}"
            print("✓ fetch_all_orders() returns data")
            
            # Test 4: fetch_order_by_id
            order = orders.fetch_order_by_id(order1_id)
            assert order is not None, "Order should exist"
            assert order["patient_last_name"] == "Smith", "Patient name should match"
            assert order["order_status"] == "Pending", "Status should match"
            print(f"✓ fetch_order_by_id({order1_id}) returns correct data")
            
            # Test 5: update_order_status
            orders.update_order_status(order1_id, "Ready")
            order = orders.fetch_order_by_id(order1_id)
            assert order["order_status"] == "Ready", "Status should be updated"
            print(f"✓ update_order_status() changes status")
            
            # Test 6: Create order items
            item1_id = create_sample_order_item(conn, order1_id, hcpcs_code="E0143")
            item2_id = create_sample_order_item(conn, order1_id, hcpcs_code="E0130")
            print(f"✓ Created 2 order items (IDs: {item1_id}, {item2_id})")
            
            # Test 7: fetch_order_items
            items = orders.fetch_order_items(order1_id)
            assert len(items) == 2, f"Expected 2 items, got {len(items)}"
            assert items[0]["hcpcs_code"] == "E0143", "First item HCPCS should match"
            assert items[1]["hcpcs_code"] == "E0130", "Second item HCPCS should match"
            print(f"✓ fetch_order_items({order1_id}) returns all items")
            
            # Test 8: fetch_order_items (no items)
            items = orders.fetch_order_items(order2_id)
            assert len(items) == 0, "Order without items should return empty list"
            print(f"✓ fetch_order_items({order2_id}) returns empty list")
            
            print("\n✓✓✓ PASS: All orders repository tests")
            
        finally:
            orders.get_connection = original_get_connection


# ============================================================================
# Test Order Items Repository Functions
# ============================================================================

def test_order_items_functions():
    """Test order item helper functions."""
    print("\n" + "=" * 70)
    print("TEST: Order Items Functions")
    print("=" * 70)
    
    with in_memory_db() as conn:
        init_orders_schema(conn)
        
        import dmelogic.db.orders as orders
        
        original_get_connection = orders.get_connection
        provider = MockConnectionProvider(conn)
        orders.get_connection = provider.get_connection
        
        try:
            # Create order and items
            order_id = create_sample_order(conn)
            item1_id = create_sample_order_item(conn, order_id, rx_no="1001", hcpcs_code="E0143")
            item2_id = create_sample_order_item(conn, order_id, rx_no="1002", hcpcs_code="E0130")
            
            # Test 1: fetch_order_items_by_ids
            items = orders.fetch_order_items_by_ids([item1_id, item2_id])
            assert len(items) == 2, f"Expected 2 items, got {len(items)}"
            print("✓ fetch_order_items_by_ids() returns requested items")
            
            # Test 2: fetch_order_items_by_ids (partial)
            items = orders.fetch_order_items_by_ids([item1_id])
            assert len(items) == 1, "Should return only requested item"
            assert items[0]["id"] == item1_id, "Should return correct item"
            print("✓ fetch_order_items_by_ids() handles partial lists")
            
            # Test 3: fetch_order_items_by_ids (empty)
            items = orders.fetch_order_items_by_ids([])
            assert len(items) == 0, "Empty ID list should return empty result"
            print("✓ fetch_order_items_by_ids() handles empty list")
            
            print("\n✓✓✓ PASS: All order items function tests")
            
        finally:
            orders.get_connection = original_get_connection


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DME LOGIC REPOSITORY UNIT TESTS")
    print("Testing with in-memory SQLite databases")
    print("=" * 70)
    
    try:
        test_patients_crud()
        test_prescribers_crud()
        test_insurance_crud()
        test_inventory_crud()
        test_orders_crud()
        test_order_items_functions()
        
        print("\n" + "=" * 70)
        print("✓✓✓ ALL REPOSITORY TESTS PASSED ✓✓✓")
        print("=" * 70)
        print("\nTest Summary:")
        print("  ✓ Patients repository: CRUD operations")
        print("  ✓ Prescribers repository: CRUD operations")
        print("  ✓ Insurance repository: CRUD operations")
        print("  ✓ Inventory repository: CRUD and search")
        print("  ✓ Orders repository: CRUD operations")
        print("  ✓ Order items: Helper functions")
        print("\nAll tests use in-memory SQLite (:memory:) for isolation")
        print("No test data pollutes production databases")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
