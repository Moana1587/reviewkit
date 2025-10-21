@echo off
REM =========================================================================
REM Quick Start Script - Run Flask App Publicly
REM =========================================================================

title ReviewKit Public Server
color 0B

echo.
echo  ====================================================================
echo               ReviewKit - Public Server Mode
echo  ====================================================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo  [WARNING] Virtual environment not found. Using system Python.
    echo.
)

REM Change to app directory
cd app

REM Get public IP
echo  Starting server on all network interfaces...
echo.

REM Run Flask with public access
python app.py --host 0.0.0.0 --port 8000

pause

