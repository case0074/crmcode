#!/bin/bash

# OpenPhone Scheduler Cron Setup Script
# This script sets up cron jobs to run contacts daily and messages hourly

echo "Setting up OpenPhone Scheduler cron jobs..."

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)
SCHEDULER_SCRIPT="$SCRIPT_DIR/scheduler.py"

echo "Script directory: $SCRIPT_DIR"
echo "Python path: $PYTHON_PATH"
echo "Scheduler script: $SCHEDULER_SCRIPT"

# Make the scheduler script executable
chmod +x "$SCHEDULER_SCRIPT"

# Create a temporary file for the new crontab
TEMP_CRON=$(mktemp)

# Get current crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "" > "$TEMP_CRON"

# Add our cron jobs
echo "" >> "$TEMP_CRON"
echo "# OpenPhone Scheduler Jobs" >> "$TEMP_CRON"
echo "# Daily contacts export at 8:00 AM" >> "$TEMP_CRON"
echo "0 8 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCHEDULER_SCRIPT contacts >> $SCRIPT_DIR/logs/cron.log 2>&1" >> "$TEMP_CRON"
echo "" >> "$TEMP_CRON"
echo "# Hourly messages export" >> "$TEMP_CRON"
echo "0 * * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCHEDULER_SCRIPT messages >> $SCRIPT_DIR/logs/cron.log 2>&1" >> "$TEMP_CRON"

# Install the new crontab
crontab "$TEMP_CRON"

# Clean up
rm "$TEMP_CRON"

echo "Cron jobs installed successfully!"
echo ""
echo "Current crontab:"
crontab -l
echo ""
echo "Jobs scheduled:"
echo "- Contacts export: Daily at 8:00 AM"
echo "- Messages export: Every hour"
echo ""
echo "Logs will be written to:"
echo "- $SCRIPT_DIR/logs/scheduler.log (application logs)"
echo "- $SCRIPT_DIR/logs/cron.log (cron execution logs)"
echo ""
echo "To test manually:"
echo "  python3 $SCHEDULER_SCRIPT contacts"
echo "  python3 $SCHEDULER_SCRIPT messages"
