"""
Visual test: Open the Order Wizard and verify rental + modifiers columns.

This will:
1. Open the wizard 
2. Navigate to the Items step
3. Add a few test items with rental status and modifiers
4. Display the result to verify the flow works
"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from dmelogic.ui.order_wizard import OrderWizard


def test_rental_wizard_ui():
    """Open wizard and show rental + modifiers columns."""
    app = QApplication(sys.argv)
    
    # Create wizard with some initial data
    wizard = OrderWizard(
        parent=None,
        initial_patient={
            "patient_name": "TEST, RENTAL",
            "patient_dob": "1980-01-01",
            "patient_phone": "555-1234"
        },
        rx_context={
            "prescriber_name": "SMITH, JOHN",
            "prescriber_npi": "1234567890",
            "prescriber_phone": "555-5678"
        }
    )
    
    # Show info message
    QMessageBox.information(
        wizard,
        "Rental & Modifiers Test",
        "Testing rental + modifiers workflow!\n\n"
        "Instructions:\n"
        "1. Navigate to 'Items' step (Next → Next)\n"
        "2. Add item rows\n"
        "3. Fill in HCPCS (e.g., E0601)\n"
        "4. Check 'Rental?' for rental items\n"
        "5. Type modifiers like 'RR, NU' or 'RR NU'\n"
        "6. Complete wizard to test full flow\n\n"
        "The wizard now has 8 columns:\n"
        "  - HCPCS, Description, Qty, Refills, Days, Directions\n"
        "  - Rental? (checkbox)\n"
        "  - Modifiers (text field)"
    )
    
    result = wizard.exec()
    
    if result == wizard.DialogCode.Accepted:
        wizard_result = wizard.result
        
        print("\n" + "="*70)
        print("WIZARD RESULT - Items with Rental & Modifiers")
        print("="*70)
        
        for idx, item in enumerate(wizard_result.items, 1):
            print(f"\nItem {idx}:")
            print(f"  HCPCS: {item.hcpcs}")
            print(f"  Description: {item.description}")
            print(f"  Quantity: {item.quantity}")
            print(f"  Refills: {item.refills}")
            print(f"  Days Supply: {item.days_supply}")
            print(f"  Directions: {item.directions}")
            print(f"  🔄 Rental?: {item.is_rental}")
            print(f"  📋 Modifiers: '{item.modifiers}'")
        
        print("\n" + "="*70)
        print("✅ Wizard completed successfully!")
        print("="*70)
        
        # Show summary dialog
        summary = []
        for idx, item in enumerate(wizard_result.items, 1):
            rental_text = "RENTAL" if item.is_rental else "PURCHASE"
            mods_text = f" [{item.modifiers}]" if item.modifiers else ""
            summary.append(
                f"{idx}. {item.hcpcs} - {rental_text}{mods_text}"
            )
        
        QMessageBox.information(
            None,
            "Wizard Result",
            f"Collected {len(wizard_result.items)} items:\n\n" + "\n".join(summary)
        )
    else:
        print("Wizard cancelled")
    
    app.quit()


if __name__ == "__main__":
    test_rental_wizard_ui()
