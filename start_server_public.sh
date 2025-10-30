#!/bin/bash
# =========================================================================
# Quick Start Script - Run Flask App Publicly
# =========================================================================

# Set terminal title
echo -ne "\033]0;ReviewKit Public Server\007"

# Set color (cyan text)
echo -e "\033[1;36m"

echo ""
echo "  ===================================================================="
echo "             ReviewKit - Public Server Mode"
echo "  ===================================================================="
echo ""

# Reset color
echo -e "\033[0m"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "  [WARNING] Virtual environment not found. Using system Python."
    echo ""
fi

# Change to app directory
cd app

# Get public IP
echo "  Starting server on all network interfaces..."
echo ""

# Run Flask with public access
python app.py --host 0.0.0.0 --port 8000

# Pause equivalent
read -p "Press Enter to continue..."

