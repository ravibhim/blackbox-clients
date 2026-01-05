"""
Blackbox: Automatic Evolution Tracking for AI Functions

Observe how your AI black box functions evolve as you iterate on signatures and implementations.
"""

from .decorator import blackbox, BlackboxFunction
from .config import set_config

# OpenTelemetry is initialized in init() after config is set

__version__ = "0.1.0"


def init(key: str, api_server: str | None = None) -> None:
    """
    Initialize the Blackbox SDK with a project key.

    Must be called before using @blackbox decorator.

    Args:
        key: Project key from Blackbox Cloud (e.g., 'bbc_proj_...')
        api_server: Optional API server URL (defaults to https://blackbox-backend-u2gu.onrender.com)

    Example:
        import blackbox

        blackbox.init(key="bbc_proj_abc123...")

        @blackbox
        def my_function(...):
            ...

        # Or with custom server:
        blackbox.init(key="bbc_proj_abc123...", api_server="http://localhost:9000")
    """
    set_config(key, api_server)

    # Initialize OpenTelemetry AFTER config is set so it uses the correct API server
    from .otel_setup import initialize_otel
    initialize_otel()

    from .config import get_api_server
    print(f"@blackbox initialized → {get_api_server()}")


__all__ = [
    "__version__",
    "init",
    "blackbox",
    "BlackboxFunction",
]
