"""
Podman Watchdog Service

A cross-platform service that monitors the Podman CLI and automatically attempts recovery
if it becomes unresponsive or crashes.
"""

import asyncio
import logging
import platform
import subprocess
from typing import Any

import podman
from podman.errors import PodmanException

logger = logging.getLogger(__name__)


class PodmanWatchdog:
    def __init__(self, check_interval: int = 30, max_retries: int = 3):
        """
        Initialize the Podman watchdog service.

        Args:
            check_interval: Seconds between health checks
            max_retries: Number of retry attempts before giving up
        """
        self.check_interval = check_interval
        self.max_retries = max_retries
        self.retry_count = 0
        self.is_windows = platform.system().lower() == "windows"
        self.podman_client = self._get_podman_client()

    def _get_podman_client(self) -> podman.PodmanClient:
        """Get a Podman client with error handling."""
        try:
            return podman.from_env()
        except PodmanException as e:
            logger.error(f"Failed to initialize Podman client: {e}")
            raise

    async def check_podman_health(self) -> dict[str, Any]:
        """Check if Podman CLI is healthy."""
        try:
            # Test basic API connectivity
            self.podman_client.ping()

            # Test container operations
            self.podman_client.containers.list(limit=1)

            self.retry_count = 0  # Reset retry counter on success
            return {"status": "healthy", "message": "Podman CLI is responding normally"}

        except Exception as e:
            self.retry_count += 1
            logger.warning(f"Podman health check failed (attempt {self.retry_count}/{self.max_retries}): {e}")

            if self.retry_count >= self.max_retries:
                return {
                    "status": "unhealthy",
                    "message": f"Podman CLI is not responding after {self.max_retries} attempts",
                    "error": str(e),
                }
            return {
                "status": "degraded",
                "message": f"Podman CLI check failed (attempt {self.retry_count}/{self.max_retries})",
                "error": str(e),
            }

    async def restart_podman_service(self) -> dict[str, Any]:
        """Attempt to restart the Podman service."""
        try:
            if self.is_windows:
                # Windows service restart
                subprocess.run(["net", "stop", "podman"], check=True, capture_output=True, text=True)  # noqa: S607
                subprocess.run(["net", "start", "podman"], check=True, capture_output=True, text=True)  # noqa: S607
            else:
                # Linux/Unix service restart
                subprocess.run(["sudo", "systemctl", "restart", "podman"], check=True, capture_output=True, text=True)  # noqa: S607  # noqa: S603 S607

            # Give Podman some time to start up
            await asyncio.sleep(5)
            return {"success": True, "message": "Podman service restarted successfully"}

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to restart Podman service: {e.stderr}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Error restarting Podman service: {e!s}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def monitor(self):
        """Main monitoring loop."""
        logger.info("Starting Podman watchdog service...")

        while True:
            health = await self.check_podman_health()

            if health["status"] == "unhealthy":
                logger.warning("Podman CLI is unhealthy, attempting recovery...")
                result = await self.restart_podman_service()

                if not result.get("success"):
                    logger.error(f"Failed to recover Podman: {result.get('error')}")
                    # TODO: Send alert/notification
                else:
                    logger.info("Podman service recovery successful")
                    self.podman_client = self._get_podman_client()  # Reinitialize client

            await asyncio.sleep(self.check_interval)

    @classmethod
    async def start_service(cls, check_interval: int = 30, max_retries: int = 3):
        """Start the watchdog service."""
        watchdog = cls(check_interval=check_interval, max_retries=max_retries)
        await watchdog.monitor()


if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("podman_watchdog.log")],
    )

    # Start the watchdog
    try:
        asyncio.run(PodmanWatchdog.start_service())
    except KeyboardInterrupt:
        logger.info("Podman watchdog service stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error in Podman watchdog: {e}", exc_info=True)
        sys.exit(1)
