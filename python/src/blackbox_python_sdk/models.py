"""
Data models for blackbox package.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Example:
    """Represents a single captured example of a function call."""

    id: str
    signature_hash: str
    timestamp: datetime
    input: dict[str, Any]
    output: dict[str, Any]
    function_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "id": self.id,
            "signature_hash": self.signature_hash,
            "timestamp": self.timestamp.isoformat(),
            "input": self.input,
            "output": self.output,
        }
        if self.function_name:
            result["function_name"] = self.function_name
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Example":
        """Create Example from dictionary loaded from YAML."""
        return cls(
            id=data["id"],
            signature_hash=data["signature_hash"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            input=data["input"],
            output=data["output"],
            function_name=data.get("function_name"),
        )


@dataclass
class Signature:
    """Represents a function signature.

    Uses content-addressed storage: the signature_hash serves as the
    unique identifier and is used as the filename.
    """

    signature_hash: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    function_name: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "signature_hash": self.signature_hash,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "created_at": self.created_at.isoformat(),
        }
        if self.function_name is not None:
            result["function_name"] = self.function_name
        if self.description is not None:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Signature":
        """Create Signature from dictionary loaded from YAML."""
        return cls(
            signature_hash=data["signature_hash"],
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            created_at=datetime.fromisoformat(data["created_at"]),
            function_name=data.get("function_name"),
            description=data.get("description"),
        )
