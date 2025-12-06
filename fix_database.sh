#!/bin/bash
# Fix database permissions and initialize

set -e

echo "=== Fixing Database ==="
echo ""

# Remove root-owned database file if it exists
if [ -f "data/lmapi.db" ]; then
    echo "Removing root-owned database file..."
    sudo rm -f data/lmapi.db || rm -f data/lmapi.db
fi

# Ensure data directory exists and has correct permissions
mkdir -p data
chmod 755 data

# Initialize database
echo "Initializing database..."
source venv/bin/activate
python3 -c "from api_gateway.database import init_db; init_db()"

echo ""
echo "✓ Database initialized successfully!"
echo ""
echo "Test it:"
echo "  python3 cli/cli.py list-customers"














