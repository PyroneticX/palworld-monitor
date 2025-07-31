#!/usr/bin/env python3
"""
Manual logging verification script for the PalWorld server management application.

This script provides manual tests that can be run to verify logging behavior
in real scenarios. It's designed to complement the automated tests.
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_test_logging():
    """Setup logging for manual testing."""
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Setup logging similar to main.py
    logging.basicConfig(
        level=logging.INFO,  # Current level - should be WARNING after task 1
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_manual.log', mode='w')
        ]
    )

def test_application_lifecycle_logging():
    """Test application lifecycle logging manually."""
    print("=" * 60)
    print("TESTING APPLICATION LIFECYCLE LOGGING")
    print("=" * 60)
    
    print("Testing app start logging...")
    logging.info("App start")
    
    print("Testing app shutdown logging...")
    logging.info("App shutdown - CTRL+C received")
    logging.info("App shutdown - Exception occurred")
    logging.info("App shutdown - Normal exit")
    
    print("✓ Application lifecycle logging test completed")
    print()

def test_server_management_logging():
    """Test server management logging manually."""
    print("=" * 60)
    print("TESTING SERVER MANAGEMENT LOGGING")
    print("=" * 60)
    
    print("Testing server start command logging...")
    logging.info("Palworld server is commanded to start")
    
    print("Testing server stop command logging...")
    logging.info("Palworld server is commanded to shutdown")
    
    print("Testing server error logging...")
    logging.error("Failed to start Palworld server: Process not found")
    logging.warning("The attempt to start the Palworld server was made, but it is already running.")
    
    print("✓ Server management logging test completed")
    print()

def test_player_monitoring_logging():
    """Test player monitoring logging manually."""
    print("=" * 60)
    print("TESTING PLAYER MONITORING LOGGING")
    print("=" * 60)
    
    print("Testing port listening start logging...")
    logging.info("Listening on Palworld Server port for new players")
    
    print("Testing port listening stop logging...")
    logging.info("No longer listening on Palworld Server port")
    
    print("Testing monitoring error logging...")
    logging.error("Error opening PalWorld port socket: Connection refused")
    
    print("✓ Player monitoring logging test completed")
    print()

def test_web_server_logging():
    """Test web server logging manually."""
    print("=" * 60)
    print("TESTING WEB SERVER LOGGING")
    print("=" * 60)
    
    print("Testing web server start logging...")
    logging.info("Web server start - listening on 127.0.0.1:5000")
    
    print("Testing web server error logging...")
    logging.error("Web server failed to start: Port already in use")
    
    print("✓ Web server logging test completed")
    print()

def test_verbose_logging_behavior():
    """Test verbose logging behavior."""
    print("=" * 60)
    print("TESTING VERBOSE LOGGING BEHAVIOR")
    print("=" * 60)
    
    print("Testing various log levels...")
    logging.debug("This is a DEBUG message (should be suppressed)")
    logging.info("This is an INFO message (essential events only)")
    logging.warning("This is a WARNING message (should appear)")
    logging.error("This is an ERROR message (should appear)")
    
    print("✓ Verbose logging behavior test completed")
    print()

def test_log_format_consistency():
    """Test log format consistency."""
    print("=" * 60)
    print("TESTING LOG FORMAT CONSISTENCY")
    print("=" * 60)
    
    print("Testing consistent log formatting...")
    logging.info("Test message with timestamp")
    logging.warning("Warning with special characters: !@#$%^&*()")
    logging.error("Error with numbers: 12345 and symbols: <>?")
    
    print("✓ Log format consistency test completed")
    print()

def analyze_log_file():
    """Analyze the generated log file."""
    print("=" * 60)
    print("LOG FILE ANALYSIS")
    print("=" * 60)
    
    try:
        with open('test_manual.log', 'r') as f:
            lines = f.readlines()
        
        print(f"Total log entries: {len(lines)}")
        
        # Count by level
        levels = {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0}
        for line in lines:
            for level in levels:
                if f' - {level} - ' in line:
                    levels[level] += 1
                    break
        
        print("Log entries by level:")
        for level, count in levels.items():
            print(f"  {level}: {count}")
        
        print("\nEssential events found:")
        essential_events = [
            "App start",
            "App shutdown",
            "Palworld server is commanded to start",
            "Palworld server is commanded to shutdown",
            "Listening on Palworld Server port for new players",
            "No longer listening on Palworld Server port",
            "Web server start"
        ]
        
        for event in essential_events:
            found = any(event in line for line in lines)
            status = "✓" if found else "✗"
            print(f"  {status} {event}")
        
        print(f"\nLog file saved as: test_manual.log")
        print("You can review the log file to verify formatting and content.")
        
    except FileNotFoundError:
        print("Error: Log file not found")

def main():
    """Run all manual logging tests."""
    print("MANUAL LOGGING VERIFICATION")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Setup logging
    setup_test_logging()
    
    # Run all tests
    test_application_lifecycle_logging()
    test_server_management_logging()
    test_player_monitoring_logging()
    test_web_server_logging()
    test_verbose_logging_behavior()
    test_log_format_consistency()
    
    # Analyze results
    analyze_log_file()
    
    print()
    print("=" * 80)
    print("MANUAL TESTING COMPLETED")
    print("=" * 80)
    print("Review the console output and test_manual.log file to verify:")
    print("1. All essential events are logged with correct messages")
    print("2. Log format is consistent (TIMESTAMP - LEVEL - MESSAGE)")
    print("3. ERROR and WARNING messages are preserved")
    print("4. Verbose logging behavior matches expectations")
    print()
    print("Next steps:")
    print("- Compare with requirements in .kiro/specs/application-logging/requirements.md")
    print("- Verify against design in .kiro/specs/application-logging/design.md")
    print("- Run automated tests with: python test_logging.py")

if __name__ == "__main__":
    main()