# Database Sync Issue - SOLVED

## The Problem

Your installed application was using a **completely different database** than your development environment:

- **Development**: `C:\Dme_Solutions\Data\*.db`
- **Installed App**: `C:\ProgramData\DMELogic\Data\*.db`

This is why:
- ✅ Terminal `python app.py` showed updated data (Medicaid, more patients, etc.)
- ❌ Installed app showed old data (EPACES, only 2 patients, etc.)

## The Root Cause

1. The installer creates databases in `C:\ProgramData\DMELogic\Data`
2. The installer creates a `data_path.txt` file pointing to this location
3. **BUT** the application code wasn't reading this file!
4. Result: Two separate databases that never sync

## The Fix

### 1. Application Code Updated ✅

**File**: `dmelogic\paths.py`

Added logic to detect installed apps and read `data_path.txt`:

```python
def _get_installed_data_path() -> Path | None:
    """Check if running from an installed version and read data_path.txt."""
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        data_path_file = exe_dir / "data_path.txt"
        if data_path_file.exists():
            # Read and use the correct path
            ...
```

Now the installed app will **automatically use the correct database location**.

### 2. Database Sync Utility Created ✅

**File**: `sync_databases.py`

Interactive tool to sync databases between dev and installed app:

```powershell
python sync_databases.py
```

**Options:**
1. **Show status** - View both database locations
2. **Sync DEV → INSTALLED** - Copy your current data to installed app
3. **Sync INSTALLED → DEV** - Copy installed app data back to dev
4. **Exit**

### 3. New Build Script with Database Bundling ✅

**File**: `BUILD_WITH_DATABASE.bat`

This script:
1. Copies your current databases to `installer_data\` folder
2. Builds the PyInstaller executable
3. Creates the installer with your databases included
4. New installations will have your current data

### 4. Installer Script Updated ✅

**File**: `installer_script.iss`

Now copies database files from `installer_data\` to the installed app's data directory during installation.

## How to Use

### Option A: Quick Fix (Sync Existing Databases)

1. Run the sync utility:
   ```powershell
   python sync_databases.py
   ```

2. Choose option 2: **Sync DEV → INSTALLED**

3. Confirm with `yes`

4. Restart your installed app - it will now show current data!

### Option B: Rebuild Installer with Current Data

1. Run the new build script:
   ```powershell
   BUILD_WITH_DATABASE.bat
   ```

2. Install the new version - it will include your current databases

### Option C: Manual Sync (Advanced)

Copy databases manually:

```powershell
# Source
C:\Dme_Solutions\Data\*.db

# Destination
C:\ProgramData\DMELogic\Data\*.db
```

## Going Forward

### When to Sync

Sync databases whenever you:
- Update patient data in dev
- Change insurance names
- Add/modify prescribers
- Create test orders
- Make any database changes in dev

### Recommended Workflow

1. **Make changes in dev** (run `python app.py`)
2. **Sync to installed app** (run `sync_databases.py`)
3. **Test installed app** (launch from Start Menu/Desktop)
4. **Build new installer** (if distributing to others)

### Database Locations Reference

| Environment | Location | Notes |
|-------------|----------|-------|
| **Development** | `C:\Dme_Solutions\Data` | Used when running `python app.py` |
| **Installed App** | `C:\ProgramData\DMELogic\Data` | Used by installed .exe |
| **Installer Bundle** | `installer_data\` | Databases included in installer |

## Why This Happened

This is a **classic PyInstaller deployment issue**:

1. **Development** uses relative paths or local folders
2. **Installed apps** need system-wide data folders (ProgramData)
3. **Without proper path handling**, they diverge

The fix ensures:
- ✅ Installed apps detect they're installed
- ✅ They read the correct path from `data_path.txt`
- ✅ All database operations use the same location

## Testing

After syncing, verify in the installed app:

- [ ] All patients visible (more than 2)
- [ ] Insurance names updated (EPACES → Medicaid)
- [ ] All prescribers present
- [ ] All orders visible
- [ ] Patient profiles show correct insurance

## Troubleshooting

### "Databases still don't match"

1. Check which database is being used:
   ```powershell
   python check_db_path.py
   ```

2. Verify sync worked:
   ```powershell
   python sync_databases.py
   # Choose option 1: Show status
   ```

3. Check file modification times in both locations

### "Sync utility shows 0 databases"

Development path might be different. Edit `sync_databases.py`:

```python
# Change this line:
DEV_DB_PATH = r"C:\Dme_Solutions\Data"

# To your actual path (check where python app.py stores databases)
```

### "Installed app still uses old data after sync"

1. Completely close the installed app (check Task Manager)
2. Run sync utility again
3. Launch installed app fresh

## Summary

**Problem**: Two separate databases (dev vs installed)  
**Solution**: Fixed path detection + created sync utility + updated build process  
**Action**: Run `sync_databases.py` → option 2 → restart installed app

Your installed app will now match your development environment! 🎉
