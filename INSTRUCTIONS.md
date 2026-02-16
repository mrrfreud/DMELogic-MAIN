# DMELogic Installer Build Instructions

## Quick Start

1. **Install Inno Setup** (if you haven't already):
   - Download from: https://jrsoftware.org/isdl.php
   - Install with default settings

2. **Run the build script**:
   - Double-click `BUILD_FULL_INSTALLER.bat`
   - Wait for the build to complete

3. **Your installer will be created at**:
   - `installer_output\DMELogic_Update_2.0.20.152.exe`

## What the Installer Does

✅ **Removes old shortcuts** (DME Manager Pro, etc.)
✅ **Installs to** `C:\Program Files\DMELogic\`
✅ **Creates data folder at** `C:\ProgramData\DMELogic\Data\`
✅ **Copies databases** to the data folder
✅ **Creates desktop shortcut**
✅ **Adds to Start Menu**
✅ **Provides clean uninstaller**

## Database Location

The installer places databases in:
```
C:\ProgramData\DMELogic\Data\
├── patients.db
├── orders.db
├── prescribers.db
└── inventory.db
```

This location is:
- ✅ User-writable (no admin rights needed)
- ✅ Shared across all users
- ✅ Preserved during uninstall
- ✅ Standard for application data on Windows

## Troubleshooting

### "Inno Setup NOT found"
- Download and install from: https://jrsoftware.org/isdl.php
- Make sure it's installed to the default location

### "PyInstaller build failed"
- Make sure virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Databases not loading
- Check `C:\ProgramData\DMELogic\Data\` folder exists
- Ensure databases are present in that folder
- Check Windows permissions (should be writable by users)
