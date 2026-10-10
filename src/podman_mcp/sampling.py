"""Re-export shim: sampling handler now lives in podmanmcp (bundle self-containment)."""

from podmanmcp.sampling import PodmanSamplingHandler

__all__ = ["PodmanSamplingHandler"]
