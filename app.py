"""
New entrypoint for DME Logic (refactored layout).
"""

import logging
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Fix Unicode output on Windows consoles that default to cp1252
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from dmelogic.ocr_status import ensure_ocr_configured
from dmelogic.ui import create_main_window
from dmelogic.paths import get_logs_dir, get_project_root, get_assets_dir, get_theme_dir

# Auth system imports
from dmelogic.db.users import init_users_db
from dmelogic.db.migrations import run_all_migrations
from dmelogic.security.auth import login, get_session
from dmelogic.ui.login_dialog import LoginDialog


def _ensure_venv():
    try:
        if not getattr(sys, "frozen", False):
            root_dir = os.path.dirname(os.path.abspath(__file__))
            venv_python = os.path.join(root_dir, "venv", "Scripts", "python.exe")
            if not os.path.exists(venv_python):
                venv_python = os.path.join(root_dir, "venv", "bin", "python")
            current = os.path.normpath(sys.executable)
            if os.path.exists(venv_python) and os.path.normpath(venv_python) != current:
                subprocess.call([venv_python, os.path.abspath(__file__)] + sys.argv[1:])
                sys.exit(0)
    except Exception:
        pass


def setup_logging() -> None:
    """Configure logging to file and console."""
    logs_dir = get_logs_dir()
    log_file = logs_dir / f"startup_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()  # also log to console
        ],
    )

    logging.info("=== DMELogic startup ===")
    logging.info(f"Project root: {get_project_root()}")
    logging.info(f"Assets dir:   {get_assets_dir()}")
    logging.info(f"Theme dir:    {get_theme_dir()}")
    logging.info(f"Frozen mode:  {getattr(sys, 'frozen', False)}")


def apply_theme(app: QApplication, theme_name: str = "light") -> None:
    """
    Load QSS from theme folder and apply to the app.
    
    Args:
        app: QApplication instance
        theme_name: "light" for light theme or "dark" for dark theme
    """
    logger = logging.getLogger("theme")

    if theme_name == "dark":
        qss_path = get_theme_dir() / "dark.qss"
    else:
        qss_path = get_theme_dir() / "light.qss"

    logger.info(f"Attempting to load theme '{theme_name}' from: {qss_path}")

    if not qss_path.exists():
        logger.warning(f"Theme file not found: {qss_path}")
        return

    try:
        with qss_path.open("r", encoding="utf-8") as f:
            qss = f.read()
        app.setStyleSheet(qss)
        logger.info(f"Theme '{theme_name}' successfully applied ({len(qss)} chars).")
    except Exception as e:
        logger.exception(f"Failed to apply theme '{theme_name}': {e}")


def main():
    _ensure_venv()
    
    # Setup logging first
    setup_logging()

    # Log where we are actually reading databases from
    try:
        from dmelogic.diagnostics import log_db_diagnostics

        log_db_diagnostics()
    except Exception:
        pass
    
    # Enable High DPI scaling for sharp fonts and modern appearance
    # Note: Qt6 has High DPI enabled by default, just set the rounding policy
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    logging.info("Creating QApplication...")
    app = QApplication(sys.argv)
    
    # Theme note:
    # The installed app UI look relies primarily on widget-level styling.
    # Do not force-apply a global QSS theme here; it can override that look.

    # Initialize user authentication database
    logging.info("Initializing authentication system...")
    try:
        init_users_db()
        logging.info("Authentication database initialized.")
    except Exception as e:
        logging.exception(f"Failed to initialize auth database: {e}")
        # Continue anyway - login dialog will show error

    # Run database migrations to ensure schema is up to date
    logging.info("Running database migrations...")
    try:
        run_all_migrations()
        logging.info("Database migrations completed.")
    except Exception as e:
        logging.exception(f"Failed to run migrations: {e}")
        # Continue anyway - app should handle missing columns gracefully

    # Configure OCR system and check status
    logging.info("Configuring OCR system...")
    ocr_status = ensure_ocr_configured()
    
    # --- Authentication: Show login dialog before main window ---
    logging.info("Showing login dialog...")
    login_dialog = LoginDialog()
    result = login_dialog.exec()
    
    if result != LoginDialog.DialogCode.Accepted:
        logging.info("Login cancelled or failed. Exiting application.")
        sys.exit(0)
    
    # Get authenticated session
    session = get_session()
    if not session or not session.is_authenticated:
        logging.error("No valid session after login. Exiting.")
        QMessageBox.critical(None, "Authentication Error", "No valid session established.")
        sys.exit(1)
    
    logging.info(f"User '{session.username}' logged in successfully")
    
    # Show warning if OCR features are limited
    if not ocr_status.fully_operational and not ocr_status.ocr_available:
        QMessageBox.warning(
            None,
            "OCR Features Limited",
            ocr_status.get_user_message()
        )
    
    logging.info("Creating main window...")
    win = create_main_window()
    
    # Apply permission-based UI restrictions
    _apply_permission_ui(win)
    
    # Update window title to show logged-in user
    from dmelogic.db.users import get_user_roles
    base_title = win.windowTitle()
    roles = get_user_roles(session.user_id, session._folder_path)
    role_str = ", ".join(roles) if roles else "User"
    win.setWindowTitle(f"{base_title}  |  👤 {session.username} ({role_str})")
    
    win.show()
    logging.info("Application started successfully.")
    
    # Show unbilled orders reminder after main window is shown
    _show_unbilled_orders_reminder(win)

    sys.exit(app.exec())


def _show_unbilled_orders_reminder(win) -> None:
    """
    Show a reminder popup for unbilled orders that need attention.
    Called after successful login.
    """
    import sqlite3
    from dmelogic.paths import db_dir
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtCore import QTimer
    
    logger = logging.getLogger("reminders")
    
    def show_reminder():
        try:
            orders_db = db_dir() / "orders.db"
            if not orders_db.exists():
                return
            
            conn = sqlite3.connect(str(orders_db))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Find orders with status "Unbilled" that need billing
            cur.execute("""
                SELECT id, patient_name, order_status, order_date, delivery_date
                FROM orders
                WHERE order_status = 'Unbilled'
                ORDER BY order_date ASC
                LIMIT 20
            """)
            unbilled = cur.fetchall()
            
            # Also check for orders on hold that are due to release
            cur.execute("""
                SELECT id, patient_name, hold_until_date, hold_resume_status
                FROM orders
                WHERE order_status = 'On Hold'
                  AND hold_until_date IS NOT NULL
                  AND date(hold_until_date) <= date('now')
            """)
            due_holds = cur.fetchall()
            
            conn.close()
            
            messages = []
            
            if unbilled:
                unbilled_list = []
                for row in unbilled[:10]:  # Show top 10
                    order_num = f"ORD-{row['id']:03d}"
                    patient = row['patient_name'] or "Unknown"
                    status = row['order_status']
                    unbilled_list.append(f"  • {order_num}: {patient} ({status})")
                
                more_text = f"\n  ... and {len(unbilled) - 10} more" if len(unbilled) > 10 else ""
                messages.append(
                    f"⚠️ UNBILLED ORDERS ({len(unbilled)}):\n" +
                    "\n".join(unbilled_list) + more_text
                )
            
            if due_holds:
                hold_list = []
                for row in due_holds[:5]:
                    order_num = f"ORD-{row['id']:03d}"
                    patient = row['patient_name'] or "Unknown"
                    resume = row['hold_resume_status'] or "Pending"
                    hold_list.append(f"  • {order_num}: {patient} → {resume}")
                
                messages.append(
                    f"⏰ HOLDS DUE FOR RELEASE ({len(due_holds)}):\n" +
                    "\n".join(hold_list)
                )
            
            if messages:
                msg_box = QMessageBox(win)
                msg_box.setWindowTitle("📋 Orders Requiring Attention")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setText("The following orders need your attention:")
                msg_box.setDetailedText("\n\n".join(messages))
                msg_box.setInformativeText(
                    f"{len(unbilled)} unbilled orders, {len(due_holds)} holds due"
                )
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
                
                logger.info(f"Shown unbilled reminder: {len(unbilled)} unbilled, {len(due_holds)} holds due")
            
        except Exception as e:
            logger.warning(f"Failed to show unbilled orders reminder: {e}")
    
    # Use QTimer to show after window is fully visible
    QTimer.singleShot(500, show_reminder)


def _apply_permission_ui(win) -> None:
    """
    Apply permission-based visibility/enabled state to UI elements.
    Called after login to hide/disable features the user cannot access.
    """
    from dmelogic.security.permissions import has_permission
    from dmelogic.security.auth import get_session
    
    logger = logging.getLogger("permissions")
    session = get_session()
    
    if not session or not session.is_authenticated:
        logger.warning("No session when applying UI permissions")
        return
    
    logger.info(f"Applying UI permissions for user '{session.username}'")
    
    # Example: Hide financial columns if user lacks financial.view
    # This will be implemented per-widget as needed
    
    # Check if main window has the tabs we want to gate
    if hasattr(win, 'tabs'):
        tabs = win.tabs
        
        # Hide Inventory tab if no inventory permissions
        if not has_permission("inventory.view"):
            for i in range(tabs.count()):
                if tabs.tabText(i) == "Inventory":
                    tabs.setTabVisible(i, False)
                    logger.info("Hidden: Inventory tab")
                    break
        
        # Reports tab - hide if no reports permission
        if not has_permission("reports.view"):
            for i in range(tabs.count()):
                if "Report" in tabs.tabText(i):
                    tabs.setTabVisible(i, False)
                    logger.info(f"Hidden: {tabs.tabText(i)} tab")
    
    logger.info("UI permissions applied")


if __name__ == "__main__":
    main()
