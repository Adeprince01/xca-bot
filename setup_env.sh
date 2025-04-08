#!/bin/bash
# Setup script for XCA-Bot environment

# Check if .env exists
if [ -f .env ]; then
    echo "Warning: .env file already exists."
    read -p "Do you want to overwrite it? (y/n): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "Setup aborted. Your existing .env file was not modified."
        exit 0
    fi
fi

# Copy the example env file
cp .env.example .env

echo ".env file created from template."
echo "Please edit the .env file to add your API keys and other configuration values."
echo ""
echo "After editing, you can run the bot with: python main.py"
echo ""
echo "Note: The .env file contains sensitive information and is excluded from Git commits." 