"""
backup.py — Backup + restore functionality for database and settings.
"""

import os
import json
import zipfile
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QDateTime, QTimer
from .config import SETTINGS_FILE, DB_FILES, DB_EXCLUDE, debug_log
from .paths import backup_dir, db_dir


# ----------------------------------------------------------
# UTILITY FUNCTIONS
# ----------------------------------------------------------
def discover_databases(folder_path: Path, exclude_list=None) -> list:
    """
    Auto-discover all .db files in the specified folder.
    
    Args:
        folder_path: Path to search for databases
        exclude_list: List of database filenames to exclude (e.g., temp.db)
    
    Returns:
        List of database filenames found
    """
    if exclude_list is None:
        exclude_list = DB_EXCLUDE
    
    if not folder_path.exists():
        return []
    
    discovered = []
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix == ".db":
            if item.name not in exclude_list:
                discovered.append(item.name)
    
    return sorted(discovered)


class BackupWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, mode: str, source_path: str = None, backup_path: str = None, auto_discover=False):
        super().__init__()
        self.mode = mode
        self.source_path = source_path
        self.backup_path = backup_path
        self.auto_discover = auto_discover  # If True, discover all .db files dynamically

    # ----------------------------------------------------------
    # MAIN RUN
    # ----------------------------------------------------------
    def run(self):
        try:
            if self.mode == "backup":
                result = self.create_backup()
                self.finished.emit(result)

            elif self.mode == "restore":
                self.restore_backup()
                self.finished.emit("Restore complete.")

            else:
                self.error.emit(f"[BackupWorker] Unknown mode: {self.mode}")

        except Exception as e:
            self.error.emit(str(e))


    # ----------------------------------------------------------
    # CREATE BACKUP ZIP
    # ----------------------------------------------------------
    def create_backup(self) -> str:
        if not self.source_path:
            raise ValueError("BackupWorker: source_path not set.")

        bdir = backup_dir()
        bdir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_zip = bdir / f"dmesolutions_backup_{timestamp}.zip"

        # Get db_folder from centralized paths
        db_folder = db_dir()

        # Determine which databases to backup
        if self.auto_discover:
            # Auto-discover all .db files (excluding temp/cache)
            discovered = discover_databases(db_folder, DB_EXCLUDE)
            db_names = list(set(DB_FILES + discovered))  # Combine + deduplicate
            debug_log(f"Auto-discovered databases: {discovered}")
            debug_log(f"Total databases to backup: {len(db_names)}")
        else:
            # Use centralized DB list from config (single source of truth)
            db_names = DB_FILES

        search_paths = [Path(self.source_path), db_folder]

        def find_db(name):
            for base in search_paths:
                p = base / name
                if p.exists():
                    return p
            return None

        self.progress.emit(5)

        with zipfile.ZipFile(str(backup_zip), "w", compression=zipfile.ZIP_DEFLATED) as z:

            # Save settings.json
            settings_path = Path(SETTINGS_FILE)
            if settings_path.exists():
                z.write(str(settings_path), SETTINGS_FILE)

            self.progress.emit(15)

            # Include DBs
            step = 80 // len(db_names)
            p = 15

            for db in db_names:
                db_path = find_db(db)
                if db_path:
                    z.write(str(db_path), f"databases/{db}")

                p += step
                self.progress.emit(min(p, 95))

        self.progress.emit(100)
        return backup_zip


    # ----------------------------------------------------------
    # RESTORE BACKUP ZIP
    # ----------------------------------------------------------
    def restore_backup(self):
        """
        Restore backup with safety measures:
        1. Backup current files to .bak before overwriting
        2. Use atomic replace for settings.json
        3. Keep .bak files on failure for manual recovery
        """
        if not self.backup_path or not os.path.exists(self.backup_path):
            raise ValueError("BackupWorker: backup_path invalid.")

        # Extract to temporary folder
        tmp = tempfile.mkdtemp(prefix="DME_Restore_")
        with zipfile.ZipFile(self.backup_path, "r") as z:
            z.extractall(tmp)

        self.progress.emit(20)

        # Restore settings.json with atomic replace
        extracted_settings = os.path.join(tmp, SETTINGS_FILE)
        if os.path.exists(extracted_settings):
            try:
                # Ensure settings file directory is writable
                settings_dir = os.path.dirname(SETTINGS_FILE) or "."
                if not os.access(settings_dir, os.W_OK):
                    raise PermissionError(f"Cannot write to settings directory: {settings_dir}")
                
                # Backup current settings before overwriting
                if os.path.exists(SETTINGS_FILE):
                    backup_settings = SETTINGS_FILE + ".bak"
                    try:
                        shutil.copy2(SETTINGS_FILE, backup_settings)
                        debug_log(f"Backed up current settings to {backup_settings}")
                    except PermissionError:
                        debug_log(f"Warning: Could not backup settings (permission denied)")
                
                # Atomic replace: write to temp, then rename
                tmp_settings = SETTINGS_FILE + ".tmp"
                shutil.copy2(extracted_settings, tmp_settings)
                
                # Try atomic replace
                try:
                    os.replace(tmp_settings, SETTINGS_FILE)  # Atomic on Windows/POSIX
                    debug_log("Settings restored successfully")
                except PermissionError:
                    # Cleanup temp file on permission error
                    try:
                        os.remove(tmp_settings)
                    except:
                        pass
                    raise PermissionError(
                        f"Permission denied: Cannot write to '{SETTINGS_FILE}'.\n\n"
                        f"Try running the application as Administrator, or\n"
                        f"manually copy the settings file from the backup."
                    )
                
            except PermissionError:
                raise  # Re-raise permission errors with clear message
            except Exception as e:
                debug_log(f"Settings restore failed: {e} (check .bak for recovery)")
                raise

        self.progress.emit(40)

        # Determine DB target folder
        db_folder = db_dir()
        db_folder.mkdir(parents=True, exist_ok=True)

        # Restore databases with safety backups
        db_extract_dir = os.path.join(tmp, "databases")
        if os.path.exists(db_extract_dir):
            db_files = [f for f in os.listdir(db_extract_dir) if f.endswith(".db")]
            step = 55 // max(len(db_files), 1)
            p = 40
            
            for file in db_files:
                try:
                    target_db = db_folder / file
                    
                    # Backup current DB before overwriting
                    if target_db.exists():
                        backup_db = str(target_db) + ".bak"
                        shutil.copy2(str(target_db), backup_db)
                        debug_log(f"Backed up {file} to {backup_db}")
                    
                    # Atomic replace: copy to temp, then rename
                    tmp_db = str(target_db) + ".tmp"
                    shutil.copy2(os.path.join(db_extract_dir, file), tmp_db)
                    os.replace(tmp_db, str(target_db))  # Atomic
                    debug_log(f"Restored {file} successfully")
                    
                except Exception as e:
                    debug_log(f"Failed to restore {file}: {e} (check .bak for recovery)")
                    # Continue with other databases even if one fails
                
                p += step
                self.progress.emit(min(p, 95))

        self.progress.emit(100)
        debug_log("Restore complete. Backup files (.bak) kept for safety.")


class AutoBackupScheduler(QThread):
    """
    Auto-backup scheduler with improved timing.
    
    Instead of checking every second, calculates the exact next run time
    and sleeps until then. This is more efficient and reliable.
    
    Note: For production, consider using OS-level task scheduling (Windows Task
    Scheduler, cron) for reliability when app isn't running.
    """
    backup_triggered = pyqtSignal()

    def __init__(self, frequency="Daily", backup_hour=0, backup_minute=0):
        super().__init__()
        self.frequency = frequency
        self.backup_hour = backup_hour
        self.backup_minute = backup_minute
        self.running = True
        self._last_backup_date = None

    def run(self):
        """Main thread loop - sleeps until next backup time."""
        debug_log(f"AutoBackupScheduler started (frequency: {self.frequency}, time: {self.backup_hour:02d}:{self.backup_minute:02d})")
        
        while self.running:
            now = QDateTime.currentDateTime()
            next_run = self._calculate_next_run(now)
            
            if next_run is None:
                # Shouldn't happen, but safety check
                self.msleep(60000)
                continue
            
            # Calculate milliseconds until next run
            ms_until_next = now.msecsTo(next_run)
            
            if ms_until_next <= 0:
                # Time to run backup
                current_date = now.date().toString("yyyy-MM-dd")
                
                # Prevent duplicate backups on same date
                if self._last_backup_date != current_date:
                    debug_log(f"Triggering auto-backup at {now.toString('yyyy-MM-dd HH:mm:ss')}")
                    self.backup_triggered.emit()
                    self._last_backup_date = current_date
                    
                    # Sleep for 2 minutes to avoid immediate re-trigger
                    self.msleep(120000)
                else:
                    # Already backed up today, wait 1 hour
                    self.msleep(3600000)
            else:
                # Sleep until next run (max 1 hour chunks to allow stopping)
                sleep_time = min(ms_until_next, 3600000)  # Max 1 hour
                debug_log(f"Next backup in {ms_until_next // 60000} minutes")
                self.msleep(int(sleep_time))

    def _calculate_next_run(self, now: QDateTime) -> QDateTime:
        """
        Calculate the exact next backup time based on frequency.
        
        Returns:
            QDateTime of next scheduled backup
        """
        target_time = now.time()
        target_time.setHMS(self.backup_hour, self.backup_minute, 0)
        
        if self.frequency == "Daily":
            # Daily: same time every day
            next_run = QDateTime(now.date(), target_time)
            if next_run <= now:
                # If time already passed today, schedule for tomorrow
                next_run = next_run.addDays(1)
            return next_run
        
        elif self.frequency == "Weekly":
            # Weekly: every Sunday (dayOfWeek 7) at target time
            next_run = QDateTime(now.date(), target_time)
            days_until_sunday = (7 - now.date().dayOfWeek()) % 7
            
            if days_until_sunday == 0 and next_run > now:
                # Today is Sunday and time hasn't passed
                return next_run
            elif days_until_sunday == 0:
                # Today is Sunday but time passed, next Sunday
                return next_run.addDays(7)
            else:
                # Not Sunday, calculate days until next Sunday
                return next_run.addDays(days_until_sunday)
        
        elif self.frequency == "Monthly":
            # Monthly: 1st of each month at target time
            next_run = QDateTime(now.date(), target_time)
            
            if now.date().day() == 1 and next_run > now:
                # Today is 1st and time hasn't passed
                return next_run
            else:
                # Schedule for 1st of next month
                next_run = next_run.addMonths(1)
                next_date = next_run.date()
                next_date.setDate(next_date.year(), next_date.month(), 1)
                return QDateTime(next_date, target_time)
        
        # Fallback: 24 hours from now
        return now.addSecs(86400)

    def stop(self):
        """Stop the scheduler gracefully."""
        debug_log("AutoBackupScheduler stopping...")
        self.running = False
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds for graceful shutdown
