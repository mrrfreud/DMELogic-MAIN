@echo off
echo ============================================
echo   DMELogic - Simple Build
echo ============================================
echo.

call .venv\Scripts\activate.bat

echo.
echo Building executable...
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

echo.
echo ============================================
echo Build Complete!
echo.
echo Run: dist\DMELogic\DMELogic.exe
echo.
echo Copy the entire dist\DMELogic folder to use
echo ============================================
pause
