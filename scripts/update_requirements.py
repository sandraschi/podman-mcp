"""
Script to update FastMCP to the latest version.
"""

import subprocess
import sys


def update_fastmcp():
    """Update FastMCP to the latest version."""
    print("Updating FastMCP to the latest version...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "fastmcp"])
        print("Successfully updated FastMCP!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error updating FastMCP: {e}")
        return False


if __name__ == "__main__":
    update_fastmcp()
