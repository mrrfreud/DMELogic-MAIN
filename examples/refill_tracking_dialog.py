"""
refill_tracking_dialog.py — Example UI implementation for Refill Due Tracking screen.

This is a REFERENCE IMPLEMENTATION showing how to integrate the refill system
with the UI layer. This follows the clean architecture pattern:
- No SQL queries in UI
- No file path logic in UI
- Simple service function calls
- All business logic in service/repository layers
- Uses unified dark theme for consistent appearance
"""

from datetime import date, timedelta
from typing import List
import sys
from pathlib import Path

# Add parent directory to path for theme_manager import
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import QDate, Qt

from dmelogic.db.refills import fetch_refills_due
from dmelogic.services.refill_service import process_refills
from theme_manager import ThemeColors, ThemeSpacing


class RefillTrackingDialog(QDialog):
    """
    Refill Due Tracking Dialog.

    Displays order items that are due for refills within a date range,
    and allows creating new orders for selected items.
    """

    def __init__(self, db_folder: str, parent=None):
        super().__init__(parent)
        self.db_folder = db_folder
        self.refill_data: List[dict] = []

        self.setup_ui()
        self.setWindowTitle("Refill Due Tracking")
        self.resize(1400, 700)

    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Date range selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Refills Due From:"))

        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate())
        self.from_date.setCalendarPopup(True)
        date_layout.addWidget(self.from_date)

        date_layout.addWidget(QLabel("To:"))

        self.to_date = QDateEdit()
        # Default to 30 days out
        self.to_date.setDate(QDate.currentDate().addDays(30))
        self.to_date.setCalendarPopup(True)
        date_layout.addWidget(self.to_date)

        self.generate_btn = QPushButton("Generate Refill List")
        self.generate_btn.clicked.connect(self.on_generate_refill_list)
        date_layout.addWidget(self.generate_btn)

        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Results table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)

        # Column headers matching the screenshot
        headers = [
            "Order ID",
            "Order Date",
            "Patient Name",
            "DOB",
            "Phone",
            "HCPCS",
            "Description",
            "Refills",
            "Day Supply",
            "Last Refill",
            "Next Due",
            "Days Until",
            "Prescriber",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Stretch columns for better visibility
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Patient Name
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)  # Description
        
        # Set standard row height from theme
        self.table.verticalHeader().setDefaultSectionSize(ThemeSpacing.TABLE_ROW_HEIGHT)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.create_orders_btn = QPushButton("Create Orders for Selected")
        self.create_orders_btn.clicked.connect(self.on_create_orders_for_selected)
        self.create_orders_btn.setEnabled(False)
        button_layout.addWidget(self.create_orders_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def on_generate_refill_list(self):
        """
        Generate the refill list based on selected date range.

        THIS IS THE KEY INTEGRATION POINT - Notice how clean it is:
        1. Get dates from UI controls
        2. Call repository function
        3. Display results
        NO SQL, NO FILE PATHS, NO BUSINESS LOGIC
        """
        # Get date range from UI
        start_date = self.from_date.date().toString("yyyy-MM-dd")
        end_date = self.to_date.date().toString("yyyy-MM-dd")
        today = date.today().strftime("%Y-%m-%d")

        try:
            # Call data layer function - that's it!
            rows = fetch_refills_due(
                start_date=start_date,
                end_date=end_date,
                today=today,
                folder_path=self.db_folder,
            )

            # Store data and display
            self.refill_data = rows
            self.display_refills(rows)

            # Enable create button if we have results
            self.create_orders_btn.setEnabled(len(rows) > 0)

            # Show count
            QMessageBox.information(
                self,
                "Refills Found",
                f"Found {len(rows)} item(s) due for refills in the selected date range.",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate refill list:\n{str(e)}\n\nPlease check the log for details.",
            )

    def display_refills(self, rows: List[dict]):
        """Display refill data in the table."""
        self.table.setRowCount(len(rows))

        for row_idx, data in enumerate(rows):
            # Order ID
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(data["order_id"])))

            # Order Date
            self.table.setItem(row_idx, 1, QTableWidgetItem(data["order_date"]))

            # Patient Name
            self.table.setItem(row_idx, 2, QTableWidgetItem(data["patient_name"]))

            # DOB
            self.table.setItem(row_idx, 3, QTableWidgetItem(data["patient_dob"]))

            # Phone
            self.table.setItem(row_idx, 4, QTableWidgetItem(data["patient_phone"]))

            # HCPCS
            self.table.setItem(row_idx, 5, QTableWidgetItem(data["hcpcs_code"]))

            # Description
            self.table.setItem(row_idx, 6, QTableWidgetItem(data["description"]))

            # Refills
            self.table.setItem(
                row_idx, 7, QTableWidgetItem(str(data["refills_remaining"]))
            )

            # Day Supply
            self.table.setItem(row_idx, 8, QTableWidgetItem(str(data["day_supply"])))

            # Last Refill
            self.table.setItem(row_idx, 9, QTableWidgetItem(data["last_filled_date"]))

            # Next Due
            next_due_item = QTableWidgetItem(data["next_refill_due"])
            # Highlight items due soon (within 7 days) using theme colors
            if data["days_until_due"] <= 7:
                next_due_item.setBackground(Qt.GlobalColor.yellow)
                next_due_item.setForeground(Qt.GlobalColor.black)
            self.table.setItem(row_idx, 10, next_due_item)

            # Days Until
            days_item = QTableWidgetItem(str(data["days_until_due"]))
            if data["days_until_due"] <= 0:
                days_item.setBackground(Qt.GlobalColor.red)
                days_item.setForeground(Qt.GlobalColor.white)
            elif data["days_until_due"] <= 7:
                days_item.setBackground(Qt.GlobalColor.yellow)
                days_item.setForeground(Qt.GlobalColor.black)
            self.table.setItem(row_idx, 11, days_item)

            # Prescriber
            self.table.setItem(row_idx, 12, QTableWidgetItem(data["prescriber_name"]))

        self.table.resizeColumnsToContents()

    def on_create_orders_for_selected(self):
        """
        Create refill orders for selected items.

        THIS IS THE OTHER KEY INTEGRATION POINT - Also very clean:
        1. Get selected rows
        2. Extract order_item_ids
        3. Call service function
        4. Show result and refresh
        NO SQL, NO TRANSACTIONS, NO BUSINESS LOGIC
        """
        # Get selected rows
        selected_rows = set(item.row() for item in self.table.selectedItems())

        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more items to create refill orders.",
            )
            return

        # Extract order_item_ids from selected rows
        selected_item_ids = [
            self.refill_data[row_idx]["order_item_id"] for row_idx in selected_rows
        ]

        # Confirm action
        reply = QMessageBox.question(
            self,
            "Confirm Refill Orders",
            f"Create refill orders for {len(selected_item_ids)} selected item(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Call service layer function - that's it!
            fill_date = date.today().strftime("%Y-%m-%d")

            count = process_refills(
                selected_item_ids=selected_item_ids,
                refill_fill_date=fill_date,
                folder_path=self.db_folder,
            )

            # Show success
            QMessageBox.information(
                self,
                "Orders Created",
                f"Successfully created {count} refill order(s).\n\n"
                f"The new orders have been created with status 'Pending'.",
            )

            # Refresh the list to show updated refills
            self.on_generate_refill_list()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create refill orders:\n{str(e)}\n\nPlease check the log for details.",
            )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """
    Example of how to launch this dialog from the main application.
    """
    import sys
    from PyQt6.QtWidgets import QApplication
    from theme_manager import apply_theme

    # This would typically come from your main window
    DB_FOLDER = "C:/FaxManagerData/Data"  # or wherever your databases are

    app = QApplication(sys.argv)
    
    # Apply unified dark theme
    apply_theme(app, "dark")

    dialog = RefillTrackingDialog(db_folder=DB_FOLDER)
    dialog.exec()

    sys.exit(0)
