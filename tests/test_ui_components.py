"""
Test script to verify UI components work correctly.

Run this to ensure all new components import and instantiate without errors.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QWidget

def test_imports():
    """Test that all components can be imported."""
    print("Testing imports...")
    
    try:
        from dmelogic.ui.components import (
            SearchBar, PageHeader, SummaryFooter, ActionButtonRow,
            FilterRow, StatusBadge, Separator,
            create_standard_page_layout, create_filter_bar_with_search
        )
        print("✅ components.py imports successful")
    except Exception as e:
        print(f"❌ components.py import failed: {e}")
        return False
    
    try:
        from dmelogic.ui.styling import (
            StatusColors, apply_standard_table_style,
            create_refill_status_item, create_order_status_item,
            calculate_days_until_due, color_code_refill_row,
            create_centered_item, create_right_aligned_item
        )
        print("✅ styling.py imports successful")
    except Exception as e:
        print(f"❌ styling.py import failed: {e}")
        return False
    
    return True


def test_component_instantiation():
    """Test that components can be instantiated."""
    print("\nTesting component instantiation...")
    
    app = QApplication(sys.argv)
    
    try:
        from dmelogic.ui.components import (
            SearchBar, PageHeader, SummaryFooter, ActionButtonRow,
            StatusBadge, Separator, create_standard_page_layout
        )
        
        # SearchBar
        search = SearchBar(label="Test:", placeholder="Test...")
        print("✅ SearchBar instantiated")
        
        # PageHeader
        header = PageHeader(title="Test Title", subtitle="Test Subtitle")
        print("✅ PageHeader instantiated")
        
        # SummaryFooter
        footer = SummaryFooter()
        footer.setSummaryText("Test: 10 items")
        footer.addPrimaryButton("Test", lambda: None)
        print("✅ SummaryFooter instantiated")
        
        # ActionButtonRow
        button_row = ActionButtonRow()
        button_row.addPrimaryButton("Test", lambda: None)
        button_row.addSecondaryButton("Test", lambda: None)
        print("✅ ActionButtonRow instantiated")
        
        # StatusBadge
        badge = StatusBadge("Pending", status_type="warning")
        print("✅ StatusBadge instantiated")
        
        # Separator
        sep = Separator()
        print("✅ Separator instantiated")
        
        # Standard page layout
        test_widget = QWidget()
        layout, h, c, f = create_standard_page_layout(
            title="Test",
            subtitle="Test subtitle",
            parent=test_widget
        )
        test_widget.setLayout(layout)
        print("✅ create_standard_page_layout() works")
        
        return True
    
    except Exception as e:
        print(f"❌ Component instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()


def test_styling_functions():
    """Test styling utility functions."""
    print("\nTesting styling functions...")
    
    app = QApplication(sys.argv)
    
    try:
        from PyQt6.QtWidgets import QTableWidget
        from dmelogic.ui.styling import (
            apply_standard_table_style,
            create_refill_status_item,
            create_order_status_item,
            calculate_days_until_due,
            create_centered_item,
            create_right_aligned_item
        )
        
        # Table styling
        table = QTableWidget()
        apply_standard_table_style(table)
        print("✅ apply_standard_table_style() works")
        
        # Refill status item
        item = create_refill_status_item("Test", days_until_due=-5)
        print("✅ create_refill_status_item() works")
        
        # Order status item
        item = create_order_status_item("Test", "Pending")
        print("✅ create_order_status_item() works")
        
        # Calculate days
        days = calculate_days_until_due("2025-12-31", "2025-12-05")
        assert days == 26, f"Expected 26 days, got {days}"
        print("✅ calculate_days_until_due() works")
        
        # Centered item
        item = create_centered_item("Test")
        print("✅ create_centered_item() works")
        
        # Right-aligned item
        item = create_right_aligned_item("123")
        print("✅ create_right_aligned_item() works")
        
        return True
    
    except Exception as e:
        print(f"❌ Styling function failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()


def main():
    """Run all tests."""
    print("=" * 60)
    print("UI COMPONENTS TEST SUITE")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test instantiation
    if not test_component_instantiation():
        all_passed = False
    
    # Test styling functions
    if not test_styling_functions():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("UI components are working correctly!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check errors above for details.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
