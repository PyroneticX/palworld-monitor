"""
Helper functions for creating temporary files and directories in tests.
"""

import os
import tempfile
import shutil


def create_temp_data_dir():
    """Create a temporary data directory for test files.

    Returns:
        tuple: (temp_dir_path, data_dir_path) where data_dir_path is temp_dir_path/data
    """
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return temp_dir, data_dir


def cleanup_temp_dir(temp_dir):
    """Clean up a temporary directory.

    Args:
        temp_dir: Path to the temporary directory to remove
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_temp_file_with_content(content, suffix=".txt", mode="w"):
    """Create a temporary file with specified content.

    Args:
        content: Content to write to the file
        suffix: File suffix (default: '.txt')
        mode: File mode (default: 'w')

    Returns:
        str: Path to the created temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, delete=False)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name


def cleanup_temp_file(file_path):
    """Clean up a temporary file.

    Args:
        file_path: Path to the temporary file to remove
    """
    if os.path.exists(file_path):
        os.unlink(file_path)
