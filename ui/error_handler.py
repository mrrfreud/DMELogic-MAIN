"""
User-friendly error handling for UI components.

Provides consistent error dialogs with:
- User-friendly messages
- Technical details (optional)
- Log file references
- Action buttons

Usage:
    from ui.error_handler import show_error, show_warning, show_db_error
    
    # Simple error
    show_error(parent, "Could not save patient", "The database is locked by another process.")
    
    # Database error with exception
    try:
        create_order(...)
    except Exception as e:
        show_db_error(parent, "Could not create order", e)
"""

from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import Qt
from dmelogic.config import debug_log
from dmelogic.paths import debug_log_path


def show_error(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None,
    log_reference: bool = True
) -> None:
    """
    Show a user-friendly error dialog.
    
    Args:
        parent: Parent widget (can be None)
        title: Short error title
        message: User-friendly message
        details: Optional technical details
        log_reference: Whether to show log file location
    """
    debug_log(f"UI Error: {title} - {message}")
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    # Build informative text
    info_parts = []
    if details:
        info_parts.append(f"Details: {details}")
    if log_reference:
        log_file = debug_log_path()
        info_parts.append(f"\nPlease check the log file for more information:\n{log_file}")
    
    if info_parts:
        msg_box.setInformativeText("\n".join(info_parts))
    
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def show_warning(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None
) -> None:
    """
    Show a user-friendly warning dialog.
    
    Args:
        parent: Parent widget (can be None)
        title: Short warning title
        message: User-friendly message
        details: Optional technical details
    """
    debug_log(f"UI Warning: {title} - {message}")
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if details:
        msg_box.setInformativeText(f"Details: {details}")
    
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def show_db_error(
    parent: Optional[QWidget],
    operation: str,
    exception: Exception,
    user_action: Optional[str] = None
) -> None:
    """
    Show a database error dialog with user-friendly message.
    
    Args:
        parent: Parent widget (can be None)
        operation: What operation failed (e.g., "save patient", "create order")
        exception: The exception that was raised
        user_action: Optional suggestion for user (e.g., "Please try again later")
    """
    debug_log(f"DB Error during {operation}: {exception}")
    
    # Build user-friendly message
    message = f"Could not {operation}."
    if user_action:
        message += f"\n\n{user_action}"
    
    # Technical details
    exception_type = type(exception).__name__
    exception_msg = str(exception)
    details = f"{exception_type}: {exception_msg}"
    
    show_error(
        parent,
        f"Database Error - {operation.title()}",
        message,
        details=details,
        log_reference=True
    )


def show_validation_error(
    parent: Optional[QWidget],
    title: str,
    errors: list[str]
) -> None:
    """
    Show a validation error dialog with list of errors.
    
    Args:
        parent: Parent widget (can be None)
        title: Dialog title
        errors: List of validation error messages
    """
    debug_log(f"Validation Error: {title} - {len(errors)} errors")
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText("Please correct the following errors:")
    
    # Format error list
    error_list = "\n".join(f"• {error}" for error in errors)
    msg_box.setInformativeText(error_list)
    
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


def show_confirmation(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None
) -> bool:
    """
    Show a confirmation dialog.
    
    Args:
        parent: Parent widget (can be None)
        title: Dialog title
        message: Confirmation message
        details: Optional additional details
        
    Returns:
        bool: True if user clicked Yes, False otherwise
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if details:
        msg_box.setInformativeText(details)
    
    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    
    result = msg_box.exec()
    return result == QMessageBox.StandardButton.Yes


def show_success(
    parent: Optional[QWidget],
    title: str,
    message: str
) -> None:
    """
    Show a success notification dialog.
    
    Args:
        parent: Parent widget (can be None)
        title: Dialog title
        message: Success message
    """
    debug_log(f"UI Success: {title} - {message}")
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    # Auto-close after 3 seconds (optional, can be configured)
    msg_box.exec()


# ============================================================================
# Exception Context Manager for UI Operations
# ============================================================================

from contextlib import contextmanager
from typing import Generator


@contextmanager
def ui_exception_handler(
    parent: Optional[QWidget],
    operation: str,
    success_message: Optional[str] = None
) -> Generator[None, None, None]:
    """
    Context manager for handling exceptions in UI operations.
    
    Usage:
        with ui_exception_handler(self, "save patient", "Patient saved successfully"):
            save_patient(patient_data)
            
    Args:
        parent: Parent widget for dialogs
        operation: Description of operation (e.g., "save patient")
        success_message: Optional success message to show if operation succeeds
    """
    try:
        yield
        if success_message:
            show_success(parent, "Success", success_message)
    except ValueError as e:
        # Validation errors - user-friendly
        show_validation_error(parent, "Validation Error", [str(e)])
    except Exception as e:
        # Database or other errors
        show_db_error(
            parent,
            operation,
            e,
            user_action="Please try again. If the problem persists, contact support."
        )


# ============================================================================
# Async Operation Error Handler (for threaded operations)
# ============================================================================

def show_async_error(
    parent: Optional[QWidget],
    operation: str,
    error_message: str
) -> None:
    """
    Show error from async/threaded operation.
    
    Use this when catching errors from worker threads.
    
    Args:
        parent: Parent widget
        operation: What operation failed
        error_message: Error message from worker thread
    """
    debug_log(f"Async Error during {operation}: {error_message}")
    
    show_error(
        parent,
        f"Error - {operation.title()}",
        f"Could not {operation}.",
        details=error_message,
        log_reference=True
    )
