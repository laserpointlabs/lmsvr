#!/bin/bash
# Quick activation script for this project
# Usage: source activate.sh

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
    echo "  Python: $(which python)"
    echo "  Version: $(python --version)"
else
    echo "✗ Error: venv/bin/activate not found"
    echo "  Run: python3 -m venv venv"
    return 1
fi




