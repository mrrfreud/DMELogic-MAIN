"""
USB Installer entrypoint for DME Logic.
This is a wrapper around app.py that includes the First-Run Setup Wizard
for new installations on PCs that don't have DMELogic configured.

This file is ONLY used by the USB installer - not for development.
"""

import logging
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

# Import the first-run wizard
from dmelogic.ui.first_run_wizard import run_first_run_wizard_if_needed, is_first_run

# Import the main app module to reuse its functions
import app as main_app


def main():
    """USB installer entry point with first-run wizard support."""
    main_app._ensure_venv()
    
    # Setup logging first
    main_app.setup_logging()

    # Log where we are actually reading databases from (before wizard/migrations)
    try:
        from dmelogic.diagnostics import log_db_diagnostics

        log_db_diagnostics()
    except Exception:
        pass
    
    logging.info("USB Installer version - Creating QApplication...")
    qt_app = QApplication(sys.argv)

    # Theme note:
    # The installed app UI look relies primarily on widget-level styling.
    # Do not force-apply a global QSS theme here; it can override that look.
    
    # --- First Run Wizard: Check if setup is needed ---
    if is_first_run():
        logging.info("First run detected - showing setup wizard...")
        if not run_first_run_wizard_if_needed(qt_app):
            logging.info("Setup wizard cancelled. Exiting application.")
            sys.exit(0)
        logging.info("Setup wizard completed successfully.")
    
    # Now continue with the rest of the main app initialization
    # Import here to avoid circular imports and ensure wizard runs first
    from dmelogic.db.users import init_users_db
    from dmelogic.db.migrations import run_all_migrations
    from dmelogic.security.auth import login, get_session
    from dmelogic.ui.login_dialog import LoginDialog
    from dmelogic.ui import create_main_window
    from dmelogic.ocr_status import ensure_ocr_configured
    
    # Initialize user authentication database
    logging.info("Initializing authentication system...")
    try:
        init_users_db()
        logging.info("Authentication database initialized.")
    except Exception as e:
        logging.exception(f"Failed to initialize auth database: {e}")
    
    # Run database migrations
    logging.info("Running database migrations...")
    try:
        run_all_migrations()
        logging.info("Database migrations completed.")
    except Exception as e:
        logging.exception(f"Error running migrations: {e}")
    
    # OCR configuration check
    try:
        ensure_ocr_configured()
    except Exception as e:
        logging.warning(f"OCR configuration check failed: {e}")
    
    # Show login dialog
    logging.info("Showing login dialog...")
    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        logging.info("Login cancelled or failed. Exiting application.")
        sys.exit(0)
    
    session = get_session()
    if not session:
        logging.error("No session after login accepted. Exiting.")
        sys.exit(1)
    
    # AuthSession does not expose a .role attribute; compute roles from the users DB.
    role_str = "User"
    try:
        from dmelogic.db.users import get_user_roles

        roles = get_user_roles(session.user_id, getattr(session, "_folder_path", None))
        role_str = ", ".join(roles) if roles else "User"
    except Exception:
        role_str = "User"

    logging.info(f"User '{session.username}' logged in successfully (roles: {role_str})")
    
    # Create and show main window
    logging.info("Creating main window...")
    main_window = create_main_window()
    
    if main_window is None:
        logging.error("Failed to create main window. Exiting.")
        sys.exit(1)
    
    # Set user info on main window if supported
    if hasattr(main_window, 'set_current_user'):
        try:
            main_window.set_current_user(session.username, role_str)
        except TypeError:
            # Backward-compat: some windows only accept username.
            main_window.set_current_user(session.username)
    
    main_window.show()
    logging.info("Main window displayed. Starting event loop.")
    
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
