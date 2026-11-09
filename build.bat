@echo off
echo ========================================================
echo Building JSD-CSV Standalone Executable with PyInstaller
echo ========================================================
echo.

pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean jsd-csv.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo SUCCESS: Standalone executable created at:
    echo   dist\jsd-csv.exe
    echo ========================================================
) else (
    echo.
    echo [ERROR] Build failed. Please check the logs above.
)
pause
