"""
Custom JSON encoder for Podman MCP server to handle Podman SDK objects and other non-serializable types.
"""

import json
import logging
import re
import uuid
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class PodmanJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Podman SDK objects and other non-serializable types."""

    # Cache for type handlers to improve performance
    _type_handlers: ClassVar[dict[type, Callable[[Any], Any]]] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_type_handlers()

    def _setup_type_handlers(self):
        """Initialize type handlers for common Podman SDK types and Python types."""
        # Clear existing handlers
        self._type_handlers = {}

        # Register standard Python type handlers
        self._type_handlers.update(
            {
                datetime: lambda x: x.isoformat(),
                set: list,
                frozenset: list,
                bytes: lambda x: x.decode("utf-8", errors="replace"),
                uuid.UUID: str,
                type(re.compile("")): lambda x: x.pattern,
                Enum: lambda x: x.name,
            }
        )

        # Try to import and handle Podman SDK types
        try:
            import podman.models.containers
            import podman.models.images
            import podman.models.networks
            import podman.models.volumes

            # Register Podman container handlers
            self._type_handlers.update(
                {
                    podman.models.containers.Container: self._serialize_podman_container,
                    podman.models.images.Image: self._serialize_podman_image,
                    podman.models.networks.Network: self._serialize_podman_network,
                    podman.models.volumes.Volume: self._serialize_podman_volume,
                }
            )

        except ImportError:
            logger.debug("Podman SDK not available, using basic type handlers")

    def _serialize_podman_container(self, container) -> dict[str, Any]:
        """Serialize a Podman container object."""
        try:
            return {
                "id": container.id,
                "short_id": container.short_id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                "created": container.attrs["Created"],
                "state": container.attrs["State"],
                "labels": container.labels,
            }
        except Exception as e:
            logger.warning(f"Failed to serialize container {getattr(container, 'id', 'unknown')}: {e}")
            return {"id": getattr(container, "id", "unknown"), "error": str(e)}

    def _serialize_podman_image(self, image) -> dict[str, Any]:
        """Serialize a Podman image object."""
        try:
            return {
                "id": image.id,
                "short_id": image.short_id,
                "tags": image.tags,
                "created": image.attrs["Created"],
                "size": image.attrs.get("Size"),
                "virtual_size": image.attrs.get("VirtualSize"),
                "labels": image.labels,
            }
        except Exception as e:
            logger.warning(f"Failed to serialize image {getattr(image, 'id', 'unknown')}: {e}")
            return {"id": getattr(image, "id", "unknown"), "error": str(e)}

    def _serialize_podman_network(self, network) -> dict[str, Any]:
        """Serialize a Podman network object."""
        try:
            return {
                "id": network.id,
                "name": network.name,
                "driver": network.attrs.get("Driver"),
                "scope": network.attrs.get("Scope"),
                "ipam": network.attrs.get("IPAM"),
                "containers": network.attrs.get("Containers", {}),
                "labels": network.attrs.get("Labels", {}),
                "created": network.attrs.get("Created"),
            }
        except Exception as e:
            logger.warning(f"Failed to serialize network {getattr(network, 'id', 'unknown')}: {e}")
            return {"id": getattr(network, "id", "unknown"), "error": str(e)}

    def _serialize_podman_volume(self, volume) -> dict[str, Any]:
        """Serialize a Podman volume object."""
        try:
            return {
                "name": volume.name,
                "driver": volume.attrs.get("Driver"),
                "mountpoint": volume.attrs.get("Mountpoint"),
                "labels": volume.attrs.get("Labels", {}),
                "options": volume.attrs.get("Options", {}),
                "created": volume.attrs.get("CreatedAt"),
                "scope": volume.attrs.get("Scope"),
            }
        except Exception as e:
            logger.warning(f"Failed to serialize volume {getattr(volume, 'name', 'unknown')}: {e}")
            return {"name": getattr(volume, "name", "unknown"), "error": str(e)}

    def default(self, obj: Any) -> Any:
        """Convert objects to a JSON-serializable format."""
        # Check for registered type handlers first
        for type_, handler in self._type_handlers.items():
            if isinstance(obj, type_) or (isinstance(type_, type) and isinstance(obj, type_)):
                try:
                    return handler(obj)
                except Exception as e:
                    logger.debug(f"Handler for {type_.__name__} failed: {e}")
                    break  # Fall through to default handling

        # Handle common non-serializable types
        if hasattr(obj, "__dict__"):
            return self.clean_dict(obj.__dict__)
        elif hasattr(obj, "_asdict"):
            return self.clean_dict(obj._asdict())
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
            return [self.default(item) for item in obj]

        # Try to get a string representation as a fallback
        try:
            return str(obj)
        except Exception as e:
            logger.debug(f"Could not serialize object of type {type(obj).__name__}: {e}")
            return None

    def clean_dict(self, d: Any) -> Any:
        """Recursively clean a dictionary or object to ensure it's JSON-serializable."""
        if d is None:
            return None

        # Handle dictionaries
        if isinstance(d, dict):
            result = {}
            for key, value in d.items():
                # Skip private attributes
                if isinstance(key, str) and key.startswith("_"):
                    continue

                try:
                    # Clean the value
                    cleaned_value = self.clean_dict(value)

                    # Only include non-None values
                    if cleaned_value is not None:
                        result[key] = cleaned_value

                except Exception as e:
                    logger.debug(f"Could not serialize {key}: {e}")

            return result

        # Handle lists, tuples, and sets
        elif isinstance(d, (list, tuple, set)):
            result = []
            for item in d:
                try:
                    cleaned_item = self.clean_dict(item)
                    if cleaned_item is not None:
                        result.append(cleaned_item)
                except Exception as e:
                    logger.debug(f"Could not serialize list item: {e}")
            return result

        # Handle other objects with __dict__
        elif hasattr(d, "__dict__"):
            return self.clean_dict(d.__dict__)

        # Handle namedtuples
        elif hasattr(d, "_asdict"):
            return self.clean_dict(d._asdict())

        # Handle other types using the default encoder
        else:
            try:
                # Try to use the default encoder first
                return self.default(d)
            except Exception as e:
                logger.debug(f"Could not serialize value of type {type(d).__name__}: {e}")
                return str(d) if d is not None else None


def dumps(obj: Any, **kwargs) -> str:
    """Serialize obj to a JSON formatted str using the custom encoder."""
    return json.dumps(obj, cls=PodmanJSONEncoder, **kwargs)


def loads(json_str: str, **kwargs) -> Any:
    """Deserialize json_str to a Python object."""
    return json.loads(json_str, **kwargs)
