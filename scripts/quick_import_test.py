import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing basic import...")
try:
    print("✅ containers import successful")
except Exception as e:
    print(f"❌ containers import failed: {e}")
    import traceback

    traceback.print_exc()

try:
    print("✅ images import successful")
except Exception as e:
    print(f"❌ images import failed: {e}")
    import traceback

    traceback.print_exc()
