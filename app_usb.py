"""
USB Installer entrypoint for DME Logic.
Identical to app.py but adds a First-Run Setup Wizard for fresh installs.

This file is ONLY used by the USB installer - not for development.
"""

import logging
import sys

# Import the main app module — we reuse its main() entirely
import app as main_app


# Monkey-patch: inject the first-run wizard check into app.main()
_original_main = main_app.main


def _usb_main():
    """
    Run the first-run wizard (if needed) before handing off to app.main().
    Everything else — theme, DPI, permissions, reminders — comes from app.py
    so the USB version is always identical to the original.
    """
    main_app._ensure_venv()
    main_app.setup_logging()

    logging.info("USB installer entry point — checking for first run...")

    from dmelogic.ui.first_run_wizard import is_first_run

    if is_first_run():
        # We need a temporary QApplication for the wizard
        from PyQt6.QtWidgets import QApplication
        from dmelogic.ui.first_run_wizard import run_first_run_wizard_if_needed

        temp_app = QApplication.instance() or QApplication(sys.argv)
        logging.info("First run detected — showing setup wizard...")
        if not run_first_run_wizard_if_needed(temp_app):
            logging.info("Setup wizard cancelled. Exiting.")
            sys.exit(0)
        logging.info("Setup wizard completed successfully.")
        # Clean up the temporary app so app.main() can create its own
        del temp_app

    # Now run the real app.main() — theme, permissions, reminders all included
    _original_main()


if __name__ == "__main__":
    _usb_main()
