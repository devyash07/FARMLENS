#!/bin/bash

echo "🔄 Restarting FarmLens Backend Server..."

# Find and kill existing uvicorn process on port 8001
echo "📍 Stopping existing server..."
PID=$(lsof -ti:8001)
if [ ! -z "$PID" ]; then
    kill $PID
    echo "✅ Stopped server (PID: $PID)"
    sleep 2
else
    echo "ℹ️  No server running on port 8001"
fi

# Activate Python 3.12 virtual environment
echo "🐍 Activating Python 3.12 virtual environment..."
if [ -d "venv312" ]; then
    source venv312/bin/activate
    echo "✅ Using Python $(python --version)"
else
    echo "⚠️  venv312 not found, using default Python"
fi

# Start the server
echo "🚀 Starting server on port 8001..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
