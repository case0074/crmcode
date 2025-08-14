#!/usr/bin/env python3
"""
OpenPhone Scheduler for Linux Mint
Runs contacts export daily and messages export hourly
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from openphone import (
    request_openphone_export,
    request_openphone_messages_export,
    check_for_export_email,
    check_for_message_export_email,
    format_contacts
)
from mondaywrite import MondaySync

# Setup logging
def setup_logging():
    log_dir = project_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "scheduler.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_contacts_job():
    """Daily contacts export job (runs once in morning)"""
    logging.info("=== Starting Daily Contacts Export ===")
    
    try:
        # Request contacts export
        logging.info("Requesting contacts export from OpenPhone...")
        request_openphone_export()
        
        # Wait and check for email
        logging.info("Checking for export email...")
        success = check_for_export_email()
        
        if success:
            # Format contacts
            logging.info("Formatting contacts...")
            format_success = format_contacts()
            
            if format_success:
                # Run Monday.com sync
                logging.info("Running Monday.com sync...")
                sync = MondaySync()
                sync.sync_contacts()
                logging.info("Daily contacts job completed successfully")
                return True
            else:
                logging.error("Contacts formatting failed")
                return False
        else:
            logging.error("No export email received")
            return False
            
    except Exception as e:
        logging.error(f"Contacts job failed: {e}")
        return False

def run_messages_job():
    """Hourly messages export job"""
    logging.info("=== Starting Hourly Messages Export ===")
    
    try:
        # Request messages export
        logging.info("Requesting messages export from OpenPhone...")
        request_openphone_messages_export()
        
        # Wait and check for email
        logging.info("Checking for export email...")
        success = check_for_message_export_email()
        
        if success:
            logging.info("Hourly messages job completed successfully")
            return True
        else:
            logging.error("No messages export email received")
            return False
            
    except Exception as e:
        logging.error(f"Messages job failed: {e}")
        return False

def main():
    """Main entry point - determines which job to run based on arguments"""
    setup_logging()
    
    if len(sys.argv) < 2:
        print("Usage: python scheduler.py [contacts|messages]")
        sys.exit(1)
    
    job_type = sys.argv[1].lower()
    
    if job_type == "contacts":
        success = run_contacts_job()
    elif job_type == "messages":
        success = run_messages_job()
    else:
        print("Invalid job type. Use 'contacts' or 'messages'")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
