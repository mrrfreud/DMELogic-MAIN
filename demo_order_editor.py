"""
Demo script to showcase the new Modern Order Editor.

This demonstrates the unified interface for viewing/editing orders,
powered by the domain model (fetch_order_with_items).

Usage:
    python demo_order_editor.py [order_id]
    
If no order_id is provided, it will use order #1 as default.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from dmelogic.ui.order_editor import OrderEditorDialog


def main():
    # Get order ID from command line or use default
    order_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    # Default folder path
    folder_path = r"C:\FaxManagerData\Data"
    
    print("=" * 80)
    print("🎯 MODERN ORDER EDITOR DEMO")
    print("=" * 80)
    print(f"\nOpening Order #{order_id}...")
    print(f"Database: {folder_path}")
    print("\nFeatures:")
    print("  ✅ Domain model powered (fetch_order_with_items)")
    print("  ✅ All order details in organized sections")
    print("  ✅ Status workflow with validation")
    print("  ✅ Action buttons for common operations:")
    print("     • Send to State Portal")
    print("     • Generate HCFA-1500 PDF")
    print("     • Print Delivery Ticket")
    print("     • Process Refills (with K modifier auto-update)")
    print("     • Change Status")
    print("  ✅ Modifier display in items table")
    print("  ✅ Clean, modern UI")
    print("\n" + "=" * 80)
    
    app = QApplication(sys.argv)
    
    # Load global theme
    theme_path = Path(__file__).parent / "assets" / "theme.qss"
    if theme_path.exists():
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    # Create and show the dialog
    dialog = OrderEditorDialog(
        order_id=order_id,
        folder_path=folder_path
    )
    
    # Connect signals to show feedback
    def on_order_updated():
        print(f"\n✅ Order #{order_id} was updated!")
    
    dialog.order_updated.connect(on_order_updated)
    
    # Show dialog
    dialog.exec()
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
