"""Custom span exporter that sends LLM spans to backend via HTTP API."""
import json
import logging
import httpx
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from typing import Sequence
from opentelemetry.sdk.trace import ReadableSpan
from datetime import datetime

logger = logging.getLogger(__name__)


class BlackboxSpanExporter(SpanExporter):
    """
    Custom exporter that sends LLM-related spans to Blackbox backend.

    Filters for LLM spans and sends them to the backend API endpoint
    where they will be processed and saved to the database.
    """

    def __init__(self, backend_url: str = None):
        """
        Initialize the exporter.

        Args:
            backend_url: Base URL of the Blackbox backend API
        """
        self.backend_url = backend_url or "http://localhost:9000"
        self.endpoint = f"{self.backend_url}/api/v1/llm-traces"
        self.client = httpx.Client(timeout=5.0)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """
        Export LLM spans to backend API.

        Args:
            spans: Sequence of ReadableSpan objects

        Returns:
            SpanExportResult.SUCCESS if export succeeded
        """
        try:
            llm_spans = [span for span in spans if self._is_llm_span(span)]

            if not llm_spans:
                return SpanExportResult.SUCCESS

            # Send each span to backend
            for span in llm_spans:
                try:
                    span_data = self._span_to_api_format(span)
                    response = self.client.post(self.endpoint, json=span_data, timeout=5.0)
                    response.raise_for_status()
                    logger.info(f"Exported LLM span {span_data['otel_span_id']} ({span_data['provider']}/{span_data['model']})")
                except Exception as e:
                    logger.warning(f"Failed to export span: {e}")
                    if hasattr(e, 'response') and hasattr(e.response, 'text'):
                        logger.warning(f"Response body: {e.response.text}")
                    # Continue with other spans even if one fails

            return SpanExportResult.SUCCESS

        except Exception as e:
            logger.error(f"Error exporting spans: {e}", exc_info=True)
            return SpanExportResult.FAILURE

    def _build_messages_dict(self, attrs: dict) -> dict:
        """Build input messages dict from Groq OpenInference attributes."""
        # Check if we have input.value (raw JSON string)
        input_value = attrs.get("input.value")
        if input_value:
            try:
                input_data = json.loads(input_value)
                # Return the messages array wrapped in a dict
                messages_list = input_data.get("messages", [])
                return {"messages": messages_list}
            except (json.JSONDecodeError, KeyError):
                pass

        # Fall back to extracting from llm.input_messages.* attributes
        messages = []
        i = 0
        while True:
            role = attrs.get(f"llm.input_messages.{i}.message.role")
            content = attrs.get(f"llm.input_messages.{i}.message.content")

            if role is None and content is None:
                break

            if role and content:
                messages.append({"role": role, "content": content})
            i += 1

        return {"messages": messages}

    def _build_response_dict(self, attrs: dict) -> dict:
        """Build output response dict from Groq OpenInference attributes."""
        # Check if we have output.value (raw JSON string)
        output_value = attrs.get("output.value")
        if output_value:
            try:
                return json.loads(output_value)
            except json.JSONDecodeError:
                pass

        # Fall back to extracting from llm.output_messages.* attributes
        messages = []
        i = 0
        while True:
            role = attrs.get(f"llm.output_messages.{i}.message.role")
            content = attrs.get(f"llm.output_messages.{i}.message.content")

            if role is None and content is None:
                break

            if role and content:
                messages.append({"role": role, "content": content})
            i += 1

        return {"messages": messages}

    def _is_llm_span(self, span: ReadableSpan) -> bool:
        """
        Check if span represents an LLM API call.

        Checks multiple attribute patterns to support different LLM providers:
        - OpenInference conventions (Groq)
        - GenAI semantic conventions (OpenAI)
        - Legacy LLM conventions (various providers)
        """
        if not span.attributes:
            return False

        attrs = span.attributes

        # Check for OpenInference LLM span kind (used by Groq, etc.)
        if attrs.get("openinference.span.kind") == "LLM":
            return True

        # Check for LLM model name attribute
        if "llm.model_name" in attrs:
            return True

        # Check for GenAI semantic conventions
        if "gen_ai.system" in attrs or "gen_ai.provider.name" in attrs:
            return True

        # Check for alternative conventions
        if "llm.vendor" in attrs or "llm.provider" in attrs:
            return True

        # Check span name patterns (as fallback)
        span_name_lower = span.name.lower()
        llm_patterns = ["openai", "anthropic", "chat.completions", "messages.create", "groq", "completions"]

        for pattern in llm_patterns:
            if pattern in span_name_lower:
                return True

        return False

    def _span_to_api_format(self, span: ReadableSpan) -> dict:
        """
        Convert span to API format expected by backend.

        Extracts all relevant LLM trace information from span attributes.
        """
        attrs = span.attributes or {}

        # Extract trace and span IDs
        trace_id = format(span.context.trace_id, "032x")
        span_id = format(span.context.span_id, "016x")
        parent_span_id = format(span.parent.span_id, "016x") if span.parent else None

        # Extract provider and model
        # Groq uses llm.model_name, OpenAI uses gen_ai.* attributes
        provider = (
            attrs.get("gen_ai.provider.name")
            or attrs.get("gen_ai.system")
            or attrs.get("llm.vendor")
            or attrs.get("llm.provider")
            or "unknown"
        )

        model = (
            attrs.get("llm.model_name")  # Groq OpenInference attribute
            or attrs.get("gen_ai.request.model")
            or attrs.get("llm.model")
            or attrs.get("gen_ai.response.model")
            or "unknown"
        )

        # Extract messages/prompt
        # Groq stores structured messages in llm.input_messages.* attributes
        messages = self._build_messages_dict(attrs)

        # Extract response
        # Groq stores response in llm.output_messages.* attributes
        response = self._build_response_dict(attrs)

        # Extract token usage
        # Groq uses llm.token_count.* attributes
        input_tokens = (
            attrs.get("llm.token_count.prompt")  # Groq OpenInference attribute
            or attrs.get("gen_ai.usage.input_tokens")
            or attrs.get("llm.usage.prompt_tokens")
            or attrs.get("gen_ai.usage.prompt_tokens")
        )

        output_tokens = (
            attrs.get("llm.token_count.completion")  # Groq OpenInference attribute
            or attrs.get("gen_ai.usage.output_tokens")
            or attrs.get("llm.usage.completion_tokens")
            or attrs.get("gen_ai.usage.completion_tokens")
        )

        # Determine status
        status = "success" if span.status.is_ok else "error"
        error_message = span.status.description if not span.status.is_ok else None

        # Convert timestamps
        started_at = datetime.fromtimestamp(span.start_time / 1_000_000_000).isoformat()
        completed_at = (
            datetime.fromtimestamp(span.end_time / 1_000_000_000).isoformat()
            if span.end_time
            else None
        )

        return {
            "otel_trace_id": trace_id,
            "otel_span_id": span_id,
            "parent_span_id": parent_span_id,
            "started_at": started_at,
            "status": status,
            # Data fields (packed into JSON blob by backend)
            "provider": provider,
            "model": model,
            "messages": messages,
            "response": response,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "completed_at": completed_at,
            "error_message": error_message,
        }

    def shutdown(self):
        """Shutdown the exporter."""
        try:
            self.client.close()
        except Exception:
            pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered spans."""
        return True
