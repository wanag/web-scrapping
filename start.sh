#!/bin/bash

# Startup script for Book Scraper & Reader System

echo "========================================"
echo "Book Scraper & Reader System"
echo "Phase 1: Core Functionality"
echo "========================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Error: Frontend dependencies not installed!"
    echo "Please run: cd frontend && npm install"
    exit 1
fi

# Start backend
echo "Starting backend server..."
source venv/bin/activate
python -m backend.app > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "Error: Backend failed to start. Check backend.log for details."
    exit 1
fi

echo "✓ Backend started on http://localhost:8001"
echo "  API docs: http://localhost:8001/docs"
echo ""

# Start frontend
echo "Starting frontend server..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"
sleep 3

# Check if frontend started successfully
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "Error: Frontend failed to start. Check frontend.log for details."
    kill $BACKEND_PID
    exit 1
fi

echo "✓ Frontend started on http://localhost:7998"
echo ""
echo "========================================"
echo "Application is ready!"
echo "========================================"
echo ""
echo "Access the application at: http://localhost:7998"
echo "Default PIN: 1234"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for user to stop
wait
