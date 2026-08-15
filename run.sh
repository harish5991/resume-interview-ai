#!/usr/bin/env bash
# Resume Interview AI — 1-Click Startup Script (Mac / Linux)

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================="
echo " Starting Resume Interview AI..."
echo "=================================================="

# Check python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python is not installed. Please install Python 3.10+."
    exit 1
fi

$PYTHON_CMD run.py
