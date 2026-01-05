"""
Global configuration for blackbox SDK.

Stores the project key and API server set via init().
"""

DEFAULT_API_SERVER = "https://blackbox-backend-u2gu.onrender.com"

_project_key: str | None = None
_api_server: str = DEFAULT_API_SERVER
_initialized: bool = False


def set_config(key: str, api_server: str | None = None) -> None:
    """Set the project key and optional API server for all blackbox operations."""
    global _project_key, _api_server, _initialized
    _project_key = key
    if api_server is not None:
        _api_server = api_server
    _initialized = True


def get_project_key() -> str:
    """
    Get the project key.

    Raises:
        RuntimeError: If init() has not been called
    """
    if not _initialized:
        raise RuntimeError(
            "Blackbox SDK not initialized. Call blackbox.init(key='your-project-key') first."
        )
    return _project_key


def get_api_server() -> str:
    """Get the API server URL."""
    return _api_server


def is_initialized() -> bool:
    """Check if the SDK has been initialized."""
    return _initialized
