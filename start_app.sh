#!/bin/bash

echo "=================================================="
echo "     FinGuard - Fraud Detection System"
echo "=================================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed."
    exit 1
fi

# Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[1/5] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/5] Virtual environment exists."
fi

# Activate Virtual Environment
echo "[2/5] Activating virtual environment..."
source venv/bin/activate

# Install Dependencies
echo "[3/5] Checking dependencies..."
pip install -r requirements.txt

# Setup Database
echo "[4/5] Setting up database..."
python backend/setup_db.py

# Start Dashboard
echo "[5/5] Starting FinGuard Dashboard..."
echo ""
echo "The dashboard will open in your default browser."
echo "Press Ctrl+C to stop the server."
echo ""

streamlit run dashboard/app.py
