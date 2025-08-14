#!/bin/bash

# Debug script for OpenPhone Scheduler cron jobs
echo "=== OpenPhone Scheduler Cron Debug ==="
echo "Date: $(date)"
echo ""

# Check if cron service is running
echo "1. Checking cron service status:"
if systemctl is-active --quiet cron; then
    echo "   ✓ Cron service is running"
else
    echo "   ✗ Cron service is NOT running"
    echo "   Try: sudo systemctl start cron"
fi
echo ""

# Check current crontab
echo "2. Current crontab entries:"
crontab -l 2>/dev/null || echo "   No crontab found"
echo ""

# Check if scheduler script exists and is executable
echo "3. Checking scheduler script:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEDULER_SCRIPT="$SCRIPT_DIR/scheduler.py"

if [ -f "$SCHEDULER_SCRIPT" ]; then
    echo "   ✓ Scheduler script exists: $SCHEDULER_SCRIPT"
    if [ -x "$SCHEDULER_SCRIPT" ]; then
        echo "   ✓ Scheduler script is executable"
    else
        echo "   ✗ Scheduler script is NOT executable"
        echo "   Try: chmod +x $SCHEDULER_SCRIPT"
    fi
else
    echo "   ✗ Scheduler script NOT found: $SCHEDULER_SCRIPT"
fi
echo ""

# Check Python path
echo "4. Checking Python installation:"
PYTHON_PATH=$(which python3)
if [ -n "$PYTHON_PATH" ]; then
    echo "   ✓ Python3 found: $PYTHON_PATH"
    echo "   Python version: $(python3 --version)"
else
    echo "   ✗ Python3 NOT found"
fi
echo ""

# Check logs directory
echo "5. Checking logs directory:"
LOGS_DIR="$SCRIPT_DIR/logs"
if [ -d "$LOGS_DIR" ]; then
    echo "   ✓ Logs directory exists: $LOGS_DIR"
    echo "   Log files:"
    ls -la "$LOGS_DIR" 2>/dev/null || echo "   (empty or no access)"
else
    echo "   ✗ Logs directory NOT found: $LOGS_DIR"
    echo "   Try: mkdir -p $LOGS_DIR"
fi
echo ""

# Check if we can write to logs
echo "6. Testing log file write access:"
TEST_LOG="$LOGS_DIR/test.log"
if touch "$TEST_LOG" 2>/dev/null; then
    echo "   ✓ Can write to logs directory"
    rm "$TEST_LOG" 2>/dev/null
else
    echo "   ✗ Cannot write to logs directory"
    echo "   Check permissions: ls -la $LOGS_DIR"
fi
echo ""

# Test manual execution
echo "7. Testing manual script execution:"
echo "   Testing scheduler script with 'contacts' argument..."
if timeout 30s python3 "$SCHEDULER_SCRIPT" contacts > "$LOGS_DIR/test_execution.log" 2>&1; then
    echo "   ✓ Script executed successfully"
    echo "   Check: $LOGS_DIR/test_execution.log"
else
    echo "   ✗ Script execution failed or timed out"
    echo "   Check: $LOGS_DIR/test_execution.log"
fi
echo ""

# Check cron logs
echo "8. Checking system cron logs:"
if [ -f "/var/log/syslog" ]; then
    echo "   Recent cron entries from syslog:"
    grep -i cron /var/log/syslog | tail -5
elif [ -f "/var/log/cron" ]; then
    echo "   Recent cron entries from cron log:"
    tail -5 /var/log/cron
else
    echo "   No cron log files found"
fi
echo ""

echo "=== Debug Complete ==="
echo ""
echo "If cron jobs still aren't running, try:"
echo "1. sudo systemctl restart cron"
echo "2. Check if your user has cron permissions"
echo "3. Verify the script paths are correct"
echo "4. Test manual execution first"
