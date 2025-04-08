@echo off
echo Starting Crypto Contract Monitor...

REM Check if Python virtual environment exists
if not exist "twitter-monitor-backend\venv" (
    echo Creating Python virtual environment...
    cd twitter-monitor-backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
) else (
    echo Using existing Python virtual environment
)

REM Start the backend API in a separate terminal
echo Starting backend API server...
start cmd /k "cd twitter-monitor-backend && call venv\Scripts\activate && python api.py"

REM Wait for the API to start
echo Waiting for API to start...
timeout /t 5 /nobreak > nul

REM Start the frontend
echo Starting frontend...
npm run dev 