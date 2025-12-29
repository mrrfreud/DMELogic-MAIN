@echo off
echo ============================================
echo   DME Logic - Build Installer
echo ============================================
echo.

echo Installing PyInstaller...
pip install pyinstaller
echo.

echo Building executable...
python setup.py
echo.

echo ============================================
echo Build complete!
echo.
echo Check the dist\DMELogic folder for the executable
echo ============================================
pause
