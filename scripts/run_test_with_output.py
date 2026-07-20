"""
Run a test and capture its output to a file.
"""

import subprocess
import sys
from datetime import datetime


def main():
    test_file = "tests/test_hello_world.py"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_output_{timestamp}.log"

    print(f"Running test: {test_file}")
    print(f"Output will be saved to: {output_file}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Run the test and capture both stdout and stderr
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", test_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
            )

            # Write the output to file
            f.write(f"Command: python -m pytest -v {test_file}\n")
            f.write(f"Exit code: {result.returncode}\n")
            f.write("=" * 80 + "\n")
            f.write(result.stdout)

        print(f"Test completed. Exit code: {result.returncode}")
        print(f"Output saved to: {output_file}")

        # Display the output file location
        print("\nOutput file contents:")
        print("-" * 80)
        with open(output_file, encoding="utf-8") as f:
            print(f.read())

    except Exception as e:
        print(f"Error running test: {e!s}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
