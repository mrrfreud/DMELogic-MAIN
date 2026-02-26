"""
scan.py — Scanner integration for DMELogic.

Supports three scanner modes:
  1. WIA (Windows Image Acquisition) — for scanners with WIA drivers
  2. File Picker — user scans with their scanner software (e.g. ScanSnap),
     then selects the resulting file
  3. Auto — tries WIA first, falls back to File Picker

Provides a helper to scan/select a document, copy it to the OCR folder,
and return the saved filename.
"""

from __future__ import annotations

import os
import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# WIA image format constants
WIA_FORMAT_PNG = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
WIA_FORMAT_BMP = "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}"
WIA_FORMAT_JPEG = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
WIA_FORMAT_TIFF = "{B96B3CB1-0728-11D3-9D7B-0000F81EF32E}"
WIA_FORMAT_PDF = "{D3CB2BF4-11A9-43C4-9B62-04E1CE28E8B8}"

# Scanner mode constants
MODE_AUTO = "Auto"
MODE_WIA = "WIA Only"
MODE_FILE_PICKER = "File Picker"

# Sentinel for "not supplied" (distinct from None / empty string)
_NOT_SET = object()


def _load_scanner_settings() -> dict:
    """Read scanner-related keys from the app settings file."""
    try:
        import json
        settings_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "DMELogic"
        settings_file = settings_dir / "settings.json"
        if settings_file.exists():
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "scanner_device_id": data.get("scanner_device_id", ""),
                "scan_format": data.get("scan_format", "PDF"),
                "scan_folder": data.get("scan_folder", ""),
                "scanner_mode": data.get("scanner_mode", MODE_AUTO),
                "scanner_app_path": data.get("scanner_app_path", ""),
                "scanner_output_folder": data.get("scanner_output_folder", ""),
            }
    except Exception:
        pass
    return {
        "scanner_device_id": "", "scan_format": "PDF", "scan_folder": "",
        "scanner_mode": MODE_AUTO, "scanner_app_path": "", "scanner_output_folder": "",
    }


def scan_document(
    parent_widget=None,
    suggested_name: str = "",
    save_folder: Path | str | None = _NOT_SET,
    as_pdf: bool | None = None,
    device_id: str | None = _NOT_SET,
) -> str | None:
    """Scan or select a document and save it to the OCR folder.

    Behaviour depends on the scanner mode in Settings:
      - **Auto**: tries WIA first; if no WIA scanner is found, falls
        back to a file-picker dialog.
      - **WIA Only**: uses WIA (shows error if no WIA scanner).
      - **File Picker**: always shows a file-picker so the user can
        scan with external software (e.g. ScanSnap) then select the
        resulting file.

    Args:
        parent_widget: Parent QWidget (for dialogs / message boxes).
        suggested_name: Suggested base filename (without extension).
        save_folder: Folder to save into. Defaults to the configured
                     scan folder or ``ocr_folder()``.
        as_pdf: If True save as PDF, False as PNG.
        device_id: WIA DeviceID to connect to directly.

    Returns:
        The saved filename (basename only), or ``None`` if cancelled.
    """
    # Load saved scanner settings for any parameter not explicitly supplied
    cfg = _load_scanner_settings()
    if device_id is _NOT_SET:
        device_id = cfg["scanner_device_id"] or None
    if save_folder is _NOT_SET:
        sf = cfg["scan_folder"]
        save_folder = sf if sf else None
    if as_pdf is None:
        as_pdf = cfg["scan_format"].upper() != "PNG"

    if save_folder is None:
        from dmelogic.paths import ocr_folder
        save_folder = ocr_folder()
    save_folder = Path(save_folder)
    save_folder.mkdir(parents=True, exist_ok=True)

    mode = cfg.get("scanner_mode", MODE_AUTO)

    if mode == MODE_FILE_PICKER:
        return _scan_via_file_picker(parent_widget, suggested_name, save_folder, as_pdf)

    if mode == MODE_WIA:
        return _scan_via_wia(parent_widget, suggested_name, save_folder, as_pdf, device_id)

    # Auto mode: try WIA, fall back to file picker
    result = _scan_via_wia(parent_widget, suggested_name, save_folder, as_pdf,
                           device_id, quiet_no_scanner=True)
    if result is not None:
        return result

    # WIA found nothing — offer file picker
    return _scan_via_file_picker(parent_widget, suggested_name, save_folder, as_pdf)


# ---------------------------------------------------------------------------
#  WIA scanning
# ---------------------------------------------------------------------------

def _scan_via_wia(
    parent_widget,
    suggested_name: str,
    save_folder: Path,
    as_pdf: bool,
    device_id: str | None,
    quiet_no_scanner: bool = False,
) -> str | None:
    """Acquire an image through WIA.

    If *quiet_no_scanner* is True and no scanner is detected, returns
    ``None`` silently (so the caller can fall back to file picker).
    """
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        if not quiet_no_scanner:
            _show_error(parent_widget, "pywin32 is not installed.\nInstall with: pip install pywin32")
        return None

    try:
        pythoncom.CoInitialize()

        if device_id:
            manager = win32com.client.Dispatch("WIA.DeviceManager")
            device = None
            for i in range(1, manager.DeviceInfos.Count + 1):
                info = manager.DeviceInfos.Item(i)
                if info.DeviceID == device_id:
                    device = info.Connect()
                    break
            if device is None:
                if not quiet_no_scanner:
                    _show_error(parent_widget,
                                "Configured scanner not found.\n\n"
                                "Check Settings → Scanner or select a different device.")
                return None
            item = device.Items(1)
            image = item.Transfer(WIA_FORMAT_PNG)
        else:
            # Check whether any WIA device exists before showing the dialog
            manager = win32com.client.Dispatch("WIA.DeviceManager")
            if manager.DeviceInfos.Count == 0:
                if not quiet_no_scanner:
                    _show_error(parent_widget,
                                "No WIA scanner found.\n\n"
                                "If you use a ScanSnap or similar scanner, go to\n"
                                "Settings → Scanner and change mode to\n"
                                "\"File Picker\" or \"Auto\".")
                return None
            wia_dialog = win32com.client.Dispatch("WIA.CommonDialog")
            image = wia_dialog.ShowAcquireImage()

        if image is None:
            return None

        return _save_scanned_image(image, suggested_name, save_folder, as_pdf)

    except Exception as e:
        error_msg = str(e)
        if "cancelled" in error_msg.lower() or "cancel" in error_msg.lower():
            return None
        if "-2145320939" in error_msg or "No scanner" in error_msg.lower():
            if not quiet_no_scanner:
                _show_error(parent_widget,
                            "No scanner found.\n\n"
                            "If you use a ScanSnap or similar scanner, go to\n"
                            "Settings → Scanner and change mode to\n"
                            "\"File Picker\" or \"Auto\".")
        elif "0x80210006" in error_msg:
            _show_error(parent_widget, "Scanner is busy or offline.\n\nPlease check the scanner and try again.")
        else:
            logger.error(f"Scan failed: {e}")
            if not quiet_no_scanner:
                _show_error(parent_widget, f"Scan failed:\n{e}")
        return None
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def _save_scanned_image(image, suggested_name: str, save_folder: Path, as_pdf: bool) -> str:
    """Save a WIA ImageFile to disk, optionally converting to PDF."""
    from datetime import datetime

    timestamp = datetime.now().strftime("%m-%d-%Y_%H%M%S")
    base = suggested_name.rstrip(".") if suggested_name else f"Scan_{timestamp}"
    ext = ".png"

    filename = f"{base}{ext}"
    save_path = save_folder / filename

    counter = 1
    while save_path.exists():
        filename = f"{base}_{counter}{ext}"
        save_path = save_folder / filename
        counter += 1

    image.SaveFile(str(save_path))
    logger.info(f"Scanned document saved: {save_path}")

    if as_pdf:
        pdf_filename = _convert_image_to_pdf(save_path)
        if pdf_filename:
            try:
                save_path.unlink()
            except OSError:
                pass
            return pdf_filename

    return filename


# ---------------------------------------------------------------------------
#  File-picker scanning (for ScanSnap, etc.)
# ---------------------------------------------------------------------------

def _scan_via_file_picker(
    parent_widget,
    suggested_name: str,
    save_folder: Path,
    as_pdf: bool,
) -> str | None:
    """Launch scanner software, watch for new files, let user confirm.

    Flow:
    1. Snapshot the scanner output folder
    2. Launch the scanner application (ScanSnap Home, etc.)
    3. Wait for the user to scan — show a dialog with a "Done Scanning" button
    4. Detect new files in the output folder
    5. If new file(s) found, auto-select the most recent one
    6. If nothing detected, fall back to a file picker
    7. Copy to OCR folder and return filename
    """
    import subprocess
    import time

    try:
        from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QDialog,
                                     QVBoxLayout, QLabel, QPushButton, QHBoxLayout)
        from PyQt6.QtCore import Qt
    except ImportError:
        _show_error(parent_widget, "PyQt6 is required.")
        return None

    cfg = _load_scanner_settings()
    scanner_app = cfg.get("scanner_app_path", "")
    output_folder = cfg.get("scanner_output_folder", "")

    # Determine the folder to watch for new scans
    watch_folder = Path(output_folder) if output_folder else None
    if watch_folder and not watch_folder.exists():
        watch_folder = None

    # If no scanner app or output folder configured, go straight to file picker
    if not scanner_app and not watch_folder:
        return _simple_file_picker(parent_widget, suggested_name, save_folder, as_pdf)

    # Snapshot existing files in the watch folder
    scan_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}
    existing_files: set[str] = set()
    if watch_folder:
        try:
            for f in watch_folder.iterdir():
                if f.is_file() and f.suffix.lower() in scan_extensions:
                    existing_files.add(str(f))
        except Exception:
            pass

    # Launch scanner application
    app_launched = False
    if scanner_app and Path(scanner_app).exists():
        try:
            subprocess.Popen([scanner_app], shell=False)
            app_launched = True
            logger.info(f"Launched scanner app: {scanner_app}")
        except Exception as e:
            logger.warning(f"Failed to launch scanner app: {e}")

    # Show "Done Scanning" dialog
    dlg = QDialog(parent_widget)
    dlg.setWindowTitle("Scan Document")
    dlg.setMinimumWidth(380)
    dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    layout = QVBoxLayout(dlg)

    if app_launched:
        msg = (
            "Your scanner software has been launched.\n\n"
            "1. Scan your document using the scanner\n"
            "2. Wait for scanning to complete\n"
            "3. Click 'Done Scanning' below"
        )
    else:
        msg = (
            "Press the Scan button on your scanner,\n"
            "or scan with your scanner software.\n\n"
            "When the scan is complete, click\n"
            "'Done Scanning' below."
        )

    label = QLabel(msg)
    label.setStyleSheet("font-size: 13px; padding: 10px;")
    layout.addWidget(label)

    btn_layout = QHBoxLayout()
    done_btn = QPushButton("✅ Done Scanning")
    done_btn.setStyleSheet("""
        QPushButton {
            background-color: #0d9488; color: white;
            font-weight: bold; padding: 10px 24px;
            border-radius: 6px; font-size: 13px;
        }
        QPushButton:hover { background-color: #0f766e; }
    """)
    done_btn.clicked.connect(dlg.accept)

    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet("padding: 10px 16px; font-size: 13px;")
    cancel_btn.clicked.connect(dlg.reject)

    pick_btn = QPushButton("📂 Pick File Manually")
    pick_btn.setStyleSheet("padding: 10px 16px; font-size: 13px;")
    pick_btn.setToolTip("Skip auto-detection and pick the scanned file yourself")

    # Use a flag to track manual pick
    manual_pick = [False]

    def on_manual_pick():
        manual_pick[0] = True
        dlg.accept()

    pick_btn.clicked.connect(on_manual_pick)

    btn_layout.addWidget(pick_btn)
    btn_layout.addStretch()
    btn_layout.addWidget(cancel_btn)
    btn_layout.addWidget(done_btn)
    layout.addLayout(btn_layout)

    result = dlg.exec()
    if result != QDialog.DialogCode.Accepted:
        return None

    # Manual pick requested
    if manual_pick[0]:
        start_dir = str(watch_folder) if watch_folder else ""
        return _simple_file_picker(parent_widget, suggested_name, save_folder, as_pdf,
                                   start_dir=start_dir)

    # Check for new files in watch folder
    new_file = None
    if watch_folder:
        try:
            new_files = []
            for f in watch_folder.iterdir():
                if f.is_file() and f.suffix.lower() in scan_extensions:
                    if str(f) not in existing_files:
                        new_files.append(f)
            if new_files:
                # Pick the most recently modified
                new_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                new_file = new_files[0]
                logger.info(f"Auto-detected new scan: {new_file}")
        except Exception as e:
            logger.warning(f"Error scanning output folder: {e}")

    if new_file is None:
        # Nothing auto-detected — fall back to file picker
        QMessageBox.information(
            parent_widget,
            "Scan",
            "No new scanned file was detected.\n\n"
            "Please select the scanned file manually.",
        )
        start_dir = str(watch_folder) if watch_folder else ""
        return _simple_file_picker(parent_widget, suggested_name, save_folder, as_pdf,
                                   start_dir=start_dir)

    # We found a new file — copy it to OCR folder
    return _copy_to_ocr_folder(new_file, suggested_name, save_folder, as_pdf, parent_widget)


def _simple_file_picker(
    parent_widget,
    suggested_name: str,
    save_folder: Path,
    as_pdf: bool,
    start_dir: str = "",
) -> str | None:
    """Plain file picker fallback."""
    from PyQt6.QtWidgets import QFileDialog

    file_filter = "Documents (*.pdf *.png *.jpg *.jpeg *.tif *.tiff *.bmp);;All Files (*)"
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select Scanned Document",
        start_dir,
        file_filter,
    )
    if not file_path:
        return None

    src = Path(file_path)
    if not src.exists():
        _show_error(parent_widget, f"File not found:\n{file_path}")
        return None

    return _copy_to_ocr_folder(src, suggested_name, save_folder, as_pdf, parent_widget)


def _copy_to_ocr_folder(
    src: Path,
    suggested_name: str,
    save_folder: Path,
    as_pdf: bool,
    parent_widget=None,
) -> str | None:
    """Copy a scanned file to the OCR folder, optionally converting to PDF."""
    if not src.exists():
        _show_error(parent_widget, f"File not found:\n{src}")
        return None

    # Build target filename
    timestamp = datetime.now().strftime("%m-%d-%Y_%H%M%S")
    base = suggested_name.rstrip(".") if suggested_name else f"Scan_{timestamp}"

    # Keep original extension unless user wants PDF conversion
    src_ext = src.suffix.lower()
    target_ext = src_ext if src_ext else ".pdf"

    filename = f"{base}{target_ext}"
    dest_path = save_folder / filename

    counter = 1
    while dest_path.exists():
        filename = f"{base}_{counter}{target_ext}"
        dest_path = save_folder / filename
        counter += 1

    # Copy file to OCR folder
    try:
        shutil.copy2(str(src), str(dest_path))
        logger.info(f"Copied scanned file: {src} -> {dest_path}")
    except Exception as e:
        _show_error(parent_widget, f"Failed to copy file:\n{e}")
        return None

    # Convert to PDF if requested and source isn't already PDF
    if as_pdf and target_ext != ".pdf":
        pdf_filename = _convert_image_to_pdf(dest_path)
        if pdf_filename:
            try:
                dest_path.unlink()
            except OSError:
                pass
            return pdf_filename

    return filename


def _convert_image_to_pdf(image_path: Path) -> str | None:
    """Convert a scanned image (PNG/TIFF) to PDF using Pillow or PyMuPDF.

    Returns the PDF filename (basename) or None on failure.
    """
    pdf_path = image_path.with_suffix(".pdf")

    # Try PyMuPDF (fitz) first — already in the project
    try:
        import fitz  # PyMuPDF
        doc = fitz.open()
        img = fitz.open(str(image_path))
        # Get image dimensions
        page = img[0]
        rect = page.rect
        pdf_page = doc.new_page(width=rect.width, height=rect.height)
        pdf_page.insert_image(rect, filename=str(image_path))
        doc.save(str(pdf_path))
        doc.close()
        img.close()
        return pdf_path.name
    except Exception:
        pass

    # Fallback to Pillow
    try:
        from PIL import Image
        img = Image.open(str(image_path))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(str(pdf_path), "PDF")
        img.close()
        return pdf_path.name
    except Exception:
        pass

    # Could not convert — return the image filename instead
    return None


def _show_error(parent_widget, message: str):
    """Show an error message box if we have a parent widget, otherwise print."""
    try:
        if parent_widget:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(parent_widget, "Scanner", message)
        else:
            print(f"Scanner error: {message}")
    except Exception:
        print(f"Scanner error: {message}")
