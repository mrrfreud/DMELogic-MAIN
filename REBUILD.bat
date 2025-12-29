@echo off
echo ============================================
echo   Quick Rebuild - DMELogic
echo ============================================
echo.
echo This will rebuild with latest changes...
echo.

call .venv\Scripts\activate.bat

echo Cleaning old build files...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q *.spec 2>nul

echo Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo Building executable with fresh source...
pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name=DMELogic ^
    --icon=assets\DMELogic-Logo.ico ^
    --add-data="assets;assets" ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=reportlab ^
    app.py

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Checking for Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Building installer...
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_script.iss
    
    if errorlevel 1 (
        echo Installer build failed!
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo SUCCESS! Installer ready at:
    echo installer_output\DMELogic_Setup_2.0.20.66.exe
    echo ============================================
) else (
    echo.
    echo Inno Setup not found. Executable ready at:
    echo dist\DMELogic\DMELogic.exe
)

pause
