"""
First Run Setup Wizard - Guides users through initial configuration.
Prompts for server folder locations on first launch.
"""

import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox,
    QCheckBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap


def get_settings_path() -> Path:
    """Get the path to settings.json in a user-writable location."""
    # Use %LOCALAPPDATA%\DMELogic for settings (user-writable, not Program Files)
    if os.name == 'nt':  # Windows
        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        settings_dir = Path(local_appdata) / "DMELogic"
    else:
        settings_dir = Path.home() / ".dmelogic"
    
    # Create directory if it doesn't exist
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "settings.json"


def is_first_run() -> bool:
    """Check if this is the first run (no settings.json, setup not completed, or missing required paths)."""
    settings_path = get_settings_path()
    if not settings_path.exists():
        return True
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # Require explicit completion flag so new installs always see the wizard once.
        if not settings.get('setup_completed', False):
            return True

        # Check if required paths are configured
        db_folder = settings.get('db_folder', '')
        if not db_folder or not Path(db_folder).exists():
            return True

        fax_folder = settings.get('fax_folder', '') or settings.get('last_folder', '')
        if not fax_folder or not Path(fax_folder).exists():
            return True

        # Backups are strongly recommended; if configured, ensure the path exists.
        backup_folder = settings.get('backup_folder', '')
        if backup_folder and (not Path(backup_folder).exists()):
            return True

        return False
    except Exception:
        return True


def load_existing_settings() -> dict:
    """Load existing settings if available."""
    settings_path = get_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


class WelcomePage(QWizardPage):
    """Welcome page introducing the setup wizard."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to DMELogic Setup")
        self.setSubTitle("This wizard will help you configure DMELogic for first use.")
        
        layout = QVBoxLayout(self)
        
        # Welcome message
        welcome_label = QLabel(
            "<h3>Welcome!</h3>"
            "<p>Before you can use DMELogic, we need to connect this workstation to your server.</p>"
            "<p>You will need the <b>network paths</b> to the following folders on the <b>server PC</b>:</p>"
            "<ul>"
            "<li><b>Database Folder</b> — Patient &amp; order databases<br>"
            "<code style='color:#0d9488;'>Example: \\\\SERVER-PC\\DMELogic\\Data</code></li>"
            "<li><b>Fax Documents Folder</b> — Scanned/faxed PDFs<br>"
            "<code style='color:#0d9488;'>Example: \\\\SERVER-PC\\FaxManagerData</code></li>"
            "<li><b>Backup Folder</b> — Automatic backups (server only, optional here)</li>"
            "</ul>"
            "<p style='color:#d97706;'><b>Important:</b> All workstations must point to the <b>same shared folders</b> "
            "on the server so everyone works from the same data.</p>"
            "<p>Click <b>Next</b> to continue.</p>"
        )
        welcome_label.setWordWrap(True)
        welcome_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(welcome_label)
        layout.addStretch()


class DatabaseFolderPage(QWizardPage):
    """Page for configuring the database folder location."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Database Location")
        self.setSubTitle("Select the folder where patient and order databases are stored.")
        
        layout = QVBoxLayout(self)
        
        # Instructions
        info_label = QLabel(
            "<p>The database folder contains the SQLite databases for patients, orders, and inventory.</p>"
            "<p><b>Network workstation:</b> Browse to the shared folder on your server:<br>"
            "<code style='color:#0d9488;'>\\\\SERVER-PC\\DMELogic\\Data</code></p>"
            "<p><b>Server PC (standalone):</b> Use the local path:<br>"
            "<code style='color:#0d9488;'>C:\\ProgramData\\DMELogic\\Data</code></p>"
            "<p style='color:#d97706;'>⚠ All workstations must point to the <b>same folder</b> on the server.</p>"
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        
        # Folder selection group
        group = QGroupBox("Database Folder")
        group_layout = QHBoxLayout(group)
        
        self.db_folder_edit = QLineEdit()
        self.db_folder_edit.setPlaceholderText("Select or enter the database folder path...")
        # Explicitly specify property + change signal so the Next button updates reliably.
        self.registerField("db_folder*", self.db_folder_edit, "text", self.db_folder_edit.textChanged)
        group_layout.addWidget(self.db_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_db_folder)
        group_layout.addWidget(browse_btn)
        
        layout.addWidget(group)
        
        # Create folder option
        self.create_checkbox = QCheckBox("Create folder if it doesn't exist")
        self.create_checkbox.setChecked(True)
        layout.addWidget(self.create_checkbox)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Connect for validation
        self.db_folder_edit.textChanged.connect(self.validate_folder)
    
    def initializePage(self):
        """Auto-detect existing database folder on page load."""
        # Check common locations for existing databases
        common_paths = [
            r"C:\Dme_Solutions\Data",
            r"C:\DME_Solutions\Data",
            r"C:\DMELogic\Data",
            r"C:\ProgramData\DMELogic\Data",
        ]
        
        for path in common_paths:
            if os.path.isdir(path):
                # Check if it contains database files
                db_files = [f for f in os.listdir(path) if f.endswith('.db')]
                if db_files:
                    self.db_folder_edit.setText(path)
                    self.status_label.setText(f"✓ Auto-detected! Found {len(db_files)} database(s)")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    return
        
        # If no existing databases found, suggest default
        if os.path.isdir(r"C:\Dme_Solutions\Data"):
            self.db_folder_edit.setText(r"C:\Dme_Solutions\Data")
    
    def browse_db_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Database Folder",
            self.db_folder_edit.text() or "C:\\"
        )
        if folder:
            self.db_folder_edit.setText(folder)
    
    def validate_folder(self):
        path = self.db_folder_edit.text()
        if not path:
            self.status_label.setText("")
            return
        
        p = Path(path)
        if p.exists():
            # Check for existing databases
            dbs = list(p.glob("*.db"))
            if dbs:
                self.status_label.setText(f"✓ Found {len(dbs)} database(s) in this folder")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("✓ Folder exists (no databases yet - they will be created)")
                self.status_label.setStyleSheet("color: #0066cc;")
        else:
            if self.create_checkbox.isChecked():
                self.status_label.setText("⚠ Folder will be created")
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.status_label.setText("✗ Folder does not exist")
                self.status_label.setStyleSheet("color: red;")
    
    def validatePage(self):
        path = self.db_folder_edit.text()
        if not path:
            QMessageBox.warning(self, "Required", "Please select a database folder.")
            return False
        
        p = Path(path)
        if not p.exists():
            if self.create_checkbox.isChecked():
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create folder:\n{e}")
                    return False
            else:
                QMessageBox.warning(self, "Invalid Path", "The folder does not exist.")
                return False
        
        return True


class FaxFolderPage(QWizardPage):
    """Page for configuring the fax/documents folder location."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Fax Documents Location")
        self.setSubTitle("Select the folder where OCR'd fax documents are stored.")
        
        layout = QVBoxLayout(self)
        
        # Instructions
        info_label = QLabel(
            "<p>This folder contains the scanned/faxed documents (PDFs) organized by date.</p>"
            "<p>DMELogic will browse these documents to link them to patient orders.</p>"
            "<p><b>Network workstation:</b> Browse to the shared fax folder on your server:<br>"
            "<code style='color:#0d9488;'>\\\\SERVER-PC\\FaxManagerData</code></p>"
            "<p><b>Server PC (standalone):</b> Use the local path:<br>"
            "<code style='color:#0d9488;'>C:\\FaxManagerData</code></p>"
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        
        # Folder selection group
        group = QGroupBox("Fax Documents Folder")
        group_layout = QHBoxLayout(group)
        
        self.fax_folder_edit = QLineEdit()
        self.fax_folder_edit.setPlaceholderText("Select or enter the fax documents folder path...")
        # Explicitly specify property + change signal so the Next button updates reliably.
        self.registerField("fax_folder*", self.fax_folder_edit, "text", self.fax_folder_edit.textChanged)
        group_layout.addWidget(self.fax_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_fax_folder)
        group_layout.addWidget(browse_btn)
        
        layout.addWidget(group)
        
        # Create folder option
        self.create_checkbox = QCheckBox("Create folder if it doesn't exist")
        self.create_checkbox.setChecked(True)
        layout.addWidget(self.create_checkbox)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.fax_folder_edit.textChanged.connect(self.validate_folder)
    
    def browse_fax_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Fax Documents Folder",
            self.fax_folder_edit.text() or "C:\\"
        )
        if folder:
            self.fax_folder_edit.setText(folder)
    
    def validate_folder(self):
        path = self.fax_folder_edit.text()
        if not path:
            self.status_label.setText("")
            return
        
        p = Path(path)
        if p.exists():
            # Check for PDFs
            pdf_count = len(list(p.rglob("*.pdf")))
            if pdf_count > 0:
                self.status_label.setText(f"✓ Found {pdf_count} PDF(s) in this folder")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("✓ Folder exists (no PDFs found yet)")
                self.status_label.setStyleSheet("color: #0066cc;")
        else:
            if self.create_checkbox.isChecked():
                self.status_label.setText("⚠ Folder will be created")
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.status_label.setText("✗ Folder does not exist")
                self.status_label.setStyleSheet("color: red;")
    
    def validatePage(self):
        path = self.fax_folder_edit.text()
        if not path:
            QMessageBox.warning(self, "Required", "Please select a fax documents folder.")
            return False
        
        p = Path(path)
        if not p.exists():
            if self.create_checkbox.isChecked():
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create folder:\n{e}")
                    return False
            else:
                QMessageBox.warning(self, "Invalid Path", "The folder does not exist.")
                return False
        
        return True


class BackupFolderPage(QWizardPage):
    """Page for configuring the backup folder location."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Backup Location")
        self.setSubTitle("Select where automatic database backups will be saved.")
        
        layout = QVBoxLayout(self)
        
        # Instructions
        info_label = QLabel(
            "<p>DMELogic automatically backs up your databases. Select a safe location for these backups.</p>"
            "<p><b>Recommendation:</b> Use a different drive or network location for safety.</p>"
            "<p style='color:#0066cc;'><b>Note:</b> Backups typically only run on the <b>server PC</b>. "
            "Workstations can leave this blank.</p>"
        )
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        
        # Folder selection group
        group = QGroupBox("Backup Folder")
        group_layout = QHBoxLayout(group)
        
        self.backup_folder_edit = QLineEdit()
        self.backup_folder_edit.setPlaceholderText("Select or enter the backup folder path...")
        self.registerField("backup_folder", self.backup_folder_edit)
        group_layout.addWidget(self.backup_folder_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_backup_folder)
        group_layout.addWidget(browse_btn)
        
        layout.addWidget(group)
        
        # Create folder option
        self.create_checkbox = QCheckBox("Create folder if it doesn't exist")
        self.create_checkbox.setChecked(True)
        layout.addWidget(self.create_checkbox)
        
        layout.addStretch()
    
    def browse_backup_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Backup Folder",
            self.backup_folder_edit.text() or "C:\\"
        )
        if folder:
            self.backup_folder_edit.setText(folder)
    
    def validatePage(self):
        path = self.backup_folder_edit.text()
        if path:
            p = Path(path)
            if not p.exists() and self.create_checkbox.isChecked():
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create folder:\n{e}")
                    return False
        return True


class SummaryPage(QWizardPage):
    """Summary page showing configured settings."""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete")
        self.setSubTitle("Review your configuration and click Finish to start DMELogic.")
        
        layout = QVBoxLayout(self)
        
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.summary_label)
        
        layout.addStretch()
    
    def initializePage(self):
        db_folder = self.field("db_folder")
        fax_folder = self.field("fax_folder")
        backup_folder = self.field("backup_folder") or "(Not configured)"
        
        self.summary_label.setText(
            f"<h3>Configuration Summary</h3>"
            f"<p><b>Database Folder:</b><br><code>{db_folder}</code></p>"
            f"<p><b>Fax Documents Folder:</b><br><code>{fax_folder}</code></p>"
            f"<p><b>Backup Folder:</b><br><code>{backup_folder}</code></p>"
            f"<hr>"
            f"<p>Click <b>Finish</b> to save these settings and start DMELogic.</p>"
        )


class FirstRunWizard(QWizard):
    """Main setup wizard for first-time configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DMELogic - First Time Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 450)
        
        # Load any existing settings
        existing = load_existing_settings()
        
        # Add pages
        self.addPage(WelcomePage())
        
        self.db_page = DatabaseFolderPage()
        if existing.get('db_folder'):
            self.db_page.db_folder_edit.setText(existing['db_folder'])
        self.addPage(self.db_page)
        
        self.fax_page = FaxFolderPage()
        if existing.get('last_folder'):
            self.fax_page.fax_folder_edit.setText(existing['last_folder'])
        self.addPage(self.fax_page)
        
        self.backup_page = BackupFolderPage()
        if existing.get('backup_folder'):
            self.backup_page.backup_folder_edit.setText(existing['backup_folder'])
        self.addPage(self.backup_page)
        
        self.addPage(SummaryPage())
        
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish && Start DMELogic")
    
    def accept(self):
        """Save settings when wizard completes."""
        settings = load_existing_settings()
        
        # Update with new values
        settings['db_folder'] = self.field("db_folder")
        settings['fax_folder'] = self.field("fax_folder")  # Save as fax_folder for paths.py
        settings['last_folder'] = self.field("fax_folder")  # Also keep last_folder for compatibility
        
        backup_folder = self.field("backup_folder")
        if backup_folder:
            settings['backup_folder'] = backup_folder
        
        # Ensure required keys exist
        if 'quick_folders' not in settings:
            settings['quick_folders'] = []
        if 'patient_button_order' not in settings:
            settings['patient_button_order'] = [
                "edit_patient", "new_order", "new_patient",
                "view_orders", "view_docs", "delete_patient"
            ]
        if 'order_button_order' not in settings:
            settings['order_button_order'] = [
                "new_order", "epaces", "edit_order", "update_status",
                "delivery_report", "clear_delivery", "process_refill",
                "reverse_refill", "export_portal", "generate_1500",
                "print_1500", "delete_order", "link_patient"
            ]
        
        # Set default theme to Light for consistent appearance
        if 'theme' not in settings:
            settings['theme'] = 'Light'

        # Mark setup as completed so we don't prompt every launch.
        settings['setup_completed'] = True
        
        # Save settings
        settings_path = get_settings_path()
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save settings:\n{e}")
            return
        
        super().accept()


def run_first_run_wizard_if_needed(app) -> bool:
    """
    Check if first run wizard is needed and run it.
    Returns True if app should continue, False if user cancelled.
    """
    if is_first_run():
        wizard = FirstRunWizard()
        result = wizard.exec()
        return result == QWizard.DialogCode.Accepted
    return True


if __name__ == "__main__":
    # Test the wizard
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    wizard = FirstRunWizard()
    wizard.show()
    sys.exit(app.exec())
