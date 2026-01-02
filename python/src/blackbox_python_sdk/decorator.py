"""
Decorator implementation for blackbox package.

Provides the @blackbox decorator for capturing function inputs/outputs.
Supports functions with multiple parameters of any type.
"""

import asyncio
import functools
import inspect
from typing import Any, Callable
from pydantic import BaseModel
from opentelemetry import trace

from .signature import SignatureManager
from .capture import capture_example


def _serialize_value(value: Any) -> Any:
    """
    Serialize a value for storage.

    Converts Pydantic models to dicts, handles other types gracefully.

    Args:
        value: Value to serialize

    Returns:
        Serialized value (dict, list, or primitive)
    """
    # Handle Pydantic BaseModel
    if isinstance(value, BaseModel):
        return value.model_dump()

    # Handle lists
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    # Handle dicts
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    # Handle tuples
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]

    # Primitives and other types
    return value


def _get_trace_context() -> tuple[str | None, str | None, str | None]:
    """
    Get current OpenTelemetry trace_id, span_id, and parent_span_id as hex strings.

    Returns:
        Tuple of (trace_id, span_id, parent_span_id) as hex strings, or (None, None, None) if no active span
    """
    try:
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, "032x")
            span_id = format(ctx.span_id, "016x")

            # Get parent span ID for nested blackbox support
            parent_span_id = None
            if hasattr(span, 'parent') and span.parent and span.parent.is_valid:
                parent_span_id = format(span.parent.span_id, "016x")

            return trace_id, span_id, parent_span_id
    except Exception:
        pass

    return None, None, None


class BlackboxFunction:
    """
    Wrapper class that holds function + signature for capture.

    This class wraps a decorated function to capture inputs/outputs as examples.
    Use the blackbox CLI to view examples and signatures.
    """

    def __init__(
        self,
        func: Callable,
        function_name: str,
        signature: Any,  # Signature object from models.py
    ):
        """
        Initialize BlackboxFunction wrapper.

        Args:
            func: Original function to wrap
            function_name: Name of the function
            signature: Signature object containing schemas and metadata
        """
        self.func = func
        self.function_name = function_name
        self.signature = signature
        self.is_async = asyncio.iscoroutinefunction(func)
        self.sig = inspect.signature(func)

        # Preserve function metadata
        functools.update_wrapper(self, func)

    def __get__(self, obj, objtype=None):
        """
        Support instance methods by implementing the descriptor protocol.

        This allows the decorator to work properly with instance methods.
        When accessed as an attribute, it returns a partial function with 'self' bound.

        Args:
            obj: Instance object (self)
            objtype: Class type

        Returns:
            Partial function with 'self' bound for instance methods,
            or self for regular functions
        """
        if obj is None:
            # Called on the class, not an instance
            return self
        # Return a partial function with 'self' bound
        return functools.partial(self.__call__, obj)

    def __call__(self, *args, **kwargs) -> Any:
        """
        Call the wrapped function and optionally capture the example.

        Supports multiple parameters of any type.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Output from the original function
        """
        if self.is_async:
            return self._async_call(*args, **kwargs)
        else:
            return self._sync_call(*args, **kwargs)

    def _build_input_dict(self, *args, **kwargs) -> dict[str, Any]:
        """
        Build input dictionary from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Dict mapping parameter names to values
        """
        input_dict = {}

        try:
            # Bind arguments to parameter names
            bound = self.sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for param_name, param_value in bound.arguments.items():
                # Skip 'self' parameter for methods
                if param_name == 'self':
                    continue

                # Serialize the value
                input_dict[param_name] = _serialize_value(param_value)
        except Exception:
            # If binding fails, fall back to simple positional args
            for i, arg in enumerate(args):
                input_dict[f"arg{i}"] = _serialize_value(arg)
            for key, value in kwargs.items():
                input_dict[key] = _serialize_value(value)

        return input_dict

    def _sync_call(self, *args, **kwargs) -> Any:
        """Handle synchronous function calls."""
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            self.function_name,
            attributes={
                "blackbox.function_name": self.function_name,
                "blackbox.signature_hash": self.signature.signature_hash,
            },
        ):
            return self._execute_sync(*args, **kwargs)

    def _execute_sync(self, *args, **kwargs) -> Any:
        """Execute sync function and capture example."""
        # Call the original function
        output_data = self.func(*args, **kwargs)

        # Build input dict from arguments
        input_dict = self._build_input_dict(*args, **kwargs)

        # Serialize output
        output_dict = _serialize_value(output_data)

        # Get trace context (trace_id, span_id, and parent_span_id)
        trace_id, span_id, parent_span_id = _get_trace_context()

        capture_example(
            function_name=self.function_name,
            signature=self.signature,
            input_data=input_dict,
            output_data=output_dict,
            otel_trace_id=trace_id,
            otel_span_id=span_id,
            parent_span_id=parent_span_id,
        )

        return output_data

    async def _async_call(self, *args, **kwargs) -> Any:
        """Handle asynchronous function calls."""
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(
            self.function_name,
            attributes={
                "blackbox.function_name": self.function_name,
                "blackbox.signature_hash": self.signature.signature_hash,
            },
        ):
            return await self._execute_async(*args, **kwargs)

    async def _execute_async(self, *args, **kwargs) -> Any:
        """Execute async function and capture example."""
        # Call the original async function
        output_data = await self.func(*args, **kwargs)

        # Build input dict from arguments
        input_dict = self._build_input_dict(*args, **kwargs)

        # Serialize output
        output_dict = _serialize_value(output_data)

        # Get trace context (trace_id, span_id, and parent_span_id)
        trace_id, span_id, parent_span_id = _get_trace_context()

        capture_example(
            function_name=self.function_name,
            signature=self.signature,
            input_data=input_dict,
            output_data=output_dict,
            otel_trace_id=trace_id,
            otel_span_id=span_id,
            parent_span_id=parent_span_id,
        )

        return output_data


def blackbox(func: Callable) -> BlackboxFunction:
    """
    Decorator that captures function inputs/outputs as examples.

    Supports functions with multiple parameters of any type (not just Pydantic).
    Automatically extracts signature from type hints and captures examples on each call.

    Usage:
        @blackbox
        def my_function(query: str, context: str) -> dict:
            return {"answer": "..."}

        @blackbox
        async def async_function(profile: dict, question: str) -> str:
            return "response"

    Args:
        func: Function to decorate

    Returns:
        Decorated function wrapped in BlackboxFunction
    """
    # Extract scoped function name (module.qualname)
    function_name = f"{func.__module__}.{func.__qualname__}"

    # Extract docstring (cleaned, or None if no docstring)
    description = inspect.getdoc(func)

    # Extract signature (no longer saves to disk)
    sig_manager = SignatureManager()
    signature = sig_manager.extract_signature_object(func, function_name, description=description)

    # Create wrapped function
    return BlackboxFunction(
        func=func,
        function_name=function_name,
        signature=signature,
    )
