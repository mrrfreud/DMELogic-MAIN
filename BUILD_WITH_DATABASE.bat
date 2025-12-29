@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   DMELogic - Full Installer Builder
echo   WITH DATABASE SYNC + AUTO-VERSION
echo ============================================
echo.

REM Use PowerShell script to increment version
for /f "delims=" %%v in ('powershell -NoProfile -ExecutionPolicy Bypass -File "increment_version.ps1"') do (
    set NEW_VERSION=%%v
)

echo Building version: %NEW_VERSION%
echo.

echo Step 0: Copying current databases to installer...
echo.

REM Create installer data directory
if not exist "installer_data" mkdir installer_data

REM Copy databases from development location
set DEV_DB=C:\FaxManagerData\Data
set INSTALLER_DB=installer_data

if exist "%DEV_DB%" (
    echo Copying databases from: %DEV_DB%
    xcopy "%DEV_DB%\*.db" "%INSTALLER_DB%\" /Y /I /Q
    echo Databases copied to installer_data\
) else (
    echo WARNING: Development database path not found: %DEV_DB%
    echo The installer will create fresh databases.
)

echo.
echo Step 1: Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Step 2: Building executable with PyInstaller...
echo.
pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name=DMELogic ^
    --add-data="assets;assets" ^
    --add-data="installer_data;installer_data" ^
    --add-data="dmelogic;dmelogic" ^
    --add-data="app_legacy.py;." ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=reportlab ^
    --hidden-import=app_legacy ^
    --hidden-import=dmelogic ^
    --hidden-import=dmelogic.ui ^
    --hidden-import=dmelogic.ui.main_window ^
    --hidden-import=dmelogic.services ^
    --hidden-import=dmelogic.db ^
    --paths="." ^
    app.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    exit /b 1
)

echo.
echo Step 3: Checking for Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Found Inno Setup!
    echo.
    echo Step 4: Building Windows installer...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_script.iss
    
    if errorlevel 1 (
        echo.
        echo ERROR: Installer build failed!
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo SUCCESS! Build %NEW_VERSION% Complete
    echo ============================================
    echo.
    echo Installer: installer_output\DMELogic_Setup_%NEW_VERSION%.exe
    echo.
    echo Previous builds preserved in installer_output\
    echo.
) else (
    echo.
    echo Inno Setup NOT found!
    echo.
    echo Your executable is ready at: dist\DMELogic\DMELogic.exe
    echo.
    echo To create a Windows installer:
    echo 1. Download Inno Setup: https://jrsoftware.org/isdl.php
    echo 2. Install it
    echo 3. Run this script again
    echo.
)

echo ============================================
endlocal
