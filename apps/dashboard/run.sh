#!/bin/bash

# Quick start script for Mental Health Dashboard

echo "🚀 Starting Mental Health Dashboard..."

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo "❌ Error: .env file not found in root directory"
    echo "Please copy .env.example to .env and configure database credentials"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "📍 Detected Python $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo "⚠️  Python 3.13 detected. Using Python 3.12 or 3.11 recommended for better compatibility."
    echo "   Attempting to use python3.12 or python3.11..."
    
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    else
        echo "   No Python 3.12 or 3.11 found. Continuing with Python 3.13 (may have issues)..."
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python3"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Load environment variables
export $(cat ../../.env | grep -v '^#' | xargs)

# Run Streamlit
echo "✅ Dashboard starting at http://localhost:8501"
echo "Press Ctrl+C to stop"
streamlit run app.py

