# Backup System Quick Reference

## Adding a New Database

**File:** `dmelogic/config.py`

```python
DB_FILES = [
    "patients.db",
    "orders.db",
    # Add your new database here:
    "claims.db",        # ← One line!
    "audit_log.db",     # ← That's it!
]
```

## Creating a Backup

### Manual Database List (Default, Safe)
```python
from dmelogic.backup import BackupWorker

worker = BackupWorker(
    mode="backup",
    source_path=current_folder
)
worker.run()
```

### Auto-Discovery (Catches All Databases)
```python
worker = BackupWorker(
    mode="backup",
    source_path=current_folder,
    auto_discover=True  # Finds all .db files
)
worker.run()
```

## Restoring a Backup

```python
worker = BackupWorker(
    mode="restore",
    backup_path="path/to/backup.zip"
)
worker.run()
```

**Safety Features:**
- Creates `.bak` files before overwriting
- Uses atomic `os.replace()` operations
- Continues on individual file failures
- Logs all operations for recovery

**Manual Recovery (if restore fails):**
```bash
# Check for backup files
dir *.bak

# Restore manually
copy settings.json.bak settings.json
copy patients.db.bak patients.db
```

## Scheduling Auto-Backups

### Default (Daily at Midnight)
```python
from dmelogic.backup import AutoBackupScheduler

scheduler = AutoBackupScheduler(frequency="Daily")
scheduler.backup_triggered.connect(do_backup)
scheduler.start()
```

### Custom Time
```python
scheduler = AutoBackupScheduler(
    frequency="Daily",
    backup_hour=2,      # 2:30 AM
    backup_minute=30
)
scheduler.start()
```

### Weekly or Monthly
```python
# Every Sunday at 2:30 AM
scheduler = AutoBackupScheduler(
    frequency="Weekly",
    backup_hour=2,
    backup_minute=30
)

# First of month at 3:00 AM
scheduler = AutoBackupScheduler(
    frequency="Monthly",
    backup_hour=3,
    backup_minute=0
)
```

### Stop Scheduler
```python
scheduler.stop()  # Graceful shutdown (5 second timeout)
```

## Auto-Discovery Function

```python
from dmelogic.backup import discover_databases
from dmelogic.paths import db_dir

# Find all databases
databases = discover_databases(db_dir())
print(f"Found: {databases}")

# Exclude specific databases
databases = discover_databases(
    db_dir(),
    exclude_list=["temp.db", "cache.db", "test.db"]
)
```

## Configuration Files

### Database List
**File:** `dmelogic/config.py`
```python
DB_FILES = [...]      # Databases to backup
DB_EXCLUDE = [...]    # Exclude from auto-discovery
```

### Paths
**File:** `dmelogic/paths.py`
```python
db_dir()      # Database folder
backup_dir()  # Backup folder
```

## Logging and Monitoring

All operations logged to `Logs/print_debug.log`:

```python
from dmelogic.config import debug_log

debug_log("Custom backup operation started")
```

**Log Examples:**
```
[2025-12-05 20:41:45] AutoBackupScheduler started (frequency: Daily, time: 02:30)
[2025-12-05 20:41:45] Next backup in 349 minutes
[2025-12-05 20:41:45] Auto-discovered databases: ['claims.db', 'audit_log.db']
[2025-12-05 20:41:45] Backed up patients.db to patients.db.bak
[2025-12-05 20:41:45] Restored patients.db successfully
```

## Production Deployment

### Recommended: OS-Level Task Scheduling

**Windows Task Scheduler:**
```powershell
schtasks /create /tn "DMELogic Backup" /tr "C:\path\to\backup.exe" /sc daily /st 02:30
```

**Linux Cron:**
```bash
# Daily 2:30 AM
30 2 * * * /usr/bin/python3 /path/to/backup.py
```

**Why?**
- Runs even if app is closed
- Survives crashes/reboots
- OS-managed reliability

### Best Practices

1. **Test restores regularly** - Verify backups work
2. **Keep multiple generations** - 7 daily, 4 weekly, 12 monthly
3. **Offsite backups** - Cloud or network drive
4. **Monitor disk space** - Cleanup old backups
5. **Check logs** - Look for failures

## Troubleshooting

### Backup Fails
```bash
# Check logs
type Logs\print_debug.log | findstr "backup"

# Check disk space
dir C:\Dme_Solutions\Backups

# Check permissions
icacls C:\Dme_Solutions\Backups
```

### Restore Fails
```bash
# Check for .bak files
dir *.bak

# Restore manually
copy settings.json.bak settings.json

# Check database integrity
sqlite3 patients.db "PRAGMA integrity_check;"
```

### Scheduler Not Triggering
```bash
# Check logs for next run time
type Logs\print_debug.log | findstr "Next backup"

# Verify scheduler is running
# (Should see "AutoBackupScheduler started")

# Check frequency and time settings
```

## Common Patterns

### Full Backup with UI Progress
```python
from PyQt6.QtCore import QThread

class BackupThread(QThread):
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
    
    def run(self):
        worker = BackupWorker("backup", self.folder, auto_discover=True)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.on_complete)
        worker.error.connect(self.on_error)
        worker.run()
    
    def update_progress(self, percent):
        print(f"Progress: {percent}%")
    
    def on_complete(self, zip_path):
        print(f"Backup created: {zip_path}")
    
    def on_error(self, error_msg):
        print(f"Error: {error_msg}")
```

### Scheduled Backup with Notification
```python
scheduler = AutoBackupScheduler("Daily", backup_hour=2, backup_minute=30)

def do_scheduled_backup():
    worker = BackupWorker("backup", current_folder, auto_discover=True)
    worker.finished.connect(lambda path: print(f"Auto-backup: {path}"))
    worker.run()

scheduler.backup_triggered.connect(do_scheduled_backup)
scheduler.start()
```

### Restore with Confirmation
```python
def restore_with_confirm(backup_zip):
    reply = QMessageBox.question(
        parent,
        "Restore Backup",
        f"Restore from {backup_zip}?\n\n"
        "Current files will be backed up to .bak",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        worker = BackupWorker("restore", backup_path=backup_zip)
        worker.finished.connect(lambda: QMessageBox.information(
            parent, "Success", "Restore complete!\n.bak files preserved."
        ))
        worker.run()
```

## API Reference

### BackupWorker

**Constructor:**
```python
BackupWorker(
    mode: str,              # "backup" or "restore"
    source_path: str = None,  # For backup
    backup_path: str = None,  # For restore
    auto_discover: bool = False  # Auto-find databases
)
```

**Signals:**
```python
progress = pyqtSignal(int)      # Progress 0-100
finished = pyqtSignal(str)      # Result message
error = pyqtSignal(str)         # Error message
```

**Methods:**
```python
worker.run()  # Execute backup/restore
```

### AutoBackupScheduler

**Constructor:**
```python
AutoBackupScheduler(
    frequency: str = "Daily",    # "Daily", "Weekly", "Monthly"
    backup_hour: int = 0,        # 0-23
    backup_minute: int = 0       # 0-59
)
```

**Signals:**
```python
backup_triggered = pyqtSignal()  # Emitted when backup should run
```

**Methods:**
```python
scheduler.start()  # Start scheduler thread
scheduler.stop()   # Stop gracefully (5s timeout)
```

### discover_databases

**Function:**
```python
discover_databases(
    folder_path: Path,
    exclude_list: list = None  # Defaults to DB_EXCLUDE
) -> list  # Returns list of database filenames
```

---

**For full documentation, see:** `BACKUP_IMPROVEMENTS.md`
