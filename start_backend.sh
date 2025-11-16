#!/bin/bash

# Script to start the backend server

echo "📚 Book Scraper & Reader - Backend Setup"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the server
echo ""
echo "Starting FastAPI server..."
echo ""
python -m backend.app
