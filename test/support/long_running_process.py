"""
Test helper script to simulate a long-running process.

This script is executed directly by the tests as a subprocess, not imported as a module.
It runs silently without output to avoid console windows on Windows.
"""
import time
import sys
import os

if __name__ == '__main__':
    # Suppress output to avoid console windows (stdout/stderr are redirected to DEVNULL anyway)
    # but this ensures no accidental output
    if sys.platform == 'win32':
        # On Windows, ensure we don't try to write to console
        try:
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
        except Exception:
            pass
    
    for i in range(10):
        # Output suppressed - process runs silently
        time.sleep(1)

