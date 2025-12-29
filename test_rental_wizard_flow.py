"""
Test rental and modifier flow from wizard to database to domain model.
"""
from dmelogic.ui.order_wizard import OrderItem as WizardOrderItem
from dmelogic.db.orders import wizard_item_to_input
from dmelogic.db.models import OrderItemInput


def test_wizard_item_to_input():
    """Test conversion of wizard OrderItem to domain OrderItemInput."""
    
    # Test case 1: Purchase item (no rental, no modifiers)
    w_item1 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        refills=0,
        days_supply=30,
        directions="Use nightly",
        is_rental=False,
        modifiers=""
    )
    
    result1 = wizard_item_to_input(w_item1)
    assert result1.hcpcs == "E0601"
    assert result1.is_rental is False
    assert result1.modifier1 is None
    assert result1.modifier2 is None
    print("✅ Purchase item (no modifiers): PASS")
    
    # Test case 2: Rental with single modifier
    w_item2 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        refills=3,
        days_supply=30,
        directions="Use nightly",
        is_rental=True,
        modifiers="RR"
    )
    
    result2 = wizard_item_to_input(w_item2)
    assert result2.is_rental is True
    assert result2.modifier1 == "RR"
    assert result2.modifier2 is None
    print("✅ Rental with single modifier (RR): PASS")
    
    # Test case 3: Rental with multiple modifiers (comma-separated)
    w_item3 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        refills=3,
        days_supply=30,
        is_rental=True,
        modifiers="RR, NU, KX"
    )
    
    result3 = wizard_item_to_input(w_item3)
    assert result3.is_rental is True
    assert result3.modifier1 == "RR"
    assert result3.modifier2 == "NU"
    assert result3.modifier3 == "KX"
    assert result3.modifier4 is None
    print("✅ Rental with 3 modifiers (comma-separated): PASS")
    
    # Test case 4: Rental with space-separated modifiers
    w_item4 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        is_rental=True,
        modifiers="RR NU KX MS"
    )
    
    result4 = wizard_item_to_input(w_item4)
    assert result4.modifier1 == "RR"
    assert result4.modifier2 == "NU"
    assert result4.modifier3 == "KX"
    assert result4.modifier4 == "MS"
    print("✅ Rental with 4 modifiers (space-separated): PASS")
    
    # Test case 5: Rental with slash-separated modifiers
    w_item5 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        is_rental=True,
        modifiers="RR/NU"
    )
    
    result5 = wizard_item_to_input(w_item5)
    assert result5.modifier1 == "RR"
    assert result5.modifier2 == "NU"
    print("✅ Rental with slash-separated modifiers: PASS")
    
    # Test case 6: More than 4 modifiers (should truncate)
    w_item6 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        is_rental=True,
        modifiers="RR, NU, KX, MS, BP"  # 5 modifiers
    )
    
    result6 = wizard_item_to_input(w_item6)
    assert result6.modifier1 == "RR"
    assert result6.modifier2 == "NU"
    assert result6.modifier3 == "KX"
    assert result6.modifier4 == "MS"
    # BP should be truncated (only 4 allowed)
    print("✅ Truncate to 4 modifiers: PASS")
    
    # Test case 7: Case normalization (lowercase → uppercase)
    w_item7 = WizardOrderItem(
        hcpcs="E0601",
        description="CPAP Device",
        quantity=1,
        is_rental=True,
        modifiers="rr, nu"
    )
    
    result7 = wizard_item_to_input(w_item7)
    assert result7.modifier1 == "RR"
    assert result7.modifier2 == "NU"
    print("✅ Lowercase modifiers normalized to uppercase: PASS")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Wizard → Domain conversion working!")
    print("="*60)
    print("\nComplete flow:")
    print("  1. User checks 'Rental?' checkbox in wizard")
    print("  2. User types 'RR, NU' in Modifiers field")
    print("  3. wizard_item_to_input() parses & normalizes")
    print("  4. OrderItemInput carries is_rental + 4 modifier slots")
    print("  5. create_order_from_wizard_result() persists to DB")
    print("  6. Domain model reads back with full rental metadata")
    print("  7. State portal export / 1500 claims can use these fields")


if __name__ == "__main__":
    test_wizard_item_to_input()
