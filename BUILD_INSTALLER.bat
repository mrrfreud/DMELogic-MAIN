@echo off
echo ============================================
echo   DME Logic - Building Installer
echo ============================================
echo.
echo This will create a standalone executable...
echo.
pause

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Running PyInstaller...
echo.
pyinstaller --noconfirm --onedir --windowed --name="DMELogic" --add-data="installer_data/patients.db;dmelogic/db" --add-data="installer_data/orders.db;dmelogic/db" --add-data="assets;assets" --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --hidden-import=reportlab.pdfgen --hidden-import=reportlab.lib --collect-all=PyQt6 app.py


echo.
echo ============================================
echo.
echo Build Complete!
echo.
echo Your executable is in: dist\DMELogic\DMELogic.exe
echo.
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\DMELogic.lnk'); $Shortcut.TargetPath = '%cd%\dist\DMELogic\DMELogic.exe'; $Shortcut.WorkingDirectory = '%cd%\dist\DMELogic'; $Shortcut.Save()"
echo.
echo Desktop shortcut created!
echo.
echo ============================================
pause
