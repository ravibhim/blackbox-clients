"""
Signature extraction and versioning for blackbox package.

Extracts function signatures from type hints and detects changes.
Supports multiple parameters of any type (not just Pydantic models).
"""

import hashlib
import inspect
import json
import types
from datetime import datetime
from typing import Any, Union, get_origin, get_args
from pydantic import BaseModel

from .models import Signature


class SignatureError(Exception):
    """Raised when function signature is invalid or missing required type hints."""
    pass


class SignatureManager:
    """
    Manages signature extraction and versioning for blackbox functions.

    This class handles:
    - Extracting schemas from function type hints (any types, not just Pydantic)
    - Computing signature hashes for version detection
    - Detecting when signatures change
    - Creating and managing versions
    """

    def __init__(self, base_dir: str = ".blackbox"):
        """
        Initialize the SignatureManager.

        Args:
            base_dir: Base directory for blackbox storage
        """
        self.base_dir = base_dir

    def _python_type_to_json_schema(self, typ: Any) -> dict[str, Any]:
        """
        Convert a Python type hint to a JSON schema representation.

        Args:
            typ: Python type annotation

        Returns:
            JSON schema dict for the type
        """
        # Handle None/empty annotation
        if typ is None or typ == inspect.Parameter.empty or typ == inspect.Signature.empty:
            return {"type": "any"}

        # Handle Pydantic BaseModel
        if inspect.isclass(typ) and issubclass(typ, BaseModel):
            try:
                return typ.model_json_schema()
            except:
                return {"type": "object", "description": typ.__name__}

        # Get origin for generic types (List, Dict, Optional, etc.)
        origin = get_origin(typ)
        args = get_args(typ)

        # Handle Optional[T] (Union[T, None])
        if origin is type(None) or typ is type(None):
            return {"type": "null"}

        # Handle Union types (including Optional)
        if origin is Union or (hasattr(types, 'UnionType') and origin is types.UnionType):
            # For Optional[T], extract T
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                schema = self._python_type_to_json_schema(non_none_args[0])
                schema["nullable"] = True
                return schema
            # For other unions, use anyOf
            return {"anyOf": [self._python_type_to_json_schema(arg) for arg in args]}

        # Handle List[T]
        if origin is list:
            if args:
                return {"type": "array", "items": self._python_type_to_json_schema(args[0])}
            return {"type": "array"}

        # Handle Dict[K, V]
        if origin is dict:
            schema = {"type": "object"}
            if args and len(args) >= 2:
                schema["additionalProperties"] = self._python_type_to_json_schema(args[1])
            return schema

        # Handle tuple
        if origin is tuple:
            if args:
                return {
                    "type": "array",
                    "items": [self._python_type_to_json_schema(arg) for arg in args],
                    "minItems": len(args),
                    "maxItems": len(args)
                }
            return {"type": "array"}

        # Handle basic Python types
        if typ is str:
            return {"type": "string"}
        if typ is int:
            return {"type": "integer"}
        if typ is float:
            return {"type": "number"}
        if typ is bool:
            return {"type": "boolean"}
        if typ is dict:
            return {"type": "object"}
        if typ is list:
            return {"type": "array"}

        # For custom classes, use object with class name
        if inspect.isclass(typ):
            return {"type": "object", "description": typ.__name__}

        # Fallback to any
        return {"type": "any", "description": str(typ)}

    def extract_signature(self, func: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Extract input and output schemas from a function's type hints.

        Supports functions with multiple parameters of any type.

        Args:
            func: Function to extract signature from

        Returns:
            Tuple of (input_schema, output_schema)
        """
        # Get function signature
        sig = inspect.signature(func)

        # Build input schema from all parameters
        input_properties = {}
        required_params = []

        for param_name, param in sig.parameters.items():
            # Skip 'self' parameter for methods
            if param_name == 'self':
                continue

            # Get type annotation
            param_type = param.annotation

            # Convert to JSON schema
            input_properties[param_name] = self._python_type_to_json_schema(param_type)

            # Track required parameters (no default value)
            if param.default == inspect.Parameter.empty:
                required_params.append(param_name)

        # Build input schema
        input_schema = {
            "type": "object",
            "properties": input_properties
        }
        if required_params:
            input_schema["required"] = required_params

        # Extract return type annotation (output)
        return_type = sig.return_annotation
        output_schema = self._python_type_to_json_schema(return_type)

        # If output is not an object type, wrap it
        if output_schema.get("type") != "object" and "anyOf" not in output_schema:
            output_schema = {
                "type": "object",
                "properties": {
                    "result": output_schema
                }
            }

        return input_schema, output_schema

    def compute_hash(
        self,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        function_name: str
    ) -> str:
        """
        Compute a stable hash for the signature schemas.

        Args:
            input_schema: Input JSON schema
            output_schema: Output JSON schema
            function_name: Fully qualified function name

        Returns:
            Hex string hash of the schemas
        """
        # Combine schemas and function name into a single dict
        combined = {
            "function_name": function_name,
            "input": input_schema,
            "output": output_schema
        }

        # Convert to stable JSON string (sorted keys)
        json_str = json.dumps(combined, sort_keys=True)

        # Compute SHA256 hash
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        return hash_obj.hexdigest()  # Full SHA-256 hash (64 hex characters)


    def extract_signature_object(
        self,
        func: Any,
        function_name: str | None = None,
        description: str | None = None
    ) -> Signature:
        """
        Extract signature information from a function without saving to disk.

        This method creates a Signature object for API storage.

        Args:
            func: Function to extract signature from
            function_name: Optional function name (defaults to func.__name__)
            description: Optional function description (from docstring)

        Returns:
            Signature object containing schemas and metadata

        Raises:
            SignatureError: If function signature is invalid
        """
        if function_name is None:
            function_name = func.__name__

        # Extract schemas from function
        input_schema, output_schema = self.extract_signature(func)

        # Compute hash (includes function name for uniqueness)
        sig_hash = self.compute_hash(input_schema, output_schema, function_name)

        # Create signature object (don't save to disk)
        signature = Signature(
            signature_hash=sig_hash,
            input_schema=input_schema,
            output_schema=output_schema,
            created_at=datetime.now(),
            function_name=function_name,
            description=description
        )

        return signature
