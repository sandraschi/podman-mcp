#!/usr/bin/env python3
"""
Test runner for Podman MCP container tools.

This script discovers and runs all tests in the tests directory.
"""

import os
import sys
import unittest


def run_tests():
    """Run all tests in the tests directory."""
    # Add the src directory to the Python path
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", pattern="test_*.py")

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
