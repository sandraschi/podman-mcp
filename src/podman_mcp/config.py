"""Re-export shim: sampling config now lives in podmanmcp (bundle self-containment)."""

from podmanmcp.sampling_config import SamplingConfig, get_sampling_config

__all__ = ["SamplingConfig", "get_sampling_config"]
