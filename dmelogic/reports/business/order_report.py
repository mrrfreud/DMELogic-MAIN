"""
Order Report - Migrated to Foundation

Shows order history with filtering and export capabilities.
"""

from typing import List, Dict, Any

from PyQt6.QtWidgets import QDialog, QVBoxLayout

from dmelogic.reports.base import ReportEngine, ReportColumn, ReportRow
from dmelogic.reports.ui import ReportViewer


class OrderReportEngine(ReportEngine):
    """Order Report Engine - Shows order history."""

    def get_report_title(self) -> str:
        return "📋 Order Report"

    def get_columns(self) -> List[ReportColumn]:
        return [
            ReportColumn("order_number", "Order #", alignment="left"),
            ReportColumn("order_date", "Order Date", data_type="date", alignment="center"),
            ReportColumn("patient_name", "Patient", alignment="left"),
            ReportColumn("insurance", "Insurance", alignment="left"),
            ReportColumn("items_count", "Items", data_type="number", alignment="center"),
            ReportColumn("total_amount", "Total", data_type="currency", alignment="right"),
            ReportColumn("status", "Status", alignment="center"),
            ReportColumn("delivery_date", "Delivery", data_type="date", alignment="center"),
        ]

    def _fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch orders from database."""
        rows = self.execute_query(
            "orders.db",
            """
            SELECT
                o.id as order_number,
                COALESCE(o.order_date, o.created_date) as order_date,
                COALESCE(o.patient_name,
                         o.patient_last_name || ', ' || o.patient_first_name) as patient_name,
                COALESCE(o.primary_insurance, 'Self Pay') as insurance,
                COALESCE(o.order_status, 'Pending') as status,
                COALESCE(o.delivery_date, '') as delivery_date,
                (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as items_count,
                (SELECT COALESCE(SUM(CAST(total AS REAL)), 0)
                 FROM order_items WHERE order_id = o.id) as total_amount
            FROM orders o
            ORDER BY COALESCE(o.order_date, o.created_date) DESC
            LIMIT 1000
            """
        )

        orders = []
        for row in rows:
            orders.append({
                'order_number': row['order_number'],
                'order_date': self.parse_date(row['order_date']),
                'patient_name': row['patient_name'] or '',
                'insurance': row['insurance'],
                'items_count': int(row['items_count'] or 0),
                'total_amount': float(row['total_amount'] or 0),
                'status': row['status'],
                'delivery_date': self.parse_date(row['delivery_date']) if row['delivery_date'] else None,
            })

        return orders

    def _calculate_summary(self, rows: List[ReportRow]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not rows:
            return {'total_rows': 0}

        total_revenue = sum(row.data['total_amount'] for row in rows)
        avg_order_value = total_revenue / len(rows) if rows else 0

        status_counts = {}
        for row in rows:
            status = row.data['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            'total_rows': len(rows),
            'total_revenue': total_revenue,
            'avg_order_value': avg_order_value,
            'status_counts': status_counts
        }


class OrderReport(QDialog):
    """Order Report Dialog using foundation."""

    def __init__(self, parent=None, folder_path=None):
        super().__init__(parent)
        self.folder_path = folder_path or "."

        self.setWindowTitle("📋 Order Report")
        self.setModal(False)
        self.resize(1400, 800)

        self._setup_ui()
        self._generate_report(self.viewer.get_filter_values())

    def _setup_ui(self):
        """Setup UI with ReportViewer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.viewer = ReportViewer(show_filters=True)

        self.viewer.add_filter_date_range("Start Date", "End Date")
        self.viewer.add_filter_combo("Status", ["All", "Pending", "Delivered", "Shipped", "Cancelled"])
        self.viewer.add_filter_search("Search orders...")

        self.viewer.refresh_requested.connect(self._generate_report)
        layout.addWidget(self.viewer)

    def _generate_report(self, filters=None):
        """Generate and display the report."""
        try:
            engine = OrderReportEngine(self.folder_path)
            data = engine.generate()

            # Apply date range filter
            if filters:
                sd, ed = filters.get('start_date'), filters.get('end_date')
                if sd and ed:
                    data.rows = [r for r in data.rows
                                 if r.data.get('order_date') and sd <= r.data['order_date'] <= ed]

            if filters and filters.get('Status') and filters['Status'] != 'All':
                data.rows = [r for r in data.rows if r.data['status'] == filters['Status']]

            # Recalculate summary from filtered rows
            data.summary = engine._calculate_summary(data.rows)

            self.viewer.load_report(data)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Report Error", f"Failed to generate order report:\n{str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = OrderReport(folder_path=".")
    dialog.show()
    sys.exit(app.exec())
