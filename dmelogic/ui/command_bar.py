"""
Command Bar / Quick Launcher (Ctrl+K)
=====================================
Global search palette that finds inventory items, orders, patients,
and navigates to any tab — inspired by VS Code / Spotlight.

Feature #4: Command Bar with Global Search

Integration:
    In MainWindow.__init__(), add:
        from dmelogic.ui.command_bar import CommandBar
        self.command_bar = CommandBar(self)
"""

from __future__ import annotations

import sqlite3
from typing import Optional, List, Dict, Any, Callable

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QListWidget, QListWidgetItem, QWidget, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QShortcut, QKeySequence, QKeyEvent

from dmelogic.db.base import get_connection


class CommandBarResult:
    """Single search result item."""

    def __init__(
        self,
        icon: str,
        title: str,
        subtitle: str,
        category: str,
        action: Optional[Callable] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        self.icon = icon
        self.title = title
        self.subtitle = subtitle
        self.category = category
        self.action = action
        self.data = data


class CommandBar(QDialog):
    """
    Quick-launch command bar accessible via Ctrl+K.

    Searches across:
    - Navigation (tabs)
    - Inventory items (HCPCS, description)
    - Orders (order #, patient name)
    - Patients (name, DOB)
    - Actions (New Order, Add Item, etc.)

    Usage:
        bar = CommandBar(main_window)
        # Ctrl+K shortcut is auto-registered on the parent.
    """

    result_activated = pyqtSignal(object)  # emits CommandBarResult

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.main_window = parent

        self.setWindowTitle("Quick Search")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setModal(True)
        self.resize(560, 420)

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(150)
        self._debounce_timer.timeout.connect(self._do_search)

        self._setup_ui()
        self._register_shortcut()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container with border
        container = QWidget()
        container.setObjectName("CommandBarContainer")
        container.setStyleSheet("""
            QWidget#CommandBarContainer {
                background-color: #1E1E2E;
                border: 1px solid #45475A;
                border-radius: 12px;
            }
        """)
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(12, 12, 12, 12)
        clayout.setSpacing(8)

        # Search input
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        icon_label = QLabel("🔍")
        icon_label.setFixedWidth(24)
        search_row.addWidget(icon_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inventory, orders, patients, or type a command…")
        self.search_input.setFont(QFont("Segoe UI", 12))
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #CDD6F4;
                padding: 6px 0px;
                font-size: 13px;
            }
        """)
        self.search_input.textChanged.connect(self._on_text_changed)
        self.search_input.installEventFilter(self)
        search_row.addWidget(self.search_input, 1)

        shortcut_label = QLabel("ESC")
        shortcut_label.setStyleSheet("""
            QLabel {
                background: #313244;
                color: #6C7086;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 10px;
            }
        """)
        search_row.addWidget(shortcut_label)

        clayout.addLayout(search_row)

        # Separator
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #313244;")
        clayout.addWidget(sep)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: #CDD6F4;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
                margin: 1px 0px;
            }
            QListWidget::item:selected {
                background-color: #313244;
            }
            QListWidget::item:hover {
                background-color: #2A2A3C;
            }
        """)
        self.results_list.setFont(QFont("Segoe UI", 10))
        self.results_list.itemActivated.connect(self._on_item_activated)
        self.results_list.itemDoubleClicked.connect(self._on_item_activated)
        clayout.addWidget(self.results_list, 1)

        # Hint bar
        hint = QLabel("↑↓ Navigate  •  Enter Select  •  Esc Close")
        hint.setStyleSheet("color: #585B70; font-size: 10px; padding: 4px 0;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clayout.addWidget(hint)

        layout.addWidget(container)

        # Show default items
        self._show_defaults()

    def _register_shortcut(self):
        """Register Ctrl+K on the parent window to open the bar."""
        try:
            shortcut = QShortcut(QKeySequence("Ctrl+K"), self.main_window)
            shortcut.activated.connect(self.toggle)
        except Exception:
            pass

    # ------------------------------------------------------------------ Show / Hide

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_bar()

    def show_bar(self):
        """Open the command bar centered over the parent."""
        self.search_input.clear()
        self._show_defaults()

        parent = self.main_window
        if parent:
            geo = parent.geometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + 80
            self.move(x, y)

        self.show()
        self.raise_()
        self.search_input.setFocus()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self.results_list.setFocus()
            self.results_list.keyPressEvent(event)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current = self.results_list.currentItem()
            if current:
                self._on_item_activated(current)
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.search_input and hasattr(event, 'key'):
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                self.results_list.setFocus()
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------ Search

    def _on_text_changed(self, text: str):
        self._debounce_timer.start()

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            self._show_defaults()
            return

        results: List[CommandBarResult] = []

        # 1) Navigation commands
        results.extend(self._search_navigation(query))

        # 2) Actions
        results.extend(self._search_actions(query))

        # 3) Inventory
        results.extend(self._search_inventory(query))

        # 4) Orders
        results.extend(self._search_orders(query))

        # 5) Patients
        results.extend(self._search_patients(query))

        self._display_results(results)

    def _show_defaults(self):
        """Show default navigation + recent actions."""
        defaults = self._get_navigation_items() + self._get_action_items()
        self._display_results(defaults)

    def _display_results(self, results: List[CommandBarResult]):
        self.results_list.clear()
        for r in results[:20]:  # Cap at 20
            text = f"{r.icon}  {r.title}"
            if r.subtitle:
                text += f"  —  {r.subtitle}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    # ------------------------------------------------------------------ Sources

    def _get_navigation_items(self) -> List[CommandBarResult]:
        """Tab navigation entries."""
        tabs = [
            ("📊", "Dashboard", "Overview & stats", "dashboard"),
            ("📋", "Orders", "View and manage orders", "orders"),
            ("👥", "Patients", "Patient management", "patients"),
            ("📦", "Inventory", "Inventory items", "inventory"),
            ("♻️", "Refills", "Refill tracking", "refills"),
        ]
        results = []
        for icon, name, desc, tab_key in tabs:
            results.append(CommandBarResult(
                icon=icon, title=f"Go to {name}", subtitle=desc,
                category="Navigation",
                action=lambda k=tab_key: self._navigate_to_tab(k),
            ))
        return results

    def _get_action_items(self) -> List[CommandBarResult]:
        """Quick action entries."""
        actions = [
            ("🛒", "New Order", "Create a new DME order", "_action_new_order"),
            ("➕", "Add Inventory Item", "Add a new item to inventory", "_action_add_inventory"),
            ("➕", "New Patient", "Add a new patient", "_action_new_patient"),
            ("📝", "Sticky Notes", "Open sticky notes board", "_action_sticky_notes"),
        ]
        results = []
        for icon, name, desc, method in actions:
            results.append(CommandBarResult(
                icon=icon, title=name, subtitle=desc,
                category="Action",
                action=lambda m=method: self._run_action(m),
            ))
        return results

    def _search_navigation(self, query: str) -> List[CommandBarResult]:
        q = query.lower()
        return [r for r in self._get_navigation_items()
                if q in r.title.lower() or q in r.subtitle.lower()]

    def _search_actions(self, query: str) -> List[CommandBarResult]:
        q = query.lower()
        return [r for r in self._get_action_items()
                if q in r.title.lower() or q in r.subtitle.lower()]

    def _search_inventory(self, query: str) -> List[CommandBarResult]:
        """Search inventory.db for matching items."""
        results = []
        try:
            folder_path = getattr(self.main_window, "folder_path", None)
            conn = get_connection("inventory.db", folder_path=folder_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT hcpcs_code, description, category, retail_price, stock_quantity
                FROM inventory
                WHERE hcpcs_code LIKE ? OR description LIKE ? OR category LIKE ?
                ORDER BY hcpcs_code
                LIMIT 8
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            for row in cur.fetchall():
                hcpcs = row["hcpcs_code"] or ""
                desc = row["description"] or ""
                cat = row["category"] or ""
                price = row["retail_price"] or ""
                stock = row["stock_quantity"] if row["stock_quantity"] is not None else "?"

                results.append(CommandBarResult(
                    icon="📦",
                    title=f"{hcpcs} — {desc}",
                    subtitle=f"{cat} • ${price} • Stock: {stock}",
                    category="Inventory",
                    action=lambda h=hcpcs: self._navigate_to_inventory(h),
                    data=dict(row),
                ))
            conn.close()
        except Exception as e:
            print(f"Command bar inventory search error: {e}")
        return results

    def _search_orders(self, query: str) -> List[CommandBarResult]:
        """Search orders.db for matching orders."""
        results = []
        try:
            folder_path = getattr(self.main_window, "folder_path", None)
            conn = get_connection("orders.db", folder_path=folder_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, patient_name, order_status, order_date, billing_type
                FROM orders
                WHERE CAST(id AS TEXT) LIKE ?
                   OR patient_name LIKE ?
                   OR order_status LIKE ?
                ORDER BY id DESC
                LIMIT 8
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            for row in cur.fetchall():
                oid = row["id"]
                name = row["patient_name"] or "Unknown"
                status = row["order_status"] or ""
                odate = row["order_date"] or ""

                results.append(CommandBarResult(
                    icon="📋",
                    title=f"ORD-{oid:03d} — {name}",
                    subtitle=f"{status} • {odate}",
                    category="Order",
                    action=lambda o=oid: self._open_order(o),
                    data=dict(row),
                ))
            conn.close()
        except Exception as e:
            print(f"Command bar order search error: {e}")
        return results

    def _search_patients(self, query: str) -> List[CommandBarResult]:
        """Search patients.db for matching patients."""
        results = []
        try:
            folder_path = getattr(self.main_window, "folder_path", None)
            conn = get_connection("patients.db", folder_path=folder_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, last_name, first_name, dob, phone
                FROM patients
                WHERE last_name LIKE ? OR first_name LIKE ? OR phone LIKE ?
                ORDER BY last_name, first_name
                LIMIT 8
                """,
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            for row in cur.fetchall():
                pid = row["id"]
                name = f"{row['last_name'] or ''}, {row['first_name'] or ''}".strip(", ")
                dob = row["dob"] or ""
                phone = row["phone"] or ""

                results.append(CommandBarResult(
                    icon="👤",
                    title=name,
                    subtitle=f"DOB: {dob} • {phone}",
                    category="Patient",
                    action=lambda p=pid: self._navigate_to_patient(p),
                    data=dict(row),
                ))
            conn.close()
        except Exception:
            pass
        return results

    # ------------------------------------------------------------------ Actions

    def _on_item_activated(self, item: QListWidgetItem):
        result: CommandBarResult = item.data(Qt.ItemDataRole.UserRole)
        if result and result.action:
            self.hide()
            try:
                result.action()
            except Exception as e:
                print(f"Command bar action error: {e}")

    def _navigate_to_tab(self, tab_key: str):
        """Switch to a specific tab by name."""
        win = self.main_window
        if not hasattr(win, "tabs"):
            return
        tabs = win.tabs
        tab_map = {
            "dashboard": "Dashboard",
            "orders": "Orders",
            "patients": "Patients",
            "inventory": "Inventory",
            "refills": "Refill",
        }
        target = tab_map.get(tab_key, "")
        for i in range(tabs.count()):
            if target.lower() in tabs.tabText(i).lower():
                tabs.setCurrentIndex(i)
                return

    def _navigate_to_inventory(self, hcpcs: str):
        """Switch to inventory tab and search for the HCPCS code."""
        self._navigate_to_tab("inventory")
        win = self.main_window
        if hasattr(win, "inventory_search_edit"):
            win.inventory_search_edit.setText(hcpcs)

    def _navigate_to_patient(self, patient_id: int):
        """Switch to patients tab."""
        self._navigate_to_tab("patients")

    def _open_order(self, order_id: int):
        """Open the order editor for the given order."""
        win = self.main_window
        if hasattr(win, "open_order_editor"):
            win.open_order_editor(order_id)
        elif hasattr(win, "edit_order_by_id"):
            win.edit_order_by_id(order_id)

    def _run_action(self, method_name: str):
        """Run a named action on the main window."""
        win = self.main_window
        actions_map = {
            "_action_new_order": lambda: (
                win.open_new_order_wizard() if hasattr(win, "open_new_order_wizard")
                else None
            ),
            "_action_add_inventory": lambda: (
                win.add_inventory_item() if hasattr(win, "add_inventory_item")
                else None
            ),
            "_action_new_patient": lambda: (
                win.add_patient() if hasattr(win, "add_patient")
                else None
            ),
            "_action_sticky_notes": lambda: (
                win.open_sticky_notes() if hasattr(win, "open_sticky_notes")
                else None
            ),
        }
        action = actions_map.get(method_name)
        if action:
            action()
