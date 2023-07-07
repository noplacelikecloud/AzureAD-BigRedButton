@echo off

REM Check if Python is installed
python3 --version 2>NUL
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python.
    exit /b
)

REM Check Python version
python3 -c "import sys; exit(0) if sys.version_info >= (3, 11, 4) else exit(1)"
if %errorlevel% neq 0 (
    echo Python version 3.11.4 or higher is required. Please update Python.
    pause
    exit /b
)

REM Check if wkhtmltopdf is installed
wkhtmltopdf --version 2>NUL
if %errorlevel% neq 0 (
    echo wkhtmltopdf is not installed. Please install wkhtmltopdf: https://wkhtmltopdf.org/downloads.html
)

REM Run the Python script
echo Running main.py...
python3 python/main.py

pause
exit /b
