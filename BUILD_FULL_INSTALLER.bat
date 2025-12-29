@echo off
echo ============================================
echo   DMELogic - Full Installer Builder
echo ============================================
echo.
echo This will:
echo 1. Build the executable with PyInstaller
echo 2. Create a Windows installer (.exe)
echo.
pause

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
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=reportlab ^
    app.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    pause
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
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo SUCCESS!
    echo ============================================
    echo.
    echo Your installer is ready:
    echo installer_output\DMELogic_Setup_2.0.20.66.exe
    echo.
    echo This installer will:
    echo - Remove old shortcuts
    echo - Install DMELogic with all dependencies
    echo - Create database folder at: C:\ProgramData\DMELogic\Data
    echo - Create desktop shortcut
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
pause
