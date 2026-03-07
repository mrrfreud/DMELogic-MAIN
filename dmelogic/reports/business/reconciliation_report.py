"""Reconciliation Report - Migrated to Foundation"""
from typing import List, Dict, Any
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from dmelogic.reports.base import ReportEngine, ReportColumn, ReportRow
from dmelogic.reports.ui import ReportViewer


class ReconciliationReportEngine(ReportEngine):
    def get_report_title(self) -> str:
        return "📊 Reconciliation Report"

    def get_columns(self) -> List[ReportColumn]:
        return [
            ReportColumn("date", "Date", data_type="date", alignment="center"),
            ReportColumn("category", "Category"),
            ReportColumn("expected", "Expected", data_type="currency", alignment="right"),
            ReportColumn("actual", "Actual", data_type="currency", alignment="right"),
            ReportColumn("variance", "Variance", data_type="currency", alignment="right"),
        ]

    def _fetch_data(self) -> List[Dict[str, Any]]:
        rows = self.execute_query(
            "billing.db",
            """
            SELECT strftime('%Y-%m-01', COALESCE(claim_date, created_date)) as date,
                   'Claims' as category,
                   SUM(COALESCE(claim_amount, 0)) as expected,
                   SUM(COALESCE(paid_amount, 0)) as actual
            FROM claims
            WHERE claim_date IS NOT NULL OR created_date IS NOT NULL
            GROUP BY strftime('%Y-%m', COALESCE(claim_date, created_date))
            ORDER BY date DESC
            LIMIT 500
            """
        )
        return [{'date': self.parse_date(r['date']), 'category': r['category'],
                 'expected': float(r['expected'] or 0), 'actual': float(r['actual'] or 0),
                 'variance': float(r['actual'] or 0) - float(r['expected'] or 0)} for r in rows]


class ReconciliationReport(QDialog):
    def __init__(self, parent=None, folder_path=None):
        super().__init__(parent)
        self.folder_path = folder_path or "."
        self.setWindowTitle("📊 Reconciliation Report")
        self.setModal(False)
        self.resize(1400, 800)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.viewer = ReportViewer(show_filters=True)
        self.viewer.add_filter_date_range("Start", "End")
        self.viewer.refresh_requested.connect(self._generate_report)
        layout.addWidget(self.viewer)
        self._generate_report(self.viewer.get_filter_values())

    def _generate_report(self, filters=None):
        try:
            engine = ReconciliationReportEngine(self.folder_path)
            data = engine.generate()
            # Apply date range filter
            if filters:
                sd, ed = filters.get('start_date'), filters.get('end_date')
                if sd and ed:
                    data.rows = [r for r in data.rows
                                 if r.data.get('date') and sd <= r.data['date'] <= ed]
            data.summary = engine._calculate_summary(data.rows)
            self.viewer.load_report(data)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed: {e}")
