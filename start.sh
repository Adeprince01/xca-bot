#!/bin/bash

# Crypto Contract Monitor Startup Script

echo "Starting Crypto Contract Monitor..."

# Check if Python virtual environment exists
if [ ! -d "twitter-monitor-backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd twitter-monitor-backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "Using existing Python virtual environment"
fi

# Start the backend API in a separate terminal
echo "Starting backend API server..."
cd twitter-monitor-backend
start cmd /k "venv\Scripts\activate && python api.py"
cd ..

# Wait for the API to start
echo "Waiting for API to start..."
sleep 5

# Start the frontend
echo "Starting frontend..."
npm run dev 