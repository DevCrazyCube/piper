#!/bin/bash

# Change to the directory where this script is located
cd "$(dirname "$0")"

set -e  # Exit on first error

echo "========================================"
echo "Starting Pipeline..."
echo "========================================"

# Step 1: Setup
echo ""
echo "[1/7] Running: make setup"
make setup
if [ $? -ne 0 ]; then
    echo "ERROR: make setup failed with exit code $?"
    exit 1
fi
echo "[✓] Step 1 completed successfully"

# Step 2: Migrate
echo ""
echo "[2/7] Running: make migrate"
make migrate
if [ $? -ne 0 ]; then
    echo "ERROR: make migrate failed with exit code $?"
    exit 1
fi
echo "[✓] Step 2 completed successfully"

# Step 3: Bootstrap
echo ""
echo "[3/7] Running: make bootstrap"
make bootstrap
if [ $? -ne 0 ]; then
    echo "ERROR: make bootstrap failed with exit code $?"
    exit 1
fi
echo "[✓] Step 3 completed successfully"

# Step 4: Ingest
echo ""
echo "[4/7] Running: make ingest"
make ingest
if [ $? -ne 0 ]; then
    echo "ERROR: make ingest failed with exit code $?"
    exit 1
fi
echo "[✓] Step 4 completed successfully"

# Step 5: Curate
echo ""
echo "[5/7] Running: make curate"
make curate
if [ $? -ne 0 ]; then
    echo "ERROR: make curate failed with exit code $?"
    exit 1
fi
echo "[✓] Step 5 completed successfully"

# Step 6: Analyse
echo ""
echo "[6/7] Running: make analyse"
make analyse
if [ $? -ne 0 ]; then
    echo "ERROR: make analyse failed with exit code $?"
    exit 1
fi
echo "[✓] Step 6 completed successfully"

# Step 7: Start application
echo ""
echo "[7/7] Running: make up"
make up
if [ $? -ne 0 ]; then
    echo "ERROR: make up failed with exit code $?"
    exit 1
fi
echo "[✓] Step 7 completed successfully"

echo ""
echo "========================================"
echo "Pipeline is running!"
echo "Open http://localhost:5173 in your browser"
echo "========================================"
