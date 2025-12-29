"""
Prescriber Lookup Dialog
Allows searching for prescribers in local database or CMS NPI Registry API
"""

import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QComboBox, QRadioButton, QButtonGroup, QWidget
)
from PyQt6.QtCore import Qt
from dmelogic.db.base import get_connection


class PrescriberLookupDialog(QDialog):
    """Dialog for searching prescribers in local database or NPI Registry."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_prescriber = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Prescriber Lookup")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Search source section
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Search In:"))
        
        self.source_group = QButtonGroup()
        self.local_radio = QRadioButton("Local Database")
        self.registry_radio = QRadioButton("NPI Registry")
        self.local_radio.setChecked(True)
        
        self.source_group.addButton(self.local_radio)
        self.source_group.addButton(self.registry_radio)
        
        source_layout.addWidget(self.local_radio)
        source_layout.addWidget(self.registry_radio)
        source_layout.addStretch()
        
        layout.addLayout(source_layout)
        
        # Search criteria section
        search_group = QVBoxLayout()
        
        # Search type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Search By:"))
        self.search_type = QComboBox()
        self.search_type.addItems(["Name", "NPI Number"])
        type_layout.addWidget(self.search_type)
        type_layout.addStretch()
        search_group.addLayout(type_layout)
        
        # Name search fields
        self.name_widget = QWidget()
        name_layout = QVBoxLayout(self.name_widget)
        name_layout.setContentsMargins(0, 0, 0, 0)
        
        first_layout = QHBoxLayout()
        first_layout.addWidget(QLabel("First Name:"))
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Enter first name (optional)")
        first_layout.addWidget(self.first_name_input)
        name_layout.addLayout(first_layout)
        
        last_layout = QHBoxLayout()
        last_layout.addWidget(QLabel("Last Name:"))
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Enter last name (optional)")
        last_layout.addWidget(self.last_name_input)
        name_layout.addLayout(last_layout)
        
        search_group.addWidget(self.name_widget)
        
        # NPI search field
        self.npi_widget = QWidget()
        npi_layout = QHBoxLayout(self.npi_widget)
        npi_layout.setContentsMargins(0, 0, 0, 0)
        npi_layout.addWidget(QLabel("NPI Number:"))
        self.npi_input = QLineEdit()
        self.npi_input.setPlaceholderText("Enter 10-digit NPI number")
        npi_layout.addWidget(self.npi_input)
        search_group.addWidget(self.npi_widget)
        self.npi_widget.hide()
        
        # Search type change handler
        self.search_type.currentTextChanged.connect(self.on_search_type_changed)
        
        layout.addLayout(search_group)
        
        # Search button
        search_btn_layout = QHBoxLayout()
        search_btn_layout.addStretch()
        self.search_btn = QPushButton("Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.search_btn.clicked.connect(self.perform_search)
        search_btn_layout.addWidget(self.search_btn)
        search_btn_layout.addStretch()
        layout.addLayout(search_btn_layout)
        
        # Results table
        layout.addWidget(QLabel("Search Results:"))
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels([
            "Last Name", "First Name", "NPI", "Credential", "City", "State"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.itemDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.results_table)
        
        # Status label
        self.status_label = QLabel("Enter search criteria and click 'Search'")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        select_btn = QPushButton("Select Prescriber")
        select_btn.setStyleSheet("background-color: #3498db; color: white; padding: 6px 16px;")
        select_btn.clicked.connect(self.on_select_clicked)
        btn_layout.addWidget(select_btn)
        
        layout.addLayout(btn_layout)
        
        # Enable Enter key to search
        self.first_name_input.returnPressed.connect(self.perform_search)
        self.last_name_input.returnPressed.connect(self.perform_search)
        self.npi_input.returnPressed.connect(self.perform_search)
        
    def on_search_type_changed(self, search_type):
        """Handle search type change."""
        if search_type == "Name":
            self.name_widget.show()
            self.npi_widget.hide()
        else:
            self.name_widget.hide()
            self.npi_widget.show()
    
    def perform_search(self):
        """Search based on current source and criteria."""
        search_type = self.search_type.currentText()
        
        if self.local_radio.isChecked():
            # Search local database
            if search_type == "Name":
                first_name = self.first_name_input.text().strip()
                last_name = self.last_name_input.text().strip()
                
                if not first_name and not last_name:
                    QMessageBox.warning(
                        self,
                        "Missing Information",
                        "Please enter at least a first name or last name."
                    )
                    return
                
                self.search_local_by_name(first_name, last_name)
            else:
                npi = self.npi_input.text().strip()
                
                if not npi:
                    QMessageBox.warning(
                        self,
                        "Missing Information",
                        "Please enter an NPI number."
                    )
                    return
                
                self.search_local_by_npi(npi)
        else:
            # Search NPI Registry
            if search_type == "Name":
                first_name = self.first_name_input.text().strip()
                last_name = self.last_name_input.text().strip()
                
                if not first_name and not last_name:
                    QMessageBox.warning(
                        self,
                        "Missing Information",
                        "Please enter at least a first name or last name."
                    )
                    return
                
                self.search_registry_by_name(first_name, last_name)
            else:
                npi = self.npi_input.text().strip()
                
                if not npi:
                    QMessageBox.warning(
                        self,
                        "Missing Information",
                        "Please enter an NPI number."
                    )
                    return
                
                if not npi.isdigit() or len(npi) != 10:
                    QMessageBox.warning(
                        self,
                        "Invalid NPI",
                        "NPI must be a 10-digit number."
                    )
                    return
                
                self.search_registry_by_npi(npi)
    
    def search_local_by_name(self, first_name, last_name):
        """Search local database by prescriber name."""
        self.status_label.setText("Searching local database...")
        self.search_btn.setEnabled(False)
        
        try:
            conn = get_connection("prescribers.db")
            cur = conn.cursor()
            
            # Build query with wildcards
            conditions = []
            params = []
            
            if first_name:
                conditions.append("first_name LIKE ?")
                params.append(f"%{first_name}%")
            if last_name:
                conditions.append("last_name LIKE ?")
                params.append(f"%{last_name}%")
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT id, first_name, last_name, npi_number, title, city, state, 
                       phone, fax, specialty, address_line1, zip_code, status
                FROM prescribers
                WHERE {where_clause}
                ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
                LIMIT 100
            """
            
            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                self.status_label.setText("No prescribers found in local database.")
                self.results_table.setRowCount(0)
            else:
                self.populate_local_results(rows)
                self.status_label.setText(f"Found {len(rows)} prescriber(s) in local database. Double-click to select.")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to search local database:\n{e}"
            )
            self.status_label.setText("Search failed.")
        finally:
            self.search_btn.setEnabled(True)
    
    def search_local_by_npi(self, npi):
        """Search local database by NPI number."""
        self.status_label.setText("Searching local database...")
        self.search_btn.setEnabled(False)
        
        try:
            conn = get_connection("prescribers.db")
            cur = conn.cursor()
            
            query = """
                SELECT id, first_name, last_name, npi_number, title, city, state,
                       phone, fax, specialty, address_line1, zip_code, status
                FROM prescribers
                WHERE npi_number LIKE ?
                LIMIT 100
            """
            
            cur.execute(query, (f"%{npi}%",))
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                self.status_label.setText(f"No prescriber found with NPI {npi} in local database.")
                self.results_table.setRowCount(0)
            else:
                self.populate_local_results(rows)
                self.status_label.setText(f"Found {len(rows)} prescriber(s) in local database. Double-click to select.")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to search local database:\n{e}"
            )
            self.status_label.setText("Search failed.")
        finally:
            self.search_btn.setEnabled(True)
    
    def populate_local_results(self, rows):
        """Populate the results table with local database data."""
        self.results_table.setRowCount(0)
        
        for row in rows:
            row_num = self.results_table.rowCount()
            self.results_table.insertRow(row_num)
            
            # Extract prescriber information
            prescriber_id = row[0]
            first_name = row[1] or ""
            last_name = row[2] or ""
            npi = row[3] or ""
            credential = row[4] or ""
            city = row[5] or ""
            state = row[6] or ""
            
            # Store full row data in first column for later retrieval
            item_last = QTableWidgetItem(last_name)
            item_last.setData(Qt.ItemDataRole.UserRole, {
                "source": "local",
                "id": prescriber_id,
                "first_name": first_name,
                "last_name": last_name,
                "npi_number": npi,
                "title": credential,
                "city": city,
                "state": state,
                "phone": row[7] or "",
                "fax": row[8] or "",
                "specialty": row[9] or "",
                "address": row[10] or "",
                "zip_code": row[11] or "",
                "status": row[12] or "Active"
            })
            self.results_table.setItem(row_num, 0, item_last)
            
            self.results_table.setItem(row_num, 1, QTableWidgetItem(first_name))
            self.results_table.setItem(row_num, 2, QTableWidgetItem(npi))
            self.results_table.setItem(row_num, 3, QTableWidgetItem(credential))
            self.results_table.setItem(row_num, 4, QTableWidgetItem(city))
            self.results_table.setItem(row_num, 5, QTableWidgetItem(state))
    
    def search_registry_by_name(self, first_name, last_name):
        """Search NPI Registry by prescriber name."""
        self.status_label.setText("Searching NPI Registry...")
        self.search_btn.setEnabled(False)
        
        try:
            # CMS NPI Registry API endpoint
            url = "https://npiregistry.cms.hhs.gov/api/"
            
            params = {
                "version": "2.1",
                "enumeration_type": "NPI-1",  # Individual providers
                "limit": 50
            }
            
            if first_name:
                params["first_name"] = first_name
            if last_name:
                params["last_name"] = last_name
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                self.status_label.setText("No prescribers found in NPI Registry.")
                self.results_table.setRowCount(0)
            else:
                self.populate_registry_results(results)
                self.status_label.setText(f"Found {len(results)} prescriber(s) in NPI Registry. Double-click to select.")
                
        except requests.exceptions.Timeout:
            QMessageBox.warning(
                self,
                "Timeout",
                "The NPI Registry search timed out. Please try again."
            )
            self.status_label.setText("Search timed out.")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(
                self,
                "Network Error",
                f"Failed to connect to NPI Registry:\n{e}"
            )
            self.status_label.setText("Search failed.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during search:\n{e}"
            )
            self.status_label.setText("Search error.")
        finally:
            self.search_btn.setEnabled(True)
    
    def search_registry_by_npi(self, npi):
        """Search NPI Registry by NPI number."""
        self.status_label.setText("Searching NPI Registry...")
        self.search_btn.setEnabled(False)
        
        try:
            url = "https://npiregistry.cms.hhs.gov/api/"
            
            params = {
                "version": "2.1",
                "number": npi
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                self.status_label.setText(f"No prescriber found with NPI {npi} in NPI Registry.")
                self.results_table.setRowCount(0)
            else:
                self.populate_registry_results(results)
                self.status_label.setText(f"Found prescriber in NPI Registry. Double-click to select.")
                
        except requests.exceptions.Timeout:
            QMessageBox.warning(
                self,
                "Timeout",
                "The NPI Registry search timed out. Please try again."
            )
            self.status_label.setText("Search timed out.")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(
                self,
                "Network Error",
                f"Failed to connect to NPI Registry:\n{e}"
            )
            self.status_label.setText("Search failed.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred during search:\n{e}"
            )
            self.status_label.setText("Search error.")
        finally:
            self.search_btn.setEnabled(True)
    
    def populate_registry_results(self, results):
        """Populate the results table with NPI Registry data."""
        self.results_table.setRowCount(0)
        
        for result in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            # Extract prescriber information
            basic = result.get("basic", {})
            npi = result.get("number", "")
            last_name = basic.get("last_name", "")
            first_name = basic.get("first_name", "")
            credential = basic.get("credential", "")
            
            # Get primary practice address
            addresses = result.get("addresses", [])
            city = ""
            state = ""
            for addr in addresses:
                if addr.get("address_purpose") == "LOCATION":
                    city = addr.get("city", "")
                    state = addr.get("state", "")
                    break
            
            # Store full result data in first column for later retrieval
            item_last = QTableWidgetItem(last_name)
            item_last.setData(Qt.ItemDataRole.UserRole, {
                "source": "registry",
                "result": result
            })
            self.results_table.setItem(row, 0, item_last)
            
            self.results_table.setItem(row, 1, QTableWidgetItem(first_name))
            self.results_table.setItem(row, 2, QTableWidgetItem(npi))
            self.results_table.setItem(row, 3, QTableWidgetItem(credential))
            self.results_table.setItem(row, 4, QTableWidgetItem(city))
            self.results_table.setItem(row, 5, QTableWidgetItem(state))
    
    def on_row_double_clicked(self, item):
        """Handle double-click on a result row."""
        self.on_select_clicked()
    
    def on_select_clicked(self):
        """Handle the Select button click."""
        current_row = self.results_table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a prescriber from the results."
            )
            return
        
        # Get the full prescriber data from the first column
        item = self.results_table.item(current_row, 0)
        data = item.data(Qt.ItemDataRole.UserRole)
        
        # Extract and format prescriber data based on source
        if data.get("source") == "local":
            self.selected_prescriber = self.extract_local_prescriber_data(data)
        else:
            self.selected_prescriber = self.extract_registry_prescriber_data(data["result"])
        
        self.accept()
    
    def extract_local_prescriber_data(self, data):
        """Extract prescriber data from local database result."""
        return {
            "prescriber_id": data["id"],
            "npi_number": data["npi_number"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "credential": data["title"],
            "title": data["title"],
            "specialty": data.get("specialty", ""),
            "address_line1": data.get("address", ""),
            "address_line2": "",
            "city": data.get("city", ""),
            "state": data.get("state", ""),
            "zip_code": data.get("zip_code", ""),
            "phone": data.get("phone", ""),
            "fax": data.get("fax", ""),
            "dea_number": "",
            "license_number": ""
        }
    
    def extract_registry_prescriber_data(self, result):
        """Extract prescriber data from NPI Registry result."""
        basic = result.get("basic", {})
        
        data = {
            "prescriber_id": None,  # New prescriber from registry
            "npi_number": result.get("number", ""),
            "first_name": basic.get("first_name", ""),
            "last_name": basic.get("last_name", ""),
            "credential": basic.get("credential", ""),
            "title": basic.get("credential", ""),  # Use credential as title
        }
        
        # Get taxonomies for specialty
        taxonomies = result.get("taxonomies", [])
        if taxonomies:
            primary = next((t for t in taxonomies if t.get("primary")), taxonomies[0])
            data["specialty"] = primary.get("desc", "")
        else:
            data["specialty"] = ""
        
        # Get primary practice location address
        addresses = result.get("addresses", [])
        for addr in addresses:
            if addr.get("address_purpose") == "LOCATION":
                data["address_line1"] = addr.get("address_1", "")
                data["address_line2"] = addr.get("address_2", "")
                data["city"] = addr.get("city", "")
                data["state"] = addr.get("state", "")
                data["zip_code"] = addr.get("postal_code", "")
                data["phone"] = addr.get("telephone_number", "")
                data["fax"] = addr.get("fax_number", "")
                break
        
        # Default empty values if no address found
        if "address_line1" not in data:
            data["address_line1"] = ""
            data["address_line2"] = ""
            data["city"] = ""
            data["state"] = ""
            data["zip_code"] = ""
            data["phone"] = ""
            data["fax"] = ""
        
        # Get DEA if available (not typically in NPI Registry)
        # User will need to enter this manually
        data["dea_number"] = ""
        
        # Get license number if available
        data["license_number"] = ""
        identifiers = result.get("identifiers", [])
        for identifier in identifiers:
            if identifier.get("code") == "01":  # State license number
                data["license_number"] = identifier.get("identifier", "")
                break
        
        return data
    
    def get_selected_prescriber(self):
        """Return the selected prescriber data."""
        return self.selected_prescriber


from PyQt6.QtWidgets import QWidget


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = PrescriberLookupDialog()
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        prescriber = dialog.get_selected_prescriber()
        print("Selected Prescriber:")
        for key, value in prescriber.items():
            print(f"  {key}: {value}")
    
    sys.exit(0)
