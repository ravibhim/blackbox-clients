"""
Storage abstraction for blackbox package.

Handles sending examples to the Blackbox API.
"""

import logging
from typing import Any
from datetime import datetime

from .api_client import send_example

logger = logging.getLogger(__name__)


def save_example(
    signature_hash: str,
    function_name: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    description: str | None,
    input_data: dict[str, Any],
    output_data: Any,
    timestamp: datetime,
    otel_trace_id: str | None = None,
    otel_span_id: str | None = None,
    parent_span_id: str | None = None,
) -> bool:
    """
    Save an example by sending it to the Blackbox API.

    Args:
        signature_hash: SHA-256 hash of the function signature
        function_name: Fully qualified function name
        input_schema: JSON schema for function inputs
        output_schema: JSON schema for function outputs
        description: Function docstring (optional)
        input_data: Actual input values
        output_data: Actual output values
        timestamp: When the example was captured
        otel_trace_id: OpenTelemetry trace ID (optional)
        otel_span_id: OpenTelemetry span ID for this blackbox function (optional)
        parent_span_id: Parent span ID for nested blackbox functions (optional)

    Returns:
        True if successfully sent to API, False otherwise
    """
    return send_example(
        signature_hash=signature_hash,
        function_name=function_name,
        input_schema=input_schema,
        output_schema=output_schema,
        description=description,
        input_data=input_data,
        output_data=output_data,
        timestamp=timestamp,
        otel_trace_id=otel_trace_id,
        otel_span_id=otel_span_id,
        parent_span_id=parent_span_id,
    )
