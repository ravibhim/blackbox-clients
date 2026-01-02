"""
Example capture logic for blackbox package.

Handles capturing function inputs/outputs and saving them as examples.
"""

import logging
from datetime import datetime
from typing import Any

from .models import Signature
from .storage import save_example

logger = logging.getLogger(__name__)


def capture_example(
    function_name: str,
    signature: Signature,
    input_data: dict[str, Any],
    output_data: Any,
    otel_trace_id: str | None = None,
    otel_span_id: str | None = None,
    parent_span_id: str | None = None,
) -> bool:
    """
    Capture a function call as an example and send it to the API.

    Args:
        function_name: Name of the function being captured
        signature: Signature object containing schemas and metadata
        input_data: Input data as dict (already serialized)
        output_data: Output data (already serialized)
        otel_trace_id: OpenTelemetry trace ID (optional)
        otel_span_id: OpenTelemetry span ID for this blackbox function (optional)
        parent_span_id: Parent span ID for nested blackbox functions (optional)

    Returns:
        True if successfully sent to API, False otherwise
    """
    timestamp = datetime.now()

    # Send to API storage
    success = save_example(
        signature_hash=signature.signature_hash,
        function_name=function_name,
        input_schema=signature.input_schema,
        output_schema=signature.output_schema,
        description=signature.description,
        input_data=input_data,
        output_data=output_data,
        timestamp=timestamp,
        otel_trace_id=otel_trace_id,
        otel_span_id=otel_span_id,
        parent_span_id=parent_span_id,
    )

    if not success:
        logger.debug(f"Failed to capture example for {function_name}")

    return success
