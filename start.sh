#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python."
    exit 1
fi

# Check Python version
python3 -c "import sys; exit(0) if sys.version_info >= (3, 11, 4) else exit(1)"
if [ $? -ne 0 ]; then
    echo "Python version 3.11.4 or higher is required. Please update Python."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if wkhtmltopdf is installed
if ! command -v wkhtmltopdf &> /dev/null; then
    echo "wkhtmltopdf is not installed. Please install wkhtmltopdf: https://wkhtmltopdf.org/downloads.html"
fi

# Run the Python script
echo "Running main.py..."
python3 python/main.py
