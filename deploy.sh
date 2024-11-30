#!/bin/bash

# Hebrew Transcription Project Deployment Script

# Exit on any error
set -e

# Ensure we're in the project root
cd "$(dirname "$0")"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created virtual environment"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Start the server
echo "Starting Hebrew Transcription Server..."
python server/server.py &

# Open the client in default browser
open client/index.html

echo "Deployment complete! Server is running."
