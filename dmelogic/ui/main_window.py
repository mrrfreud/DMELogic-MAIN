"""
Main application window for DME Logic.

Phase 2: we define a real MainWindow class that currently just
inherits from the legacy PDFViewer, so behavior is identical.
Later we can move logic out of app_legacy.PDFViewer into here,
step by step, without breaking the app.
"""

from typing import Type, Iterable
from decimal import Decimal
import os
import sys
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QComboBox, QLabel, QPushButton, 
    QFrame, QSizePolicy, QDialog, QMessageBox, QTableWidget, QToolBar, QApplication, QFileDialog
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSize, Qt
from pathlib import Path

# Legacy implementation from the monolithic app
from app_legacy import PDFViewer

# Order wizard
from dmelogic.ui.order_wizard import OrderWizard, OrderWizardResult

# EPACES helper dialog
from dmelogic.ui.epaces_helper import EpacesHelperDialog

# Theme manager
from dmelogic.ui.theme_manager import ThemeManager

# DB layer for order creation
from dmelogic.db.inventory import fetch_latest_item_by_hcpcs
from dmelogic.db.patients import fetch_patient_insurance
from dmelogic.db.orders import create_order
from dmelogic.db import fetch_order_with_items
from dmelogic.db.models import OrderInput, OrderItemInput, BillingType, OrderStatus
from dmelogic.db import sticky_notes as notes_db
from dmelogic.ui.notes_board import NotesBoardDialog
from dmelogic.ui.components.sticky_notes_panel import StickyNotesPanel
from dmelogic.ui.draggable_button_bar import DraggableButtonBar


def build_orders_tab(self) -> QWidget:
    """
    Build the Orders tab UI: top filter bar, orders table, bottom summary/action panel.
    Assumes self.orders_table already exists and is configured.
    """
    tab = QWidget()
    main_layout = QVBoxLayout(tab)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(8)

    # --- Top filter bar ---
    top_bar = QHBoxLayout()
    top_bar.setSpacing(8)

    self.orders_search_edit = QLineEdit()
    self.orders_search_edit.setPlaceholderText("Search orders (patient, order #, status)...")

    self.orders_status_combo = QComboBox()
    self.orders_status_combo.addItems(["All statuses", "Unbilled", "On Hold", "Open", "Pending", "Shipped", "Delivered", "Cancelled"])

    self.orders_date_combo = QComboBox()
    # Date filters: match dashboard logic (week starts Monday, month starts 1st)
    self.orders_date_combo.addItems(["All dates", "This week", "This month", "This year"])

    top_bar.addWidget(QLabel("Search:"))
    top_bar.addWidget(self.orders_search_edit, 2)
    top_bar.addSpacing(8)
    top_bar.addWidget(QLabel("Status:"))
    top_bar.addWidget(self.orders_status_combo, 1)
    top_bar.addSpacing(8)
    top_bar.addWidget(QLabel("Date:"))
    top_bar.addWidget(self.orders_date_combo, 1)

    # Filler to push content left
    top_bar.addStretch(1)

    main_layout.addLayout(top_bar)

    # --- Orders table (existing widget) ---
    main_layout.addWidget(self.orders_table, 10)

    # --- Bottom summary / actions ---
    bottom_frame = QFrame()
    bottom_frame.setObjectName("OrdersSummaryFrame")
    bottom_layout = QHBoxLayout(bottom_frame)
    bottom_layout.setContentsMargins(10, 6, 10, 6)
    bottom_layout.setSpacing(12)

    # Summary labels
    self.orders_summary_label = QLabel("No order selected")
    self.orders_summary_label.setProperty("typo", "section")
    self.orders_sub_label = QLabel("")
    self.orders_sub_label.setProperty("typo", "caption")

    summary_layout = QVBoxLayout()
    summary_layout.setContentsMargins(0, 0, 0, 0)
    summary_layout.setSpacing(2)
    summary_layout.addWidget(self.orders_summary_label)
    summary_layout.addWidget(self.orders_sub_label)

    bottom_layout.addLayout(summary_layout, 4)

    # Spacer between summary and buttons
    bottom_layout.addStretch(1)

    # Action buttons using draggable button bar
    def _save_order_button_order(order_list):
        self.settings['order_button_order'] = order_list
        self.save_settings()
    
    self.order_button_bar = DraggableButtonBar(save_callback=_save_order_button_order)
    
    # Add all buttons with keys for identification (Orders tab)
    self.btn_edit_order = self.order_button_bar.add_button(
        "edit_order", "✏️ Edit Order", "Edit the selected order"
    )
    # Make Edit Order the primary action visually
    try:
        self.btn_edit_order.setProperty("primary", True)
        self.btn_edit_order.style().unpolish(self.btn_edit_order)
        self.btn_edit_order.style().polish(self.btn_edit_order)
    except Exception:
        pass
    self.btn_update_status = self.order_button_bar.add_button(
        "update_status", "🔄 Update Status", "Update order status"
    )
    self.btn_delivery_report = self.order_button_bar.add_button(
        "delivery_report", "📊 Delivery Report", "View delivery report"
    )
    self.btn_clear_delivery = self.order_button_bar.add_button(
        "clear_delivery", "🧹 Clear Delivery", "Set delivery date to blank for the selected order"
    )
    self.btn_process_refill = self.order_button_bar.add_button(
        "process_refill", "♻️ Process Refill", "Create a new order as a refill of the selected one"
    )
    self.btn_reverse_refill = self.order_button_bar.add_button(
        "reverse_refill", "↩️ Reverse Refill", "Undo a refill: restore refills to parent and delete the refill order"
    )
    self.btn_refill_request = self.order_button_bar.add_button(
        "refill_request", "📋 Refill Request", "Generate a fax to request new prescriptions from the provider"
    )
    
    # Batch operations section
    self.btn_batch_delivered = self.order_button_bar.add_button(
        "batch_delivered", "📦 Batch Delivered", "Mark multiple selected orders as delivered"
    )
    self.btn_batch_billed = self.order_button_bar.add_button(
        "batch_billed", "💰 Batch Billed", "Mark multiple selected orders as billed/paid"
    )
    
    self.btn_export_portal = self.order_button_bar.add_button(
        "export_portal", "📤 Export to Portal", "Export order to state portal (CSV/JSON)"
    )
    self.btn_epaces = self.order_button_bar.add_button(
        "epaces", "🔐 Bill in ePACES", "Open copy-friendly helper for manual ePACES portal entry"
    )
    self.btn_print_delivery_ticket = self.order_button_bar.add_button(
        "print_delivery_ticket", "🎫 Print Delivery Ticket", "Generate delivery ticket PDF for the selected order"
    )
    self.btn_generate_1500 = self.order_button_bar.add_button(
        "generate_1500", "📄 Generate 1500 JSON", "Generate HCFA-1500 claim data (JSON preview)"
    )
    self.btn_print_1500 = self.order_button_bar.add_button(
        "print_1500", "🖨️ Print HCFA-1500", "Generate and print CMS-1500 claim form (PDF)"
    )
    self.btn_delete_order = self.order_button_bar.add_button(
        "delete_order", "🗑️ Delete Order", "Delete the selected order"
    )
    self.btn_link_patient = self.order_button_bar.add_button(
        "link_patient", "🔗 Link to Patient", "Link order to a patient"
    )
    
    # Restore saved button order if available
    saved_order = self.settings.get('order_button_order', [])
    if saved_order:
        self.order_button_bar.set_order(saved_order)

    # Persist button order on app exit to survive restarts
    try:
        app_instance = QApplication.instance()
        if app_instance:
            def _persist_order_buttons():
                self.settings['order_button_order'] = self.order_button_bar.get_order()
                self.save_settings()
            app_instance.aboutToQuit.connect(_persist_order_buttons)
    except Exception:
        pass
    
    bottom_layout.addWidget(self.order_button_bar)

    main_layout.addWidget(bottom_frame)

    # Basic signals (you can wire these to your existing slots)
    self.orders_search_edit.textChanged.connect(self.apply_table_filters)
    self.orders_status_combo.currentIndexChanged.connect(self.apply_table_filters)
    self.orders_date_combo.currentIndexChanged.connect(self.apply_table_filters)

    return tab


def build_patients_tab(self) -> QWidget:
    """
    Build the Patients tab UI: top filter bar, patients table, bottom summary/action panel.
    Assumes self.patients_table already exists and is configured.
    """
    tab = QWidget()
    main_layout = QVBoxLayout(tab)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(8)

    # --- Top filter bar ---
    top_bar = QHBoxLayout()
    top_bar.setSpacing(8)

    self.patients_search_edit = QLineEdit()
    self.patients_search_edit.setPlaceholderText("Search patients (name, DOB, MRN)...")

    self.patients_status_combo = QComboBox()
    self.patients_status_combo.addItems(["All", "Active", "Inactive"])

    self.patients_insurance_combo = QComboBox()
    self.patients_insurance_combo.addItem("All insurances")

    top_bar.addWidget(QLabel("Search:"))
    top_bar.addWidget(self.patients_search_edit, 2)
    top_bar.addSpacing(8)
    top_bar.addWidget(QLabel("Status:"))
    top_bar.addWidget(self.patients_status_combo, 1)
    top_bar.addSpacing(8)
    top_bar.addWidget(QLabel("Insurance:"))
    top_bar.addWidget(self.patients_insurance_combo, 1)

    top_bar.addStretch(1)
    main_layout.addLayout(top_bar)
    
    # --- Recent patients row ---
    recent_bar = QHBoxLayout()
    recent_bar.setSpacing(8)
    
    recent_label = QLabel("Recent:")
    recent_label.setStyleSheet("font-weight: normal; color: #666;")
    recent_bar.addWidget(recent_label)
    
    # Create 4 recent patient buttons
    self.recent_patient_buttons = []
    for i in range(4):
        btn = QPushButton("")
        btn.setFixedHeight(30)
        btn.setMinimumWidth(200)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px 10px;
                text-align: left;
                font-size: 10pt;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
                color: #000000;
            }
            QPushButton:disabled {
                color: transparent;
                background-color: transparent;
                border: 1px dashed #dee2e6;
            }
        """)
        btn.clicked.connect(lambda checked, idx=i: self.select_recent_patient_main(idx))
        btn.setEnabled(False)
        recent_bar.addWidget(btn)
        self.recent_patient_buttons.append(btn)
    
    recent_bar.addStretch()
    main_layout.addLayout(recent_bar)

    # --- Patients table (existing widget) ---
    main_layout.addWidget(self.patients_table, 10)

    # --- Bottom summary / actions ---
    bottom_frame = QFrame()
    bottom_frame.setObjectName("PatientsSummaryFrame")
    bottom_layout = QHBoxLayout(bottom_frame)
    bottom_layout.setContentsMargins(10, 6, 10, 6)
    bottom_layout.setSpacing(12)

    # Summary labels
    self.patients_summary_label = QLabel("No patient selected")
    self.patients_summary_label.setStyleSheet("font-weight: 500; color: #333333;")
    self.patients_sub_label = QLabel("")
    self.patients_sub_label.setStyleSheet("color: #666666; font-size: 9pt;")

    summary_layout = QVBoxLayout()
    summary_layout.setContentsMargins(0, 0, 0, 0)
    summary_layout.setSpacing(2)
    summary_layout.addWidget(self.patients_summary_label)
    summary_layout.addWidget(self.patients_sub_label)

    bottom_layout.addLayout(summary_layout, 4)
    bottom_layout.addStretch(1)

    # Action buttons using draggable button bar
    def _save_patient_button_order(order_list):
        self.settings['patient_button_order'] = order_list
        self.save_settings()
    
    self.patient_button_bar = DraggableButtonBar(save_callback=_save_patient_button_order)
    
    self.btn_new_patient = self.patient_button_bar.add_button(
        "new_patient", "➕ New Patient", "Add a new patient"
    )
    self.btn_edit_patient = self.patient_button_bar.add_button(
        "edit_patient", "✏️ Edit Patient", "Edit selected patient"
    )
    self.btn_patients_view_orders = self.patient_button_bar.add_button(
        "view_orders", "📋 View Orders", "View patient's orders"
    )
    self.btn_patients_view_docs = self.patient_button_bar.add_button(
        "view_docs", "📄 View Documents", "View patient's documents"
    )
    self.btn_patients_new_order = self.patient_button_bar.add_button(
        "new_order", "🛒 New Order", "Create a new order for this patient"
    )
    self.btn_delete_patient = self.patient_button_bar.add_button(
        "delete_patient", "🗑️ Delete Patient", "Delete selected patient"
    )
    
    # Restore saved button order if available
    saved_patient_order = self.settings.get('patient_button_order', [])
    if saved_patient_order:
        self.patient_button_bar.set_order(saved_patient_order)
    
    bottom_layout.addWidget(self.patient_button_bar)

    main_layout.addWidget(bottom_frame)

    # Hook filters
    self.patients_search_edit.textChanged.connect(self.on_patients_filter_changed)
    self.patients_status_combo.currentIndexChanged.connect(self.on_patients_filter_changed)
    self.patients_insurance_combo.currentIndexChanged.connect(self.on_patients_filter_changed)

    return tab


class MainWindow(PDFViewer):
    """Primary window for the application.

    For now, this simply subclasses PDFViewer so that all existing
    behavior is preserved. Over time we will move logic from
    app_legacy.PDFViewer into this class and slim down app_legacy.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: future: inject services, db repos, etc. here
        # e.g. self.orders_repo = OrdersRepository(...)
        # Right now we keep it minimal to avoid behavior changes.
        
        # Setup theme switching menu
        self._setup_theme_menu()
        self._setup_tools_menu()
        self._setup_help_menu()

    def _get_or_create_menu(self, title_candidates: Iterable[str], fallback_title: str):
        """Return an existing menu matching one of the given titles, else create it."""
        menubar = self.menuBar()

        for act in menubar.actions():
            menu = act.menu()
            if not menu:
                continue
            normalized = menu.title().replace("&&", "&")
            if normalized in title_candidates:
                return menu

        return menubar.addMenu(fallback_title)

    @staticmethod
    def _menu_has_action(menu, text: str) -> bool:
        for act in menu.actions():
            if act.text().replace("&&", "&") == text.replace("&&", "&"):
                return True
        return False

    def _setup_help_menu(self) -> None:
        """Add Help menu actions shared by installed + USB builds."""
        help_menu = self._get_or_create_menu(("&Help", "Help"), "&Help")

        # Add a separator if the help menu already has items.
        if help_menu.actions() and not help_menu.actions()[-1].isSeparator():
            help_menu.addSeparator()

        if not self._menu_has_action(help_menu, "Update from File..."):
            self.action_update_from_file = QAction("Update from File...", self)
            self.action_update_from_file.setToolTip("Run an update installer from a file")
            self.action_update_from_file.triggered.connect(self._update_from_file)
            help_menu.addAction(self.action_update_from_file)

        if not self._menu_has_action(help_menu, "Uninstall Application..."):
            self.action_uninstall_app = QAction("Uninstall Application...", self)
            self.action_uninstall_app.setToolTip("Open the Windows uninstaller for DMELogic")
            self.action_uninstall_app.triggered.connect(self._uninstall_application)
            help_menu.addAction(self.action_uninstall_app)

    def _update_from_file(self) -> None:
        if sys.platform != "win32":
            QMessageBox.information(self, "Update", "Update from file is only supported on Windows.")
            return

        start_dir = str(Path.home())
        try:
            if getattr(sys, "frozen", False):
                start_dir = str(Path(sys.executable).resolve().parent)
        except Exception:
            pass

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Update Installer",
            start_dir,
            "Installer (*.exe)"
        )
        if not file_path:
            return

        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Update", "Selected installer file was not found.")
            return

        resp = QMessageBox.question(
            self,
            "Update",
            "This will launch the selected installer and close DMELogic. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        try:
            self._launch_windows_exe(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Update", f"Could not launch installer:\n\n{e}")
            return

        # Exit so files can be replaced during update.
        QApplication.quit()

    def _uninstall_application(self) -> None:
        if sys.platform != "win32":
            QMessageBox.information(self, "Uninstall", "Uninstall is only supported on Windows.")
            return

        resp = QMessageBox.question(
            self,
            "Uninstall Application",
            "This will launch the DMELogic uninstaller.\n\n"
            "It is recommended to run a backup first (File → Backup).\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        uninstaller = self._find_uninstaller_path()
        if uninstaller is None:
            QMessageBox.information(
                self,
                "Uninstall",
                "Could not find the automatic uninstaller.\n\n"
                "To uninstall manually:\n"
                "1) Open Windows Settings\n"
                "2) Apps → Installed apps\n"
                "3) Search for 'DMELogic'\n"
                "4) Click Uninstall",
            )
            return

        try:
            # Inno Setup uninstallers are normal EXEs. Launch detached.
            self._launch_windows_exe(str(uninstaller))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Uninstall",
                f"Could not launch uninstaller:\n\n{e}\n\n"
                "To uninstall manually, use Windows Settings → Apps → Installed apps.",
            )
            return

        QMessageBox.information(
            self,
            "Uninstall",
            "The uninstaller has been launched.\n\n"
            "DMELogic will now close.",
        )
        QApplication.quit()

    def _find_uninstaller_path(self) -> Path | None:
        """Try to locate the Inno Setup uninstaller for this app."""
        # 1) If frozen, the uninstaller is usually next to the EXE.
        try:
            if getattr(sys, "frozen", False):
                install_dir = Path(sys.executable).resolve().parent
                matches = sorted(install_dir.glob("unins*.exe"))
                if matches:
                    return matches[0]
        except Exception:
            pass

        # 2) Look in registry uninstall entries.
        try:
            import winreg

            app_id = "{8F3D5E2A-9B4C-4F1A-8D2E-5C6F7A8B9D0E}"
            display_names = {"DMELogic", "DME Logic"}

            roots = [
                winreg.HKEY_LOCAL_MACHINE,
                winreg.HKEY_CURRENT_USER,
            ]
            key_paths = [
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
            ]

            for root in roots:
                for base in key_paths:
                    try:
                        with winreg.OpenKey(root, base) as uninstall_key:
                            i = 0
                            while True:
                                try:
                                    subkey_name = winreg.EnumKey(uninstall_key, i)
                                except OSError:
                                    break
                                i += 1

                                try:
                                    with winreg.OpenKey(uninstall_key, subkey_name) as subkey:
                                        try:
                                            display = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        except OSError:
                                            display = ""

                                        if subkey_name.lower() in {f"{app_id}_is1".lower(), app_id.lower()}:
                                            pass_match = True
                                        else:
                                            pass_match = any(n.lower() in (display or "").lower() for n in display_names)

                                        if not pass_match:
                                            continue

                                        try:
                                            uninstall_str = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                        except OSError:
                                            uninstall_str = ""

                                        if not uninstall_str:
                                            continue

                                        # UninstallString can be quoted and/or include args.
                                        # Prefer to extract an unins*.exe path if present.
                                        candidate = uninstall_str.strip().strip('"')
                                        if (
                                            "unins" in candidate.lower()
                                            and candidate.lower().endswith(".exe")
                                            and os.path.exists(candidate)
                                        ):
                                            return Path(candidate)

                                        # Otherwise, return the first token if it exists.
                                        first = candidate.split(" ", 1)[0].strip('"')
                                        if first and os.path.exists(first):
                                            return Path(first)
                                except OSError:
                                    continue
                    except OSError:
                        continue
        except Exception:
            pass

        return None

    @staticmethod
    def _launch_windows_exe(exe_path: str) -> None:
        """Launch an EXE detached on Windows (with UAC prompt if required by the EXE)."""
        exe_path = os.path.abspath(exe_path)
        if not os.path.exists(exe_path):
            raise FileNotFoundError(exe_path)

        # Prefer ShellExecute so Windows handles UAC correctly.
        try:
            import ctypes

            r = ctypes.windll.shell32.ShellExecuteW(None, "open", exe_path, None, None, 1)
            if r <= 32:
                raise OSError(f"ShellExecuteW failed with code {r}")
            return
        except Exception:
            # Fallback.
            subprocess.Popen([exe_path], close_fds=True)
    
    def _setup_theme_menu(self):
        """Add View menu with theme switching options."""
        from PyQt6.QtWidgets import QApplication
        
        menubar = self.menuBar()
        
        # Create View menu
        view_menu = menubar.addMenu("&View")
        
        # Light theme action
        self.action_light_theme = QAction("Light Theme", self)
        self.action_light_theme.setCheckable(True)
        self.action_light_theme.setChecked(True)  # default
        self.action_light_theme.triggered.connect(self._set_light_theme)
        
        # Dark theme action
        self.action_dark_theme = QAction("Dark Theme", self)
        self.action_dark_theme.setCheckable(True)
        self.action_dark_theme.triggered.connect(self._set_dark_theme)
        
        view_menu.addAction(self.action_light_theme)
        view_menu.addAction(self.action_dark_theme)

    def _setup_tools_menu(self) -> None:
        """Add Tools menu and toolbar entry for sticky notes and user administration."""
        from dmelogic.security.permissions import has_permission
        
        menubar = self.menuBar()
        tools_menu = None
        for act in menubar.actions():
            menu = act.menu()
            if menu and menu.title().replace("&&", "&") in ("&Tools", "Tools"):
                tools_menu = menu
                break
        if tools_menu is None:
            tools_menu = menubar.addMenu("&Tools")

        self.action_sticky_notes = QAction("Sticky Notes", self)
        self.action_sticky_notes.setToolTip("Open global sticky notes")
        self.action_sticky_notes.triggered.connect(self.open_sticky_notes)

        tools_menu.addAction(self.action_sticky_notes)
        
        # User Administration (only visible for users with users.manage permission)
        if has_permission("users.manage"):
            tools_menu.addSeparator()
            self.action_user_admin = QAction("User Administration", self)
            self.action_user_admin.setToolTip("Manage users, roles, and permissions")
            self.action_user_admin.triggered.connect(self._open_user_admin)
            tools_menu.addAction(self.action_user_admin)
        
        # Change Password (available to all logged-in users)
        self.action_change_password = QAction("Change Password", self)
        self.action_change_password.setToolTip("Change your password")
        self.action_change_password.triggered.connect(self._open_change_password)
        tools_menu.addAction(self.action_change_password)

        toolbar = QToolBar("Tools", self)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.addAction(self.action_sticky_notes)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
    
    def _open_user_admin(self) -> None:
        """Open the User Administration dialog."""
        from dmelogic.security.permissions import has_permission
        from dmelogic.ui.admin.users_admin_dialog import UsersAdminDialog
        
        if not has_permission("users.manage"):
            QMessageBox.warning(self, "Access Denied", "You do not have permission to manage users.")
            return
        
        dialog = UsersAdminDialog(self)
        dialog.exec()
    
    def _open_change_password(self) -> None:
        """Open the Change Password dialog."""
        from dmelogic.ui.change_password_dialog import ChangePasswordDialog
        
        dialog = ChangePasswordDialog(self)
        dialog.exec()

    def open_sticky_notes(self) -> None:
        """Open the notes board (global sticky notes) as a modeless window."""
        try:
            # Reuse existing board if open
            if hasattr(self, "_notes_board") and self._notes_board and self._notes_board.isVisible():
                self._notes_board.raise_()
                self._notes_board.activateWindow()
                return
        except Exception:
            pass

        notes_db.init_notes_db(getattr(self, "folder_path", None))
        self._notes_board = NotesBoardDialog(folder_path=getattr(self, "folder_path", None), parent=self)
        self._notes_board.setModal(False)
        self._notes_board.show()
        self._notes_board.raise_()
        self._notes_board.activateWindow()
    
    def _set_light_theme(self):
        """Switch to light theme."""
        app = QApplication.instance()
        if not app:
            return
        ThemeManager.apply_theme(app, "light")
        self.action_light_theme.setChecked(True)
        self.action_dark_theme.setChecked(False)
    
    def _set_dark_theme(self):
        """Switch to dark theme."""
        app = QApplication.instance()
        if not app:
            return
        ThemeManager.apply_theme(app, "dark")
        self.action_light_theme.setChecked(False)
        self.action_dark_theme.setChecked(True)

    # -------------------- Modern Order Editor --------------------

    def open_order_editor(self, order_id: int) -> None:
        """
        Open the modern Order Editor dialog for the specified order ID.
        
        This is the new unified interface for viewing/editing orders,
        powered by the domain model (fetch_order_with_items).
        """
        from dmelogic.ui.order_editor import OrderEditorDialog
        
        folder_path = getattr(self, "folder_path", None)
        
        dialog = OrderEditorDialog(
            order_id=order_id,
            folder_path=folder_path,
            parent=self
        )
        
        # Register as child window if parent supports it
        if hasattr(self, 'register_child_window'):
            self.register_child_window(dialog)
        
        # Connect order_updated signal to refresh orders table
        def on_order_updated():
            if hasattr(self, 'load_orders'):
                self.load_orders()
        
        dialog.order_updated.connect(on_order_updated)
        
        # Show dialog modally
        dialog.exec()

        # Ensure orders grid reflects any changes made while the editor was open
        if hasattr(self, 'load_orders'):
            try:
                self.load_orders()
            except Exception:
                pass

    def edit_order_by_id_modern(self, order_id: int) -> None:
        """
        Modern wrapper for edit_order_by_id that uses the new Order Editor.
        
        This can be called from anywhere that currently calls edit_order_by_id
        to get the new modern interface instead of the legacy one.
        """
        self.open_order_editor(order_id)

    # -------------------- New Order Wizard --------------------

    def open_new_order_wizard(self, patient_context: dict | None = None, rx_context: dict | None = None) -> None:
        """
        Launch the New Order Wizard.

        patient_context: optional dict like {"name": "...", "dob": "...", "phone": "...", "patient_id": 123}
        rx_context: optional dict like {"rx_number": "...", "prescriber_name": "...", ...}
        """
        # Extract patient_id from context if available
        patient_id = (patient_context or {}).get("patient_id", 0)
        
        wizard = OrderWizard(
            self,
            patient_id=patient_id,
            folder_path=getattr(self, "folder_path", None),
            initial_patient=patient_context,
            rx_context=rx_context
        )
        
        # Register as child window if parent supports it
        if hasattr(self, 'register_child_window'):
            self.register_child_window(wizard)
        
        # Connect accepted signal
        def on_accepted():
            if wizard.result:
                self.create_order_from_wizard(wizard.result)
        
        wizard.accepted.connect(on_accepted)
        wizard.show()
        wizard.raise_()
        wizard.activateWindow()

    def create_order_from_wizard(self, result: OrderWizardResult) -> None:
        """
        Take the wizard result and create a real order in orders.db via the
        centralized DB layer (dmelogic.db.orders.create_order),
        then immediately open the full 'New DME Order' window for that order.

        - Pulls inventory data to fill item_number and cost_ea (bill amount).
        - Stores ICD-10 codes and doctor directions.
        - Tries to pull primary insurance from the patient DB (best-effort).
        """
        try:
            from datetime import datetime

            folder_path = getattr(self, "folder_path", None)

            # --- Split patient name "LAST, FIRST" (fallback to FIRST LAST) ---
            last_name = ""
            first_name = ""
            name = (result.patient_name or "").strip()
            if name:
                if "," in name:
                    parts = [p.strip() for p in name.split(",", 1)]
                    if len(parts) == 2:
                        last_name, first_name = parts[0], parts[1]
                else:
                    parts = name.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = " ".join(parts[1:])

            # --- Insurance & address (best-effort) ---
            primary_insurance = ""
            primary_insurance_id = ""
            patient_address = ""

            # Use insurance from wizard result if available
            if result.insurance_name:
                primary_insurance = result.insurance_name or ""
                primary_insurance_id = result.insurance_policy_number or ""
            elif last_name or first_name:
                try:
                    ins = fetch_patient_insurance(
                        last_name=last_name,
                        first_name=first_name,
                        dob=None,  # we already have DOB in result, but legacy code used None
                        folder_path=folder_path,
                    )
                    if ins:
                        if not primary_insurance:
                            primary_insurance = ins.primary_insurance or ""
                            primary_insurance_id = ins.primary_insurance_id or ""
                        addr_parts = [
                            ins.address or "",
                            ins.city or "",
                            ins.state or "",
                            ins.zip_code or "",
                        ]
                        patient_address = ", ".join([p for p in addr_parts if p.strip()])
                except Exception as e:
                    print("⚠️ Could not read insurance from patients.db:", e)

            # --- Build OrderItemInput list (with inventory lookup) ---
            order_items: list[OrderItemInput] = []

            for ui_item in result.items:
                hcpcs = (ui_item.hcpcs or "").strip()
                desc = (ui_item.description or "").strip()

                # Skip fully empty lines
                if not hcpcs and not desc:
                    continue

                item_number = ""
                cost_ea_dec: Decimal | None = None

                if hcpcs:
                    try:
                        inv_row = fetch_latest_item_by_hcpcs(
                            hcpcs_code=hcpcs,
                            folder_path=folder_path,
                        )
                    except Exception as e:
                        print(f"⚠️ Inventory lookup failed for {hcpcs}: {e}")
                        inv_row = None

                    if inv_row:
                        item_number = inv_row.get("item_number") or ""
                        # Retail price is our billing amount
                        retail_price = inv_row.get("retail_price")
                        if retail_price not in (None, ""):
                            try:
                                cost_ea_dec = Decimal(str(retail_price))
                            except Exception:
                                cost_ea_dec = None

                        # If description empty in UI, fall back to inventory description
                        if not desc:
                            inv_desc = inv_row.get("description")
                            if inv_desc:
                                desc = inv_desc

                # If the line has no HCPCS AND no description after all that, skip it
                if not hcpcs and not desc:
                    continue

                # Directions priority: item-level, then order-level MD directions
                directions = ui_item.directions or result.doctor_directions or ""

                order_items.append(
                    OrderItemInput(
                        hcpcs=hcpcs,
                        description=desc,
                        quantity=ui_item.quantity,
                        refills=ui_item.refills,
                        days_supply=ui_item.days_supply,
                        directions=directions,
                        item_number=item_number or None,
                        cost_ea=cost_ea_dec,
                    )
                )

            if not order_items:
                QMessageBox.warning(
                    self,
                    "Order",
                    "No valid items to create an order. Please add at least one item.",
                )
                return

            # --- Build OrderInput DTO for the DB layer ---
            # If wizard didn't provide dates for some reason, fall back to today
            today_str = datetime.now().strftime("%m/%d/%Y")
            rx_date_str = (result.rx_date or "").strip() or today_str
            order_date_str = (result.order_date or "").strip() or today_str
            delivery_date_str = (result.delivery_date or "").strip() or None

            # Billing type / status from enums (keeps consistency with DB layer)
            billing_type = (result.billing_type or "").strip() or BillingType.INSURANCE.value
            order_status = OrderStatus.PENDING.value  # new orders start Pending

            order_input = OrderInput(
                patient_last_name=last_name,
                patient_first_name=first_name,
                patient_id=result.patient_id or None,
                patient_dob=(result.patient_dob or "").strip() or None,
                patient_phone=(result.patient_phone or "").strip() or None,
                patient_address=patient_address or None,
                prescriber_name=(result.prescriber_name or "").strip() or None,
                prescriber_npi=(result.prescriber_npi or "").strip() or None,
                rx_date_2=(result.rx_date_2 or "").strip() or None,
                prescriber_name_2=(result.prescriber_name_2 or "").strip() or None,
                prescriber_npi_2=(result.prescriber_npi_2 or "").strip() or None,
                rx_date=rx_date_str,
                order_date=order_date_str,
                delivery_date=delivery_date_str,
                billing_type=billing_type,
                order_status=order_status,
                primary_insurance=primary_insurance or None,
                primary_insurance_id=primary_insurance_id or None,
                icd_code_1=(result.icd_code_1 or "").strip() or None,
                icd_code_2=(result.icd_code_2 or "").strip() or None,
                icd_code_3=(result.icd_code_3 or "").strip() or None,
                icd_code_4=(result.icd_code_4 or "").strip() or None,
                icd_code_5=(result.icd_code_5 or "").strip() or None,
                doctor_directions=(result.doctor_directions or "").strip() or None,
                notes=(result.notes or "").strip() or None,
                items=order_items,
            )

            # Let the DB layer validate and persist
            new_order_id = create_order(order_input, folder_path=folder_path)

            # Process attachment files from wizard (if any)
            if hasattr(result, 'attachment_paths') and result.attachment_paths:
                self._process_wizard_attachments(new_order_id, result.attachment_paths, folder_path, patient_id=result.patient_id)

            # Fetch the newly created order with items to show in EPACES dialog
            order = fetch_order_with_items(new_order_id, folder_path=folder_path)
            
            # Show EPACES billing cockpit instead of order editor
            epaces_dlg = EpacesHelperDialog(order=order, folder_path=folder_path, parent=self)
            epaces_dlg.exec()

            try:
                formatted = self.format_order_number(new_order_id)
            except Exception:
                formatted = str(new_order_id)

            QMessageBox.information(
                self,
                "Order Created",
                f"Order {formatted} created successfully.",
            )

            # Refresh order list if available
            try:
                if hasattr(self, "load_orders"):
                    self.load_orders()
            except Exception as e:
                print(f"⚠️ Could not refresh orders list: {e}")

        except Exception as e:
            print("❌ Error creating order from wizard:", e)
            QMessageBox.critical(
                self,
                "Error Creating Order",
                f"An error occurred while creating the order:\n{e}",
            )

    def _process_wizard_attachments(self, order_id: int, attachment_paths: list, folder_path: str = None, patient_id: int = None) -> None:
        """
        Copy attachment files from wizard to order's document folder and update DB.
        Also auto-links documents to the patient's profile.
        """
        import shutil
        from pathlib import Path
        import sqlite3
        
        if not attachment_paths:
            return
            
        try:
            from dmelogic.paths import fax_root
            
            # Create order documents folder
            order_docs_dir = fax_root() / "OrderDocuments" / f"ORD-{order_id:03d}"
            order_docs_dir.mkdir(parents=True, exist_ok=True)
            
            copied_files = []
            original_names = []
            for src_path in attachment_paths:
                try:
                    src = Path(src_path)
                    if not src.exists():
                        print(f"⚠️ Attachment not found: {src_path}")
                        continue
                    
                    dest = order_docs_dir / src.name
                    
                    # Handle duplicate names
                    counter = 1
                    while dest.exists():
                        stem = src.stem
                        suffix = src.suffix
                        dest = order_docs_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.copy2(src, dest)
                    copied_files.append(str(dest))
                    original_names.append(src.name)
                    print(f"✅ Attached: {src.name} → {dest}")
                except Exception as e:
                    print(f"⚠️ Failed to copy attachment {src_path}: {e}")
            
            if copied_files:
                # Update order's attached_rx_files field in DB
                from dmelogic.db.base import get_connection
                
                conn = get_connection("orders.db", folder_path)
                cur = conn.cursor()
                
                # Get existing attached files
                cur.execute("SELECT attached_rx_files FROM orders WHERE id = ?", (order_id,))
                row = cur.fetchone()
                current_files = row[0] if row and row[0] else ""
                
                # Build new list (append to existing if any)
                if current_files:
                    all_files = current_files + "\n" + "\n".join(copied_files)
                else:
                    all_files = "\n".join(copied_files)
                
                cur.execute(
                    "UPDATE orders SET attached_rx_files = ? WHERE id = ?",
                    (all_files, order_id)
                )
                conn.commit()
                conn.close()
                
                print(f"✅ Attached {len(copied_files)} documents to order {order_id}")
                
                # Auto-attach to patient profile
                if patient_id:
                    self._auto_attach_to_patient(patient_id, copied_files, original_names, order_id, folder_path)
                    
        except Exception as e:
            print(f"❌ Error processing wizard attachments: {e}")

    def _auto_attach_to_patient(self, patient_id: int, file_paths: list, original_names: list, order_id: int, folder_path: str = None):
        """Auto-attach order documents to patient profile."""
        try:
            import sqlite3
            from dmelogic.db.base import resolve_db_path
            
            patient_db_path = resolve_db_path("patients.db", folder_path=folder_path)
            conn = sqlite3.connect(patient_db_path)
            cur = conn.cursor()
            
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patient_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    description TEXT,
                    original_name TEXT,
                    stored_path TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            
            order_num = f"ORD-{order_id:03d}"
            
            for file_path, orig_name in zip(file_paths, original_names):
                # Check if already linked (avoid duplicates)
                cur.execute(
                    "SELECT id FROM patient_documents WHERE patient_id = ? AND stored_path = ?",
                    (patient_id, file_path)
                )
                if cur.fetchone():
                    continue
                
                description = f"From {order_num}"
                cur.execute(
                    "INSERT INTO patient_documents (patient_id, description, original_name, stored_path) VALUES (?, ?, ?, ?)",
                    (patient_id, description, orig_name, file_path)
                )
            
            conn.commit()
            conn.close()
            print(f"✅ Auto-attached {len(file_paths)} documents to patient {patient_id}")
            
        except Exception as e:
            print(f"⚠️ Failed to auto-attach documents to patient: {e}")

    def on_new_order_from_patients(self) -> None:
        """Start wizard using selected patient (if any) as context."""
        patient = None
        try:
            # If you have a patients_table model, pull name/dob/phone from current row
            model = self.patients_table.model()
            sel = self.patients_table.selectionModel()
            if sel.hasSelection():
                row = sel.currentIndex().row()
                # adjust column indices to your actual model
                last_name = model.index(row, 0).data() or ""
                first_name = model.index(row, 1).data() or ""
                dob = model.index(row, 2).data() or ""
                phone = model.index(row, 3).data() or ""
                
                # Try to get patient_id from Qt.UserRole stored in first column
                patient_id = 0
                first_item = self.patients_table.item(row, 0)
                if first_item:
                    stored_id = first_item.data(Qt.ItemDataRole.UserRole)
                    if stored_id is not None:
                        patient_id = int(stored_id)
                
                patient = {
                    "patient_id": patient_id,
                    "name": f"{last_name}, {first_name}".strip(", "),
                    "dob": dob,
                    "phone": phone,
                }
        except Exception:
            patient = None

        self.open_new_order_wizard(patient_context=patient)

    def on_create_order_from_rx(self) -> None:
        """
        Launch the order wizard using current document / OCR
        context to pre-fill RX & prescriber where possible.
        """
        rx_ctx = {}

        try:
            # If you already parse OCR into some fields, pull them here.
            # These are placeholders – wire to your real attributes later.
            if hasattr(self, "current_ocr_data") and self.current_ocr_data:
                data = self.current_ocr_data
                rx_ctx = {
                    "rx_date": data.get("rx_date", ""),  # Changed from rx_number to rx_date
                    "prescriber_name": data.get("prescriber_name", ""),
                    "prescriber_npi": data.get("prescriber_npi", ""),
                    "prescriber_phone": data.get("prescriber_phone", ""),
                }
        except Exception:
            rx_ctx = {}

        self.open_new_order_wizard(rx_context=rx_ctx)

    def setup_inventory_tab(self) -> QWidget:
        """
        Modern Inventory tab:
        - Compact header with search
        - Colored action buttons
        - Styled table
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # --- Header: title + search ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title = QLabel("Inventory Management System")
        title.setObjectName("inventoryTitle")
        title.setStyleSheet("font-size: 15px; font-weight: 600;")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self.inventory_search_edit = QLineEdit()
        self.inventory_search_edit.setPlaceholderText("Search inventory by name, HCPCS, or description…")
        self.inventory_search_edit.setClearButtonEnabled(True)
        self.inventory_search_edit.setMinimumWidth(260)
        header_layout.addWidget(self.inventory_search_edit)

        layout.addLayout(header_layout)

        # --- Action toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        def make_btn(text: str, color: str) -> QPushButton:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("designRole", "inventoryAction")
            btn.setStyleSheet(
                f"""
                QPushButton[designRole="inventoryAction"] {{
                    background-color: {color};
                    color: #ffffff;
                    border-radius: 4px;
                    padding: 5px 12px;
                    font-weight: 500;
                }}
                QPushButton[designRole="inventoryAction"]:hover {{
                    background-color: {color};
                    border: 1px solid #ffffff;
                }}
                """
            )
            return btn

        self.btn_inventory_add = make_btn("Add Item", "#1E8E3E")          # green
        self.btn_inventory_edit = make_btn("Edit Item", "#1967D2")        # blue
        self.btn_inventory_delete = make_btn("Delete Item", "#D93025")    # red
        self.btn_inventory_duplicate = make_btn("Duplicate Item", "#5F6368")  # grey
        self.btn_inventory_reports = make_btn("Generate Reports", "#7B1FA2")
        self.btn_inventory_dashboard = make_btn("Reports Dashboard", "#512DA8")

        toolbar.addWidget(self.btn_inventory_add)
        toolbar.addWidget(self.btn_inventory_edit)
        toolbar.addWidget(self.btn_inventory_delete)
        toolbar.addWidget(self.btn_inventory_duplicate)
        toolbar.addWidget(self.btn_inventory_reports)
        toolbar.addWidget(self.btn_inventory_dashboard)
        toolbar.addStretch(1)

        layout.addLayout(toolbar)

        # --- Table ---
        # Reuse existing table or create new one
        if hasattr(self, 'inventory_table') and isinstance(self.inventory_table, QTableWidget):
            # Use existing table from legacy
            table = self.inventory_table
        else:
            # Create new table with proper column setup
            table = QTableWidget()
            self.inventory_table = table
            
            # Set up columns (12 columns for inventory)
            table.setColumnCount(12)
            table.setHorizontalHeaderLabels([
                "ITEM ID", "HCPCS", "DESCRIPTION", "CATEGORY", "COST", "BILL AMOUNT", 
                "BRAND", "SOURCE", "STOCK", "REORDER LEVEL", "LAST USED", "LAST RESTOCKED"
            ])
            
            # Set column widths
            header = table.horizontalHeader()
            header.resizeSection(0, 80)    # Item ID
            header.resizeSection(1, 180)   # HCPCS Code
            header.resizeSection(2, 300)   # Description
            header.resizeSection(3, 120)   # Category
            header.resizeSection(4, 80)    # Cost
            header.resizeSection(5, 100)   # Bill Amount
            header.resizeSection(6, 150)   # Brand
            header.resizeSection(7, 150)   # Source
            header.resizeSection(8, 80)    # Stock
            header.resizeSection(9, 120)   # Reorder Level
            header.resizeSection(10, 150)  # Last Used
            header.resizeSection(11, 150)  # Last Restocked
        
        table.setObjectName("inventoryTable")
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable double-click to edit
        if hasattr(self, 'edit_inventory_item'):
            table.itemDoubleClicked.connect(self.edit_inventory_item)

        layout.addWidget(table, 1)

        # --- Footer / status strip (low stock summary) ---
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(12)

        self.inventory_summary_label = QLabel("Ready • 0 inventory items")
        self.inventory_summary_label.setStyleSheet("color: #A0A0A0; font-size: 10px;")
        footer.addWidget(self.inventory_summary_label)

        footer.addStretch(1)

        self.inventory_low_stock_btn = QPushButton("⚠ Low Stock Report")
        self.inventory_low_stock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.inventory_low_stock_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #F9AB00;
                color: #202124;
                border-radius: 4px;
                padding: 3px 10px;
                font-weight: 500;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #FBBC04;
                border: 1px solid #EA8600;
            }
            """
        )
        footer.addWidget(self.inventory_low_stock_btn)

        layout.addLayout(footer)

        # Wire interactions (using existing legacy methods)
        if hasattr(self, 'search_inventory'):
            self.inventory_search_edit.textChanged.connect(self.search_inventory)
        if hasattr(self, 'add_inventory_item'):
            self.btn_inventory_add.clicked.connect(self.add_inventory_item)
        if hasattr(self, 'edit_inventory_item'):
            self.btn_inventory_edit.clicked.connect(self.edit_inventory_item)
        if hasattr(self, 'delete_inventory_item'):
            self.btn_inventory_delete.clicked.connect(self.delete_inventory_item)
        if hasattr(self, 'duplicate_inventory_item'):
            self.btn_inventory_duplicate.clicked.connect(self.duplicate_inventory_item)
        if hasattr(self, 'open_inventory_reports_dialog'):
            self.btn_inventory_reports.clicked.connect(self.open_inventory_reports_dialog)
        if hasattr(self, 'open_reports_dashboard_standalone'):
            self.btn_inventory_dashboard.clicked.connect(self.open_reports_dashboard_standalone)
        if hasattr(self, 'show_low_stock_report'):
            self.inventory_low_stock_btn.clicked.connect(self.show_low_stock_report)
        return page

    def update_inventory_summary(self) -> None:
        """Update the inventory summary label with item count and low stock info"""
        if not hasattr(self, 'inventory_table') or not self.inventory_table:
            if hasattr(self, 'inventory_summary_label'):
                self.inventory_summary_label.setText("Ready • 0 inventory items")
            return

        table = self.inventory_table
        total = table.rowCount()

        # Count low stock items (assuming STOCK is column 8, REORDER LEVEL is column 9)
        low_stock = 0
        try:
            for row in range(total):
                stock_item = table.item(row, 8)
                reorder_item = table.item(row, 9)
                if stock_item and reorder_item:
                    try:
                        stock = int(stock_item.text() or 0)
                        reorder = int(reorder_item.text() or 0)
                        if reorder > 0 and stock <= reorder:
                            low_stock += 1
                    except (ValueError, AttributeError):
                        pass
        except Exception:
            pass

        text = f"Loaded {total} inventory items"
        if low_stock:
            text += f" • ⚠ {low_stock} items low stock"

        if hasattr(self, 'inventory_summary_label'):
            self.inventory_summary_label.setText(text)


def get_main_window_class() -> Type[QMainWindow]:
    """Return the main window class used by the application."""
    return MainWindow


def create_main_window() -> QMainWindow:
    """Factory used by the new entrypoint (app.py)."""
    return MainWindow()
