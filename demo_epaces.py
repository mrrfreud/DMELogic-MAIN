"""
Test ePACES Dialog

Quick test to verify the ePACES billing helper dialog works.
"""

import sys
from PyQt6.QtWidgets import QApplication

from dmelogic.ui.epaces_dialog import EpacesDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Load theme
    try:
        with open("assets/theme.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Warning: Theme file not found, using default styling")
    
    print("=" * 80)
    print("🔐 EPACES BILLING HELPER DIALOG TEST")
    print("=" * 80)
    print()
    print("Opening Order #1 in ePACES helper...")
    print("Database: C:\\FaxManagerData\\Data")
    print()
    print("Features:")
    print("  ✅ Member & Insurance info (all copyable)")
    print("  ✅ Prescriber NPI (copyable)")
    print("  ✅ HCPCS lines with units and amounts")
    print("  ✅ PA# scratch fields for manual portal entry")
    print("  ✅ Copy individual lines or all lines as formatted text")
    print()
    print("=" * 80)
    
    dialog = EpacesDialog(
        order_id=1,
        folder_path=r"C:\FaxManagerData\Data"
    )
    
    dialog.exec()
    
    print("\n✅ ePACES dialog test complete")
