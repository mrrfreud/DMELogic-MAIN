"""
Visual demo of UI components and styling.

This demo shows all reusable components in action with the dark theme.
Run this to see what the standardized UI looks like.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QTabWidget, QVBoxLayout,
    QTableWidget, QComboBox, QLabel, QHBoxLayout
)
from PyQt6.QtCore import QDate

from dmelogic.ui.components import (
    PageHeader, SearchBar, SummaryFooter, ActionButtonRow,
    FilterRow, StatusBadge, Separator, create_standard_page_layout
)
from dmelogic.ui.styling import (
    apply_standard_table_style, create_refill_status_item,
    create_order_status_item, create_centered_item
)
from theme.theme_manager import apply_dark_theme


class ComponentDemoTab(QWidget):
    """Demo of all reusable components."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(24)
        
        # PageHeader demo
        layout.addWidget(QLabel("1. PageHeader Component:"))
        header = PageHeader(
            title="Component Showcase",
            subtitle="Demonstrating all reusable UI components"
        )
        layout.addWidget(header)
        
        layout.addWidget(Separator())
        
        # SearchBar demo
        layout.addWidget(QLabel("2. SearchBar Component:"))
        search_bar = SearchBar(
            label="Search Orders:",
            placeholder="Patient name, RX#..."
        )
        search_bar.textChanged.connect(lambda t: print(f"Search: {t}"))
        layout.addWidget(search_bar)
        
        layout.addWidget(Separator())
        
        # FilterRow demo
        layout.addWidget(QLabel("3. FilterRow with Multiple Filters:"))
        filter_row = FilterRow()
        filter_row.addSearchBar("Search:", "Type to search...")
        
        status_combo = QComboBox()
        status_combo.addItems(["All", "Pending", "Verified", "Delivered"])
        filter_row.addWidget(QLabel("Status:"))
        filter_row.addWidget(status_combo)
        filter_row.addSpacer()
        layout.addWidget(filter_row)
        
        layout.addWidget(Separator())
        
        # ActionButtonRow demo
        layout.addWidget(QLabel("4. ActionButtonRow (Button Types):"))
        button_row = ActionButtonRow()
        button_row.addPrimaryButton("Primary Action", lambda: print("Primary"))
        button_row.addSecondaryButton("Secondary", lambda: print("Secondary"))
        button_row.addSpacer()
        button_row.addDangerButton("Delete", lambda: print("Danger"))
        layout.addWidget(button_row)
        
        layout.addWidget(Separator())
        
        # StatusBadge demo
        layout.addWidget(QLabel("5. StatusBadge Component:"))
        badge_layout = QHBoxLayout()
        badge_layout.addWidget(StatusBadge("Success", "success"))
        badge_layout.addWidget(StatusBadge("Warning", "warning"))
        badge_layout.addWidget(StatusBadge("Danger", "danger"))
        badge_layout.addWidget(StatusBadge("Info", "info"))
        badge_layout.addWidget(StatusBadge("Neutral", "neutral"))
        badge_layout.addStretch()
        layout.addLayout(badge_layout)
        
        layout.addWidget(Separator())
        
        # SummaryFooter demo
        layout.addWidget(QLabel("6. SummaryFooter Component:"))
        footer = SummaryFooter()
        footer.setSummaryText("Total: 25 orders | Pending: 10 | Completed: 15")
        footer.addPrimaryButton("Create Order", lambda: print("Create"))
        footer.addSecondaryButton("Export", lambda: print("Export"))
        footer.addSecondaryButton("Print", lambda: print("Print"))
        layout.addWidget(footer)
        
        layout.addStretch()


class TableDemoTab(QWidget):
    """Demo of standardized table styling with color coding."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        # Use standard page layout
        layout, header, content, footer = create_standard_page_layout(
            title="Table Styling Demo",
            subtitle="Color-coded status indicators and standard formatting"
        )
        self.setLayout(layout)
        
        # Filter row
        filter_row = FilterRow()
        search_bar = filter_row.addSearchBar("Search:", "Filter table...")
        filter_row.addSpacer()
        content.layout().addWidget(filter_row)
        
        # Table with refill status color coding
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Patient", "HCPCS", "Next Due", "Days Until", "Refills", "Status"
        ])
        
        apply_standard_table_style(self.table)
        
        # Sample data with different urgencies
        sample_data = [
            ("Smith, John", "A4253", "2025-11-30", -5, 8),  # Overdue
            ("Jones, Mary", "E0601", "2025-12-03", -2, 5),  # Overdue
            ("Brown, Bob", "A4224", "2025-12-05", 0, 11),   # Today
            ("Davis, Sue", "K0738", "2025-12-08", 3, 4),    # Due soon
            ("Wilson, Tom", "A4217", "2025-12-10", 5, 7),   # Due soon
            ("Miller, Ann", "E0424", "2025-12-20", 15, 9),  # Future
            ("Taylor, Jim", "A4561", "2025-12-25", 20, 6),  # Future
        ]
        
        self.table.setRowCount(len(sample_data))
        
        for row, (patient, hcpcs, due_date, days_until, refills) in enumerate(sample_data):
            # Patient name - color coded
            item = create_refill_status_item(patient, days_until)
            self.table.setItem(row, 0, item)
            
            # HCPCS - centered
            item = create_centered_item(hcpcs)
            self.table.setItem(row, 1, item)
            
            # Next due - color coded, centered
            item = create_refill_status_item(due_date, days_until, align_center=True)
            self.table.setItem(row, 2, item)
            
            # Days until - color coded with text
            if days_until < 0:
                days_text = f"{abs(days_until)} OVERDUE"
            elif days_until == 0:
                days_text = "TODAY"
            else:
                days_text = str(days_until)
            item = create_refill_status_item(days_text, days_until, align_center=True)
            self.table.setItem(row, 3, item)
            
            # Refills - centered
            item = create_centered_item(str(refills))
            self.table.setItem(row, 4, item)
            
            # Order status - color coded
            if days_until < 0:
                status = "Overdue"
            elif days_until <= 7:
                status = "Due Soon"
            else:
                status = "Scheduled"
            item = create_order_status_item(status, status)
            self.table.setItem(row, 5, item)
        
        content.layout().addWidget(self.table, stretch=1)
        
        # Footer
        overdue = sum(1 for _, _, _, d, _ in sample_data if d < 0)
        due_soon = sum(1 for _, _, _, d, _ in sample_data if 0 <= d <= 7)
        future = sum(1 for _, _, _, d, _ in sample_data if d > 7)
        
        footer.setSummaryText(
            f"Total: {len(sample_data)} | Overdue: {overdue} | "
            f"Due Soon: {due_soon} | Future: {future}"
        )
        footer.addPrimaryButton("Process Refills", lambda: print("Process"))
        footer.addSecondaryButton("Export", lambda: print("Export"))


class StandardLayoutDemo(QWidget):
    """Demo of standard page layout pattern."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        # One-line standard layout creation
        layout, header, content, footer = create_standard_page_layout(
            title="Standard Layout Pattern",
            subtitle="This is what every screen should look like"
        )
        self.setLayout(layout)
        
        # Add description
        desc = QLabel(
            "Every screen in the application follows this pattern:\n\n"
            "1. PageHeader (title + subtitle)\n"
            "2. FilterRow (search + filters)\n"
            "3. Content Area (table, form, etc.)\n"
            "4. SummaryFooter (statistics + action buttons)\n\n"
            "All styling is handled by dark.qss theme.\n"
            "No inline styles needed!"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("padding: 20px; background: #2b2b2b; border-radius: 4px;")
        content.layout().addWidget(desc)
        
        # Benefits list
        benefits = QLabel(
            "✅ Consistent appearance across all screens\n"
            "✅ Faster development (reusable components)\n"
            "✅ Easy maintenance (one theme file)\n"
            "✅ Professional, commercial look\n"
            "✅ Accessible and user-friendly"
        )
        benefits.setWordWrap(True)
        benefits.setStyleSheet("padding: 20px; background: #252525; border-radius: 4px;")
        content.layout().addWidget(benefits)
        
        content.layout().addStretch()
        
        # Footer with typical actions
        footer.setSummaryText("Standard Layout Demo")
        footer.addPrimaryButton("Primary Action", lambda: print("Primary"))
        footer.addSecondaryButton("Secondary", lambda: print("Secondary"))


class ComponentDemoWindow(QMainWindow):
    """Main window for component demo."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DME Logic - UI Components Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create tab widget
        tabs = QTabWidget()
        tabs.addTab(StandardLayoutDemo(), "Standard Layout")
        tabs.addTab(ComponentDemoTab(), "Components")
        tabs.addTab(TableDemoTab(), "Table Styling")
        
        self.setCentralWidget(tabs)


def main():
    """Run component demo application."""
    app = QApplication(sys.argv)
    
    # Apply dark theme
    apply_dark_theme(app)
    
    # Show demo window
    window = ComponentDemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
