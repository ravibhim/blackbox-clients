"""
Blackbox: Automatic Evolution Tracking for AI Functions

Observe how your AI black box functions evolve as you iterate on signatures and implementations.
"""

from .decorator import blackbox, BlackboxFunction
from .config import set_project_key

# Initialize OpenTelemetry at import time for better performance
# This eliminates per-call overhead from lazy initialization
from .otel_setup import initialize_otel
initialize_otel()

__version__ = "0.1.0"


def init(key: str) -> None:
    """
    Initialize the Blackbox SDK with a project key.

    Must be called before using @blackbox decorator.

    Args:
        key: Project key from Blackbox Cloud (e.g., 'bbc_proj_...')

    Example:
        import blackbox

        blackbox.init(key="bbc_proj_abc123...")

        @blackbox
        def my_function(...):
            ...
    """
    set_project_key(key)


__all__ = [
    "__version__",
    "init",
    "blackbox",
    "BlackboxFunction",
]
