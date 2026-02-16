"""
DME Logic Installer Setup
Creates a Windows executable and installer using PyInstaller
"""
import sys
import os
from pathlib import Path

from dmelogic.version import APP_VERSION as DM_APP_VERSION

# Build configuration
APP_NAME = "DME Logic"
APP_VERSION = DM_APP_VERSION
APP_AUTHOR = "DME Logic"
APP_DESCRIPTION = "DME Order Management System"

# PyInstaller spec file content
SPEC_CONTENT = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('dmelogic', 'dmelogic'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sqlite3',
        'reportlab',
        'PIL',
        'pandas',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DMELogic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DMELogic',
)
"""

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_path = Path('DMELogic.spec')
    with open(spec_path, 'w') as f:
        f.write(SPEC_CONTENT)
    print(f"✅ Created {spec_path}")
    return spec_path

def check_dependencies():
    """Check if required tools are installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        os.system('pip install pyinstaller')
    
    # Check for NSIS (for installer creation)
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    
    nsis_found = any(os.path.exists(p) for p in nsis_paths)
    if nsis_found:
        print("✅ NSIS found (optional - for creating installer)")
    else:
        print("ℹ️  NSIS not found (optional)")
        print("   Download from: https://nsis.sourceforge.io/Download")

def build_executable():
    """Build executable using PyInstaller"""
    print("\n🔨 Building executable...")
    
    spec_file = create_spec_file()
    
    # Run PyInstaller
    cmd = f'pyinstaller --clean --noconfirm {spec_file}'
    print(f"\nRunning: {cmd}")
    result = os.system(cmd)
    
    if result == 0:
        print("\n✅ Build successful!")
        print(f"\nExecutable location: dist\\DMELogic\\DMELogic.exe")
        return True
    else:
        print("\n❌ Build failed!")
        return False

def create_nsis_script():
    """Create NSIS installer script"""
    nsis_script = f"""
; DME Logic Installer Script
!define APP_NAME "DME Logic"
!define APP_VERSION "{APP_VERSION}"
!define PUBLISHER "{APP_AUTHOR}"
!define APP_EXE "DMELogic.exe"

Name "${{APP_NAME}}"
OutFile "DMELogic-Setup-${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES64\\DME Logic"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy all files from dist\\DMELogic
    File /r "dist\\DMELogic\\*.*"
    
    ; Create desktop shortcut
    CreateShortcut "$DESKTOP\\DME Logic.lnk" "$INSTDIR\\${{APP_EXE}}"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\\DME Logic"
    CreateShortcut "$SMPROGRAMS\\DME Logic\\DME Logic.lnk" "$INSTDIR\\${{APP_EXE}}"
    CreateShortcut "$SMPROGRAMS\\DME Logic\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DMELogic" \\
                     "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DMELogic" \\
                     "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DMELogic" \\
                     "Publisher" "${{PUBLISHER}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DMELogic" \\
                     "DisplayVersion" "${{APP_VERSION}}"
SectionEnd

Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\\DME Logic.lnk"
    RMDir /r "$SMPROGRAMS\\DME Logic"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\DMELogic"
SectionEnd
"""
    
    nsis_path = Path('installer.nsi')
    with open(nsis_path, 'w') as f:
        f.write(nsis_script)
    print(f"✅ Created {nsis_path}")
    return nsis_path

def create_installer():
    """Create Windows installer using NSIS"""
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]
    
    nsis_exe = None
    for path in nsis_paths:
        if os.path.exists(path):
            nsis_exe = path
            break
    
    if not nsis_exe:
        print("\n⚠️  NSIS not found. Skipping installer creation.")
        print("   You can manually create an installer or distribute the dist\\DMELogic folder.")
        return False
    
    print("\n📦 Creating Windows installer...")
    nsis_script = create_nsis_script()
    
    cmd = f'"{nsis_exe}" {nsis_script}'
    print(f"\nRunning: {cmd}")
    result = os.system(cmd)
    
    if result == 0:
        print(f"\n✅ Installer created: DMELogic-Setup-{APP_VERSION}.exe")
        return True
    else:
        print("\n❌ Installer creation failed!")
        return False

def main():
    print("=" * 60)
    print(f"  {APP_NAME} Installer Builder")
    print(f"  Version {APP_VERSION}")
    print("=" * 60)
    
    # Check dependencies
    print("\n📋 Checking dependencies...")
    check_dependencies()
    
    # Build executable
    if not build_executable():
        return
    
    # Create installer
    print("\n" + "=" * 60)
    create_installer()
    
    print("\n" + "=" * 60)
    print("✅ Build complete!")
    print("\nFiles created:")
    print("  • dist\\DMELogic\\DMELogic.exe - Standalone executable")
    print("  • DMELogic-Setup-{}.exe - Windows installer (if NSIS available)".format(APP_VERSION))
    print("\n💡 Distribution options:")
    print("  1. Distribute the entire dist\\DMELogic folder")
    print("  2. Use the installer .exe file (if created)")
    print("=" * 60)

if __name__ == "__main__":
    main()
