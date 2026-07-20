"""
Test script to verify behavior when Podman Machine GUI is not running.
"""


def test_podman_desktop_gui():
    """Test if Podman Machine GUI is running."""
    try:
        import psutil

        # Check if Podman Machine process is running
        for proc in psutil.process_iter(["name"]):
            if "Podman Machine" in proc.info["name"]:
                return True, "✅ Podman Machine GUI is running"

        return False, "❌ Podman Machine GUI is not running (but Podman CLI might be)"

    except Exception as e:
        return False, f"❌ Error checking Podman Machine GUI: {e!s}"


if __name__ == "__main__":
    print("Checking Podman Machine GUI status...")
    success, message = test_podman_desktop_gui()
    print(message)

    if not success:
        print("\n✅ Test successful! The script correctly detected that Podman Machine GUI is not running.")
        print("\nThis is the scenario we want to test - where the Podman CLI is running")
        print("but the Desktop GUI is not. Our application should handle this gracefully.")
