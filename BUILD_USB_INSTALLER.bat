@echo off
echo ============================================
echo   DMELogic - USB Installer Builder
echo   Creates plug-and-play flash drive install
echo ============================================
echo.
echo This will create a complete installer for USB deployment.
echo Users only need to run the installer - no technical knowledge required.
echo.
pause

echo.
echo Step 1: Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Step 2: Building executable with PyInstaller...
echo          (This may take several minutes)
echo.

pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name=DMELogic ^
    --icon=assets\DMELogic Icon.ico ^
    --add-data="assets;assets" ^
    --add-data="theme;theme" ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtPrintSupport ^
    --hidden-import=reportlab ^
    --hidden-import=reportlab.lib ^
    --hidden-import=reportlab.pdfgen ^
    --hidden-import=reportlab.platypus ^
    --hidden-import=openpyxl ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=fitz ^
    --hidden-import=pytesseract ^
    --collect-all=reportlab ^
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
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_usb.iss
    
    if errorlevel 1 (
        echo.
        echo ERROR: Installer build failed!
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo   BUILD SUCCESSFUL!
    echo ============================================
    echo.
    echo Installer created in: installer_output\
    echo.
    echo To deploy via USB:
    echo 1. Copy the installer .exe to a USB drive
    echo 2. On target PC, run the installer
    echo 3. First launch will prompt user for server folders
    echo.
) else (
    echo.
    echo WARNING: Inno Setup 6 not found!
    echo.
    echo Please install Inno Setup from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo The executable is ready in: dist\DMELogic\
    echo You can manually copy this folder to deploy.
)

pause
