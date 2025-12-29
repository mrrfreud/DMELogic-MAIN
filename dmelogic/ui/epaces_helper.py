# dmelogic/ui/epaces_helper.py

from __future__ import annotations

import sqlite3
from typing import Optional
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QTableWidget,
    QHeaderView,
    QLineEdit,
    QWidget,
    QSizePolicy,
    QSpacerItem,
    QPushButton,
    QMessageBox,
)

from dmelogic.models import Order, OrderItem, OrderStatus
from dmelogic.db.order_workflow import update_order_status_validated
from dmelogic.db.patients import fetch_patient_by_id
from dmelogic.db.base import resolve_db_path
from dmelogic.services.patient_address import get_patient_full_address


def _copy(text: str) -> None:
    """Copy text to clipboard (safe on empty)."""
    QGuiApplication.clipboard().setText(text or "")


def _make_value_copier(value: str):
    """Return a slot that copies a specific value."""
    def _slot(_checked: bool = False) -> None:
        _copy(value)
    return _slot


class EpacesHelperDialog(QDialog):
    """
    Helper dialog for manually billing an order in ePACES.

    Header shows:
      - Patient
      - Primary Insurance + ID
      - Secondary Insurance + ID (if present)
      - Prescriber + NPI
      - ICD-10 codes (each with a copy button)

    Items grid columns:
      ITEM | HCPCS | QTY | AMOUNT | MD DIRECTIONS | PA #

      - ITEM: Item # from inventory profile + Copy
      - HCPCS: HCPCS code (e.g. A6530) + Copy
      - QTY: quantity + Copy
      - AMOUNT: line total + Copy
      - MD DIRECTIONS: prescription directions + Copy
      - PA #: editable text field with Copy button (saved to order)

    Bottom:
      - Claim Total: <sum of amounts> + Copy
      - Mark as Billed
      - Close
    """

    def __init__(
        self,
        order: Order,
        folder_path: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.order = order
        self.folder_path = folder_path

        # DEBUG: Check order at init
        print(f"EPACES __init__: Received order {order.id}")
        print(f"EPACES __init__: order.patient_last_name = {getattr(order, 'patient_last_name', 'NO ATTR')}")
        print(f"EPACES __init__: order.patient_first_name = {getattr(order, 'patient_first_name', 'NO ATTR')}")
        print(f"EPACES __init__: order.patient_id = {getattr(order, 'patient_id', 'NO ATTR')}")

        # raw numeric string for claim total
        self._claim_total_raw: str = "0.00"
        # for copying IDs
        self._primary_ins_id: str = ""
        self._secondary_ins_id: str = ""
        
        # Track PA# edits for each item (item_id -> QLineEdit)
        self._pa_edits: dict[int, QLineEdit] = {}

        self.setObjectName("EpacesHelperDialog")
        self.setWindowTitle(f"EPACES – Order {order.id}")
        self.setModal(False)

        self.resize(1400, 750)  # Increased from 1200x700 to accommodate wider columns
        self.setMinimumSize(1300, 700)  # Increased from 1100x650

        # Allow minimize/maximize
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )

        # Local styling
        self.setStyleSheet(
            """
            #EpacesHelperDialog {
                font-size: 11pt;
            }
            #EpacesHelperDialog QLabel {
                font-weight: 600;
            }
            #EpacesHelperDialog QLineEdit {
                font-size: 11pt;
                padding: 4px 6px;
            }
            #EpacesHelperDialog QTableWidget {
                font-size: 11pt;
            }
            #EpacesHelperDialog QToolButton#copyTool {
                padding: 0px 5px;
                min-width: 48px;
                min-height: 20px;
                border-radius: 4px;
                border: 1px solid #999;
                background-color: #f5f5f5;
                font-size: 8pt;
                font-weight: 500;
            }
            #EpacesHelperDialog QToolButton#copyTool:hover {
                background-color: #e0e0e0;
            }
            #EpacesHelperDialog QToolButton#copyTool:pressed {
                background-color: #d0d0d0;
            }
            """
        )

        self._build_ui()
        self._bind_data()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(18)  # Increased vertical spacing

        # === Header block ================================================
        header = QWidget(self)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)  # Increased padding
        header_layout.setSpacing(10)  # Increased spacing

        # Row 1: Pt name + Primary Member ID
        row1 = QHBoxLayout()
        row1.setSpacing(10)  # Increased horizontal spacing

        self.lbl_patient_name = QLabel("")
        self.lbl_patient_name.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row1.addWidget(QLabel("Pt Name:"))
        row1.addWidget(self.lbl_patient_name, 2)

        btn_pt = self._make_copy_button(
            "Copy patient name",
            lambda: _copy(self.lbl_patient_name.text()),
        )
        row1.addWidget(btn_pt)

        self.lbl_primary_member = QLabel("")
        self.lbl_primary_member.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row1.addSpacing(24)
        row1.addWidget(QLabel("Primary ID:"))
        row1.addWidget(self.lbl_primary_member, 2)

        btn_primary_id = self._make_copy_button(
            "Copy primary member ID",
            lambda: _copy(self._primary_ins_id),
        )
        row1.addWidget(btn_primary_id)

        header_layout.addLayout(row1)

        # Row 2: Prescriber + NPI
        row2 = QHBoxLayout()
        row2.setSpacing(10)  # Increased horizontal spacing

        self.lbl_prescriber = QLabel("")
        self.lbl_prescriber.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row2.addWidget(QLabel("Prescriber:"))
        row2.addWidget(self.lbl_prescriber, 2)

        btn_presc = self._make_copy_button(
            "Copy prescriber name",
            lambda: _copy(self.lbl_prescriber.text()),
        )
        row2.addWidget(btn_presc)

        self.lbl_npi = QLabel("")
        self.lbl_npi.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row2.addSpacing(24)
        row2.addWidget(QLabel("NPI #:"))
        row2.addWidget(self.lbl_npi, 2)

        btn_npi = self._make_copy_button(
            "Copy NPI",
            lambda: _copy(self.lbl_npi.text()),
        )
        row2.addWidget(btn_npi)

        header_layout.addLayout(row2)

        # Row 3: Primary/Secondary insurance
        row3 = QHBoxLayout()
        row3.setSpacing(10)  # Increased horizontal spacing

        self.lbl_primary_ins = QLabel("")
        self.lbl_primary_ins.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row3.addWidget(QLabel("Primary Ins:"))
        row3.addWidget(self.lbl_primary_ins, 2)

        btn_copy_primary_line = self._make_copy_button(
            "Copy primary insurance ID",
            lambda: _copy(self._primary_ins_id),
        )
        row3.addWidget(btn_copy_primary_line)

        self.lbl_secondary_ins = QLabel("")
        self.lbl_secondary_ins.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row3.addSpacing(24)
        row3.addWidget(QLabel("Secondary Ins:"))
        row3.addWidget(self.lbl_secondary_ins, 2)

        btn_copy_secondary_line = self._make_copy_button(
            "Copy secondary insurance ID",
            lambda: _copy(self._secondary_ins_id),
        )
        row3.addWidget(btn_copy_secondary_line)

        header_layout.addLayout(row3)

        # Row 4: Condensed patient address
        row_addr = QHBoxLayout()
        row_addr.setSpacing(10)  # Increased horizontal spacing

        self.lbl_address_line = QLabel("")
        self.lbl_address_line.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        row_addr.addWidget(QLabel("Address:"))
        row_addr.addWidget(self.lbl_address_line, 1)

        btn_addr_copy = self._make_copy_button(
            "Copy full address line",
            lambda: _copy(self.lbl_address_line.text()),
        )
        row_addr.addWidget(btn_addr_copy)

        header_layout.addLayout(row_addr)

        # Row 5: ICD-10 list
        icd_row = QHBoxLayout()
        icd_row.setSpacing(10)  # Increased horizontal spacing
        icd_row.addWidget(QLabel("ICD-10:"))

        self.icd_codes_container = QWidget(self)
        self.icd_codes_layout = QVBoxLayout(self.icd_codes_container)
        self.icd_codes_layout.setContentsMargins(0, 0, 0, 0)
        self.icd_codes_layout.setSpacing(4)
        icd_row.addWidget(self.icd_codes_container, 1)

        header_layout.addLayout(icd_row)

        layout.addWidget(header)

        # === Items table ==================================================
        # Columns:
        # 0: ITEM (inventory item number)
        # 1: HCPCS
        # 2: QTY
        # 3: AMOUNT
        # 4: MD DIRECTIONS
        # 5: PA #
        self.items_table = QTableWidget(0, 6, self)
        self.items_table.setHorizontalHeaderLabels(
            ["ITEM", "HCPCS", "QTY", "AMOUNT", "MD DIRECTIONS", "PA #"]
        )

        header_view = self.items_table.horizontalHeader()
        # ITEM column: increased width for item numbers + Copy button
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(0, 160)  # Increased from 120
        # HCPCS column: increased width for codes + Copy button
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(1, 140)  # Increased from 100
        # QTY: fixed width to accommodate number + Copy button
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(2, 120)  # Fixed size instead of auto
        # AMOUNT: fixed width to accommodate currency + Copy button
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(3, 140)  # Fixed size instead of auto
        # MD DIRECTIONS: increased width for longer text
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(4, 320)  # Increased from 280
        # PA #: increased width for 12 characters + Copy button
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(5, 280)  # Increased from 250

        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set default row height for better visibility
        self.items_table.verticalHeader().setDefaultSectionSize(42)

        layout.addWidget(self.items_table, 1)

        # === Claim total row =============================================
        total_row = QHBoxLayout()
        total_row.setSpacing(10)  # Increased spacing

        total_row.addItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
        )

        self.lbl_claim_total = QLabel("Claim Total: 0.00")
        total_row.addWidget(self.lbl_claim_total)

        btn_total_copy = self._make_copy_button(
            "Copy claim total",
            lambda: _copy(self._claim_total_raw),
        )
        total_row.addWidget(btn_total_copy)

        layout.addLayout(total_row)

        # === Delivery info row (moved from header) =======================
        delivery_row = self._build_delivery_info_row()
        layout.addLayout(delivery_row)

        # === Bottom buttons ===============================================
        bottom = QHBoxLayout()
        bottom.setSpacing(12)  # Increased button spacing

        self.btn_save_delivery = QPushButton("Save Delivery Info")
        self.btn_save_delivery.setToolTip("Save delivery date and tracking number to order")
        self.btn_save_delivery.setMinimumHeight(32)  # Ensure button is fully visible
        self.btn_save_delivery.clicked.connect(self._on_save_delivery_info)
        self.btn_save_delivery.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold; border-radius: 4px; padding: 6px 12px;")
        bottom.addWidget(self.btn_save_delivery)

        self.btn_mark_billed = QPushButton("Mark as Billed")
        self.btn_mark_billed.setProperty("class", "primary")
        self.btn_mark_billed.setMinimumHeight(32)  # Ensure button is fully visible
        self.btn_mark_billed.clicked.connect(self._on_mark_billed)
        self.btn_mark_billed.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border-radius: 4px; padding: 6px 12px;")
        bottom.addWidget(self.btn_mark_billed)

        bottom.addItem(
            QSpacerItem(
                20,
                20,
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Minimum,
            )
        )

        btn_close = QPushButton("Close")
        btn_close.setMinimumHeight(32)  # Ensure button is fully visible
        btn_close.clicked.connect(self._save_pa_and_close)
        btn_close.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px; padding: 6px 12px;")
        bottom.addWidget(btn_close)

        layout.addLayout(bottom)

    def _make_copy_button(self, tooltip: str, slot) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("copyTool")
        btn.setText("Copy")
        btn.setToolTip(tooltip)
        btn.setAutoRaise(True)
        btn.setMinimumHeight(28)  # Ensure button is fully visible
        btn.setMinimumWidth(60)  # Ensure button text fits
        btn.clicked.connect(slot)
        return btn

    # ------------------------------------------------------------------ Data binding

    def _bind_data(self) -> None:
        o = self.order

        # Patient name - use patient_full_name property which has proper fallback
        patient_name = o.patient_full_name or ""
        self.lbl_patient_name.setText(patient_name)
        
        # Prescriber - try snapshot first, fall back to legacy fields
        prescriber_name = (
            o.prescriber_name_at_order_time
            or getattr(o, "prescriber_name", None)
            or ""
        )
        self.lbl_prescriber.setText(prescriber_name)
        
        prescriber_npi = (
            o.prescriber_npi_at_order_time
            or getattr(o, "prescriber_npi", None)
            or ""
        )
        self.lbl_npi.setText(prescriber_npi)

        # --- Fetch patient record FIRST for insurance/address fallback ---
        patient_record = None
        
        # DEBUG
        print(f"EPACES: order.patient_id = {getattr(o, 'patient_id', None)}")
        print(f"EPACES: order.patient_last_name = {getattr(o, 'patient_last_name', None)}")
        print(f"EPACES: order.patient_first_name = {getattr(o, 'patient_first_name', None)}")
        
        # Try to get patient record by patient_id first
        if getattr(o, "patient_id", None):
            try:
                patient_record = fetch_patient_by_id(o.patient_id, folder_path=self.folder_path)
                print(f"EPACES: fetch_patient_by_id returned: {patient_record}")
            except Exception as e:
                print(f"EPACES: fetch_patient_by_id failed: {e}")
                pass
        
        # If no patient_id or lookup failed, try by name using case-insensitive lookup
        if not patient_record and o.patient_last_name and o.patient_first_name:
            print(f"EPACES: Trying name lookup for last='{o.patient_last_name}', first='{o.patient_first_name}'")
            try:
                from dmelogic.db.patients import find_patient_by_name_and_dob
                dob_str = None
                if getattr(o, 'patient_dob', None):
                    dob_str = o.patient_dob.strftime("%Y-%m-%d")
                print(f"EPACES: DOB string = '{dob_str}'")
                patient_record = find_patient_by_name_and_dob(
                    o.patient_last_name,
                    o.patient_first_name,
                    dob=dob_str,
                    folder_path=self.folder_path
                )
                if patient_record:
                    print(f"EPACES: FOUND patient! address='{patient_record['address']}'")
                else:
                    print(f"EPACES: Patient NOT FOUND by name lookup")
            except Exception as e:
                import traceback
                print(f"EPACES: name lookup failed: {e}")
                traceback.print_exc()
                pass

        # Primary / secondary insurance - try order first, then patient record
        primary_name = (
            getattr(o, "insurance_name_at_order_time", None)
            or getattr(o, "primary_insurance", None)
            or getattr(o, "primary_insurance_name", "")
            or ""
        )
        primary_id = (
            getattr(o, "insurance_id_at_order_time", None)
            or getattr(o, "primary_insurance_id", None)
            or ""
        )
        secondary_name = (
            getattr(o, "secondary_insurance_name_at_order_time", None)
            or getattr(o, "secondary_insurance", None)
            or getattr(o, "secondary_insurance_name", "")
            or ""
        )
        secondary_id = (
            getattr(o, "secondary_insurance_id_at_order_time", None)
            or getattr(o, "secondary_insurance_id", None)
            or ""
        )
        
        # Fallback to patient record for insurance if order lacks it
        if patient_record:
            try:
                def get_field(row, field_name):
                    """Safely get a field from a sqlite Row."""
                    if hasattr(row, "keys") and field_name in row.keys():
                        return row[field_name] or ""
                    return ""
                
                # Patients table uses: primary_insurance, policy_number, secondary_insurance, secondary_insurance_id
                if not primary_name:
                    primary_name = get_field(patient_record, "primary_insurance")
                if not primary_id:
                    primary_id = get_field(patient_record, "policy_number")
                if not secondary_name:
                    secondary_name = get_field(patient_record, "secondary_insurance")
                if not secondary_id:
                    secondary_id = get_field(patient_record, "secondary_insurance_id")
                print(f"EPACES: Insurance after patient fallback - pri: {primary_name}/{primary_id}, sec: {secondary_name}/{secondary_id}")
            except Exception as e:
                print(f"EPACES: Failed to get insurance from patient: {e}")

        self._primary_ins_id = primary_id or ""
        self._secondary_ins_id = secondary_id or ""

        # Normalize insurance name: "EPACES..." -> "MEDICAID"
        if primary_name and "EPACES" in primary_name.upper():
            primary_name = "MEDICAID"
        
        prim_line = "None"
        if primary_name:
            prim_line = primary_name
            if primary_id:
                prim_line += f" (ID: {primary_id})"
        self.lbl_primary_ins.setText(prim_line)
        self.lbl_primary_member.setText(primary_id or "")

        # Normalize insurance name: "EPACES..." -> "MEDICAID"
        if secondary_name and "EPACES" in secondary_name.upper():
            secondary_name = "MEDICAID"
        
        sec_line = "None"
        if secondary_name:
            sec_line = secondary_name
            if secondary_id:
                sec_line += f" (ID: {secondary_id})"
        self.lbl_secondary_ins.setText(sec_line)

        # --- Delivery Date and Tracking Number -----------------------
        from PyQt6.QtCore import QDate
        
        if hasattr(o, "delivery_date") and o.delivery_date:
            if isinstance(o.delivery_date, str):
                parsed = None
                # Try ISO first (YYYY-MM-DD), then fallback to MM/DD/YYYY
                try:
                    y, m, d = o.delivery_date.split("-")
                    parsed = QDate(int(y), int(m), int(d))
                except Exception:
                    try:
                        parts = o.delivery_date.split("/")
                        if len(parts) == 3:
                            month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                            parsed = QDate(year, month, day)
                    except Exception:
                        parsed = None
                if parsed and parsed.isValid():
                    self.delivery_date_edit.setDate(parsed)
                else:
                    self.delivery_date_edit.setDate(QDate(2000, 1, 1))  # Blank
            else:
                # date object
                self.delivery_date_edit.setDate(QDate(o.delivery_date.year, o.delivery_date.month, o.delivery_date.day))
        else:
            # No delivery date - leave blank
            self.delivery_date_edit.setDate(QDate(2000, 1, 1))

        tracking_num = getattr(o, "tracking_number", None) or ""
        self.tracking_number_edit.setText(tracking_num)
        
        # Resolve patient address (patients.db first, then order snapshot)
        patient_db_path = resolve_db_path("patients.db", folder_path=self.folder_path)
        resolved_address = get_patient_full_address(
            patient_db_path,
            getattr(o, "patient_id", None),
            getattr(o, "patient_last_name", None),
            getattr(o, "patient_first_name", None),
        )

        def _build_snapshot_address() -> str:
            street = (
                getattr(o, "patient_address_at_order_time", None)
                or getattr(o, "patient_address", None)
                or ""
            ).strip()
            city = (
                getattr(o, "patient_city_at_order_time", None)
                or getattr(o, "patient_city", None)
                or ""
            ).strip()
            state = (
                getattr(o, "patient_state_at_order_time", None)
                or getattr(o, "patient_state", None)
                or ""
            ).strip()
            zip_code = (
                getattr(o, "patient_zip_at_order_time", None)
                or getattr(o, "patient_zip", None)
                or ""
            ).strip()

            if not any([street, city, state, zip_code]):
                return ""

            city_state = ", ".join([p for p in [city, state] if p])
            tail = (f"{city_state} {zip_code}".strip()).strip()
            parts = [p for p in [street, tail] if p]
            return ", ".join([p for p in parts if p])

        snapshot_address = _build_snapshot_address()
        address_line = resolved_address or snapshot_address or "N/A"
        print(f"EPACES: Final address_line = {address_line}")
        self.lbl_address_line.setText(address_line)

        # ICD-10s
        if getattr(o, "icd_codes", None):
            for code in o.icd_codes:
                if not code:
                    continue
                row = QHBoxLayout()
                row.setSpacing(4)

                # Remove period from ICD-10 code for EPACES display only
                display_code = code.replace(".", "")
                
                lbl = QLabel(display_code)
                lbl.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                row.addWidget(lbl)

                btn = self._make_copy_button(
                    f"Copy ICD-10 {display_code}", _make_value_copier(display_code)
                )
                row.addWidget(btn)

                row.addStretch()
                container = QWidget()
                container.setLayout(row)
                self.icd_codes_layout.addWidget(container)
        else:
            self.icd_codes_layout.addWidget(QLabel("(no ICD-10 codes on order)"))

        self._populate_items_table(list(o.items or []))

    # ---------- Item rows (buttons above values) ------------------------

    def _make_value_cell(self, display: str, tooltip: str, copy_value: str) -> QWidget:
        """
        Create a horizontal layout widget:

            [ display ]  [Copy]

        Used for ITEM, HCPCS, QTY, AMOUNT, MODS.
        """
        w = QWidget()
        w.setMinimumHeight(36)  # Ensure cell height accommodates button
        h = QHBoxLayout(w)
        h.setContentsMargins(6, 4, 6, 4)  # Increased horizontal padding
        h.setSpacing(8)  # Increased spacing between label and button

        lbl = QLabel(display)
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Vertical centering
        h.addWidget(lbl, 1)

        btn = self._make_copy_button(tooltip, _make_value_copier(copy_value))
        h.addWidget(btn)
        h.addStretch(0)  # Allow expansion to right

        return w

    def _make_pa_cell(self, item_id: int, initial_value: str = "") -> QWidget:
        """
        Horizontal layout for PA column:

            [ QLineEdit (PA #) ]  [Copy]
        
        Args:
            item_id: Order item ID (for saving)
            initial_value: Pre-fill the PA # if already saved
        """
        w = QWidget()
        w.setMinimumHeight(36)  # Ensure cell height accommodates widgets
        h = QHBoxLayout(w)
        h.setContentsMargins(6, 4, 6, 4)  # Increased horizontal padding
        h.setSpacing(8)  # Increased spacing between input and button

        edit = QLineEdit()
        edit.setPlaceholderText("PA # (12 max)")
        edit.setMaxLength(12)
        edit.setMinimumHeight(28)  # Ensure input field is fully visible
        edit.setMinimumWidth(140)  # Ensure 12 characters fit comfortably
        edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        edit.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Pre-fill with saved PA# if available
        if initial_value:
            edit.setText(initial_value)
        
        # Store reference for saving later
        self._pa_edits[item_id] = edit
        
        h.addWidget(edit, 1)

        def copy_pa(_checked: bool = False) -> None:
            _copy(edit.text().strip())

        btn = self._make_copy_button("Copy PA #", copy_pa)
        h.addWidget(btn)
        h.addStretch(0)  # Allow expansion to right

        return w

    def _populate_items_table(self, items: list[OrderItem]) -> None:
        self.items_table.setRowCount(0)
        claim_total = Decimal("0.00")

        for item in items:
            full_hcpcs = (item.hcpcs_code or "").strip()
            # Actual HCPCS (pre-hyphen) and item code (post-hyphen)
            post_hyphen = ""
            if "-" in full_hcpcs:
                pre, post = full_hcpcs.split("-", 1)
                actual_hcpcs = pre.strip()
                post_hyphen = post.strip()
            else:
                actual_hcpcs = full_hcpcs
            
            # Use inventory item number for ITEM column (e.g., MSC281226C)
            # First try from order item, then lookup from inventory by HCPCS
            item_number = (getattr(item, "item_number", None) or "").strip()
            if not item_number:
                # Lookup item_number from inventory database by HCPCS code
                try:
                    from dmelogic.db.inventory import fetch_latest_item_by_hcpcs
                    inv_data = fetch_latest_item_by_hcpcs(actual_hcpcs, folder_path=self.folder_path)
                    if inv_data and inv_data.get("item_number"):
                        item_number = inv_data["item_number"]
                except Exception:
                    pass
            # Final fallback to post-hyphen if still empty
            if not item_number and post_hyphen:
                item_number = post_hyphen

            qty = str(item.quantity or 0)

            # Amount: prefer total_cost; else cost_ea * qty
            line_total = Decimal("0.00")
            if item.total_cost is not None:
                line_total = item.total_cost
            elif item.cost_ea is not None:
                try:
                    line_total = (item.cost_ea or Decimal("0.00")) * Decimal(
                        str(item.quantity)
                    )
                except Exception:
                    line_total = Decimal("0.00")

            amount_val = f"{line_total:.2f}" if line_total != Decimal("0.00") else ""

            claim_total += line_total

            # MD Directions from item
            directions = getattr(item, "directions", None) or ""

            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setRowHeight(row, 42)  # Increased to accommodate widgets fully

            # ITEM cell (inventory item number, e.g., MSC281226C)
            item_cell = self._make_value_cell(
                display=item_number,
                tooltip="Copy inventory item number",
                copy_value=item_number,
            )
            self.items_table.setCellWidget(row, 0, item_cell)

            # HCPCS cell (Actual HCPCS, tooltip full string)
            hcpcs_cell = self._make_value_cell(
                display=actual_hcpcs,
                tooltip="Copy HCPCS (pre-hyphen)",
                copy_value=actual_hcpcs,
            )
            hcpcs_cell.setToolTip(full_hcpcs or "")
            self.items_table.setCellWidget(row, 1, hcpcs_cell)

            # QTY cell
            qty_cell = self._make_value_cell(
                display=qty,
                tooltip="Copy QTY",
                copy_value=qty,
            )
            self.items_table.setCellWidget(row, 2, qty_cell)

            # AMOUNT cell
            amt_cell = self._make_value_cell(
                display=amount_val,
                tooltip="Copy AMOUNT",
                copy_value=amount_val,
            )
            self.items_table.setCellWidget(row, 3, amt_cell)

            # MD DIRECTIONS cell
            directions_cell = self._make_value_cell(
                display=directions,
                tooltip="Copy MD directions",
                copy_value=directions,
            )
            self.items_table.setCellWidget(row, 4, directions_cell)

            # PA # cell (line edit + Copy button horizontally)
            # Load saved PA# from order item
            saved_pa = getattr(item, "pa_number", None) or ""
            pa_cell = self._make_pa_cell(item.id, saved_pa)
            self.items_table.setCellWidget(row, 5, pa_cell)

        # Update claim total label + raw copy value
        self._claim_total_raw = f"{claim_total:.2f}"
        self.lbl_claim_total.setText(f"Claim Total: {self._claim_total_raw}")

    # ------------------------------------------------------------------ Delivery info row

    def _build_delivery_info_row(self) -> QHBoxLayout:
        """Build delivery date and tracking number row (called from _build_ui)."""
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate
        
        row_delivery = QHBoxLayout()
        row_delivery.setSpacing(10)  # Increased spacing

        # Delivery Date with calendar picker
        self.delivery_date_edit = QDateEdit()
        self.delivery_date_edit.setCalendarPopup(True)
        self.delivery_date_edit.setDisplayFormat("MM/dd/yyyy")
        self.delivery_date_edit.setMinimumDate(QDate(2000, 1, 1))
        self.delivery_date_edit.setSpecialValueText(" ")  # Allow clearing the date (displays as blank)
        self.delivery_date_edit.setDate(QDate(2000, 1, 1))  # Start blank
        self.delivery_date_edit.setMinimumHeight(28)  # Ensure fully visible
        self.delivery_date_edit.setMinimumWidth(120)  # Ensure date fits
        row_delivery.addWidget(QLabel("Delivery Date:"))
        row_delivery.addWidget(self.delivery_date_edit, 2)

        btn_delivery_copy = self._make_copy_button(
            "Copy delivery date",
            lambda: _copy(self.delivery_date_edit.date().toString("MM/dd/yyyy")),
        )
        row_delivery.addWidget(btn_delivery_copy)

        # Shipper's Order Number (editable)
        self.tracking_number_edit = QLineEdit()
        self.tracking_number_edit.setPlaceholderText("Enter shipper's order number")
        self.tracking_number_edit.setMinimumHeight(28)  # Ensure fully visible
        self.tracking_number_edit.setMinimumWidth(180)  # Ensure text fits
        self.tracking_number_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_delivery.addSpacing(24)
        row_delivery.addWidget(QLabel("Shipper's Order #:"))
        row_delivery.addWidget(self.tracking_number_edit, 2)

        btn_tracking_copy = self._make_copy_button(
            "Copy shipper's order number",
            lambda: _copy(self.tracking_number_edit.text()),
        )
        row_delivery.addWidget(btn_tracking_copy)

        return row_delivery

    # ------------------------------------------------------------------ Status action

    def _on_save_delivery_info(self) -> None:
        """Save delivery date and tracking number to order without changing status."""
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import QDate

        try:
            # Check if date is blank (minimum date means blank)
            date_val = self.delivery_date_edit.date()
            if date_val.isValid() and date_val.year() > 1900:
                delivery_date = date_val.toString("MM/dd/yyyy")
            else:
                delivery_date = None  # Store as NULL in database
            tracking_number = self.tracking_number_edit.text().strip()
            
            orders_db = resolve_db_path("orders.db", folder_path=self.folder_path)
            conn = sqlite3.connect(orders_db)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET delivery_date = ?, tracking_number = ? WHERE id = ?",
                (delivery_date, tracking_number, self.order.id)
            )
            conn.commit()
            conn.close()
            
            # Update order object
            self.order.delivery_date = delivery_date
            self.order.tracking_number = tracking_number
            
            QMessageBox.information(
                self,
                "Saved",
                "Delivery date and tracking number saved successfully.",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save delivery info: {e}",
            )

    def _on_mark_billed(self) -> None:
        """
        Mark this order as BILLED via the workflow engine.
        Also saves delivery date, tracking number, and PA numbers first.
        """
        from PyQt6.QtWidgets import QMessageBox

        # First, save delivery info and PA numbers
        self._on_save_delivery_info()
        self._save_pa_numbers()

        folder = self.folder_path

        current = self.order.order_status.value
        new_status = OrderStatus.BILLED.value

        success, error = update_order_status_validated(
            order_id=self.order.id,
            current_status=current,
            new_status=new_status,
            folder_path=folder,
        )

        if not success:
            QMessageBox.warning(
                self,
                "Mark as Billed",
                error or "Failed to mark order as BILLED.",
            )
            return

        self.order.order_status = OrderStatus.BILLED
        QMessageBox.information(
            self,
            "Mark as Billed",
            "Order has been marked as BILLED.",
        )

    def _save_pa_numbers(self) -> bool:
        """
        Save all PA numbers entered in the dialog to the order_items table.
        
        Returns:
            True if save was successful, False otherwise
        """
        if not self._pa_edits:
            return True
        
        try:
            orders_db = resolve_db_path("orders.db", folder_path=self.folder_path)
            conn = sqlite3.connect(orders_db)
            cursor = conn.cursor()
            
            saved_count = 0
            for item_id, edit in self._pa_edits.items():
                pa_value = edit.text().strip()
                cursor.execute(
                    "UPDATE order_items SET pa_number = ? WHERE id = ?",
                    (pa_value, item_id)
                )
                if pa_value:
                    saved_count += 1
            
            conn.commit()
            conn.close()
            
            if saved_count > 0:
                print(f"✅ Saved PA# for {saved_count} items")
            
            return True
        except Exception as e:
            print(f"❌ Failed to save PA numbers: {e}")
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save PA numbers: {e}",
            )
            return False

    def _save_pa_and_close(self) -> None:
        """Save PA numbers and close the dialog."""
        self._save_pa_numbers()
        self.accept()
