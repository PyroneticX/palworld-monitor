"""
Helper function to get the appropriate Python executable for launching test processes.
On Windows, uses pythonw.exe to avoid console windows.
Always uses the Python executable from the current environment (venv).
"""

import sys
import os


def get_python_executable():
    """Get the Python executable to use for launching test processes.

    Uses sys.executable to ensure we use the Python from the current environment
    (e.g., venv). On Windows, prefers pythonw.exe to avoid console windows.

    Returns:
        str: Path to Python executable from current environment
    """
    # Always use sys.executable to ensure we use the venv's Python
    python_exe = sys.executable

    if sys.platform == "win32":
        # Try pythonw.exe first (no console window)
        # Check in the same directory as python.exe (should be venv's Scripts directory)
        python_dir = os.path.dirname(python_exe)
        pythonw_exe = os.path.join(python_dir, "pythonw.exe")

        if os.path.exists(pythonw_exe):
            return pythonw_exe

        # Also try replacing python.exe with pythonw.exe in the path
        pythonw_exe_alt = python_exe.replace("python.exe", "pythonw.exe")
        if pythonw_exe_alt != python_exe and os.path.exists(pythonw_exe_alt):
            return pythonw_exe_alt

        # Fallback to python.exe if pythonw.exe not found
        # The CREATE_NO_WINDOW flag in process_manager should still prevent windows
        return python_exe
    else:
        return python_exe
