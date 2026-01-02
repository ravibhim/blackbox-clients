"""
Global configuration for blackbox SDK.

Stores the project key set via init().
"""

_project_key: str | None = None
_initialized: bool = False


def set_project_key(key: str) -> None:
    """Set the project key for all blackbox operations."""
    global _project_key, _initialized
    _project_key = key
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


def is_initialized() -> bool:
    """Check if the SDK has been initialized."""
    return _initialized
