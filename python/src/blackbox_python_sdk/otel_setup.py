"""OpenTelemetry setup for client SDK - auto-instruments LLM providers."""
import logging
import os
import atexit
import signal
import sys
import threading

logger = logging.getLogger(__name__)

_initialized = False
_shutdown_registered = False
_shutdown_complete = False
_lock = threading.Lock()


def initialize_otel():
    """
    Initialize OpenTelemetry with auto-instrumentation for LLM providers.

    This is called automatically on first import of blackbox decorator.
    Sets up spans to be sent to the backend API endpoint.
    """
    global _initialized

    with _lock:
        if _initialized:
            logger.debug("Already initialized, returning early")
            return

        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.trace import NoOpTracerProvider, ProxyTracerProvider
            from .span_exporter import BlackboxSpanExporter

            # Check for conflicting TracerProvider setup
            existing_provider = trace.get_tracer_provider()

            # NoOpTracerProvider is the default (no conflict)
            # ProxyTracerProvider is used by some tools but hasn't been set yet (no conflict)
            # Anything else means another tool already configured OTel (conflict!)

            if not isinstance(existing_provider, (NoOpTracerProvider, ProxyTracerProvider)):
                logger.warning(
                    f"⚠️  Another OpenTelemetry TracerProvider is already configured ({type(existing_provider).__name__}). "
                    f"Blackbox will not initialize. Spans may not be exported to Blackbox backend. "
                    f"Please remove other OTel setup or disable Blackbox."
                )
                _initialized = True
                return

            # No conflicts - create and set our TracerProvider
            provider = TracerProvider()
            trace.set_tracer_provider(provider)
            logger.info("Created new TracerProvider for Blackbox")

            # Add custom HTTP exporter to send LLM spans to backend
            from .config import get_api_server
            backend_url = get_api_server()
            http_exporter = BlackboxSpanExporter(backend_url=backend_url)
            http_processor = BatchSpanProcessor(
                http_exporter,
                max_queue_size=2048,
                schedule_delay_millis=5000,  # Export every 5 seconds
                max_export_batch_size=512,
            )
            provider.add_span_processor(http_processor)
            logger.info(f"Blackbox HTTP span exporter enabled (backend: {backend_url})")

            # Auto-instrument LLM providers
            _auto_instrument_all()

            # Register shutdown handlers for graceful cleanup
            _register_shutdown_handlers()

            _initialized = True
            logger.info("Blackbox OpenTelemetry initialization complete")

        except ImportError as e:
            logger.warning(f"OpenTelemetry not available (ImportError): {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry (Exception): {e}")
            import traceback
            logger.warning(f"Traceback: {traceback.format_exc()}")


def _auto_instrument_all():
    """Auto-instrument all available LLM providers."""

    # OpenAI (will also capture Groq calls when using OpenAI SDK with Groq base_url)
    try:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
        logger.info("OpenAI instrumentation enabled")
    except ImportError:
        logger.debug("OpenAI instrumentation not available")
    except Exception as e:
        logger.warning(f"OpenAI instrumentation failed: {e}")

    # Anthropic
    try:
        from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
        AnthropicInstrumentor().instrument()
        logger.info("Anthropic instrumentation enabled")
    except ImportError:
        logger.debug("Anthropic instrumentation not available")
    except Exception as e:
        logger.warning(f"Anthropic instrumentation failed: {e}")

    # Groq
    try:
        from openinference.instrumentation.groq import GroqInstrumentor
        GroqInstrumentor().instrument()
        logger.info("Groq instrumentation enabled")
    except ImportError:
        logger.debug("Groq instrumentation not available")
    except Exception as e:
        logger.warning(f"Groq instrumentation failed: {e}")


def _graceful_shutdown(signum=None, frame=None):
    """
    Gracefully shutdown OpenTelemetry, flushing all pending spans.

    Called on:
    - Normal exit (atexit)
    - SIGTERM (graceful shutdown request)
    - SIGINT (Ctrl+C)

    Args:
        signum: Signal number if called from signal handler
        frame: Current stack frame if called from signal handler
    """
    global _shutdown_complete

    # Idempotent: only shutdown once
    if not _initialized or _shutdown_complete:
        return

    _shutdown_complete = True

    try:
        from opentelemetry import trace
        provider = trace.get_tracer_provider()

        if hasattr(provider, 'force_flush'):
            logger.info("Flushing pending spans before shutdown...")
            provider.force_flush(timeout_millis=30000)  # 30 second timeout for final flush

        if hasattr(provider, 'shutdown'):
            logger.info("Shutting down OpenTelemetry...")
            provider.shutdown()

        logger.info("Blackbox shutdown complete")
    except Exception as e:
        logger.warning(f"Error during graceful shutdown: {e}")


def _register_shutdown_handlers():
    """Register shutdown handlers for graceful cleanup."""
    global _shutdown_registered

    if _shutdown_registered:
        return

    # Register atexit handler for normal program termination
    atexit.register(_graceful_shutdown)

    # Register signal handlers for SIGTERM and SIGINT
    try:
        signal.signal(signal.SIGTERM, _graceful_shutdown)
        signal.signal(signal.SIGINT, _graceful_shutdown)
        logger.debug("Shutdown handlers registered (atexit, SIGTERM, SIGINT)")
    except (ValueError, OSError) as e:
        # Signal handlers can only be registered in the main thread
        logger.debug(f"Could not register signal handlers: {e}")

    _shutdown_registered = True
