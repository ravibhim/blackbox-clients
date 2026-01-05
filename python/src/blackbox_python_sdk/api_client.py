"""HTTP client for sending examples to the Blackbox API."""
import logging
from typing import Any
from datetime import datetime

import httpx

from .config import get_project_key, get_api_server

logger = logging.getLogger(__name__)


def send_example(
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
    Send an example to the Blackbox API.

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
        True if successful, False otherwise (failures are logged but not raised)
    """
    # Get project key from global config
    project_key = get_project_key()

    payload = {
        "project_key": project_key,
        "signature_hash": signature_hash,
        "function_name": function_name,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "description": description,
        "input": input_data,
        "output": output_data,
        "timestamp": timestamp.isoformat(),
        "otel_trace_id": otel_trace_id,
        "otel_span_id": otel_span_id,
        "parent_span_id": parent_span_id,
    }

    try:
        api_endpoint = f"{get_api_server()}/api/v1/examples"
        response = httpx.post(
            api_endpoint,
            json=payload,
            timeout=5.0,  # 5 second timeout
        )
        response.raise_for_status()
        logger.debug(f"Successfully sent example to API: {response.json().get('id')}")
        return True

    except httpx.HTTPStatusError as e:
        logger.warning(
            f"API request failed with status {e.response.status_code}: {e.response.text}"
        )
        return False

    except httpx.RequestError as e:
        logger.warning(f"Network error while sending example to API: {e}")
        return False

    except Exception as e:
        logger.warning(f"Unexpected error while sending example to API: {e}")
        return False
