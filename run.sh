#!/usr/bin/env bash

set -e

# --- Move to script directory ---
cd "$(dirname "$0")"

# --- Check venv ---
if [ ! -f ".venv/bin/activate" ]; then
    echo "[ERROR] .venv not found. Please setup environment first."
    exit 1
fi

# --- Activate venv ---
source .venv/bin/activate

# --- Show installed packages ---
pip list

# --- Start servers in background ---
echo "Starting Salesforce Server..."
python -m salesforce_server.main &

echo "Starting Storage Server..."
python -m storage_server.main &

echo "=================================================="
echo "  [Salesforce Server: http://localhost:8000]"
echo "  [Storage Server:    http://localhost:8080]"
echo "  * Press Ctrl+C to stop all servers."
echo "=================================================="

# --- Keep script alive ---
wait
