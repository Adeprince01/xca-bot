@echo off
REM Setup script for XCA-Bot environment (Windows)

REM Check if .env exists
if exist .env (
    echo Warning: .env file already exists.
    set /p overwrite="Do you want to overwrite it? (y/n): "
    if /i not "%overwrite%"=="y" (
        echo Setup aborted. Your existing .env file was not modified.
        exit /b 0
    )
)

REM Copy the example env file
copy .env.example .env

echo .env file created from template.
echo Please edit the .env file to add your API keys and other configuration values.
echo.
echo After editing, you can run the bot with: python main.py
echo.
echo Note: The .env file contains sensitive information and is excluded from Git commits.
pause 