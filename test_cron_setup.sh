#!/bin/bash

# Quick test script for OpenPhone Scheduler
echo "=== Testing OpenPhone Scheduler Setup ==="
echo "Date: $(date)"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Test 1: Check if setup_cron.sh was run
echo "1. Checking if cron jobs are installed:"
if crontab -l 2>/dev/null | grep -q "OpenPhone Scheduler"; then
    echo "   ✓ OpenPhone cron jobs found"
    crontab -l | grep -A 5 "OpenPhone Scheduler"
else
    echo "   ✗ OpenPhone cron jobs NOT found"
    echo "   Run: bash setup_cron.sh"
fi
echo ""

# Test 2: Manual test of scheduler
echo "2. Testing scheduler script manually:"
SCHEDULER_SCRIPT="$SCRIPT_DIR/scheduler.py"

if [ -f "$SCHEDULER_SCRIPT" ]; then
    echo "   Testing with 'contacts' argument..."
    python3 "$SCHEDULER_SCRIPT" contacts
    echo "   Exit code: $?"
else
    echo "   ✗ Scheduler script not found"
fi
echo ""

# Test 3: Check if logs directory exists
echo "3. Checking logs directory:"
LOGS_DIR="$SCRIPT_DIR/logs"
if [ -d "$LOGS_DIR" ]; then
    echo "   ✓ Logs directory exists"
    echo "   Contents:"
    ls -la "$LOGS_DIR"
else
    echo "   ✗ Logs directory missing"
    echo "   Creating logs directory..."
    mkdir -p "$LOGS_DIR"
fi
echo ""

echo "=== Test Complete ==="
