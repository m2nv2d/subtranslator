# Task 6: Add Distributed Tracing

## Project Context
To better understand request flow and identify bottlenecks, especially involving external calls like the Gemini API, distributed tracing can be implemented. OpenTelemetry is the standard for this.

## Goal
Integrate basic distributed tracing using OpenTelemetry and a FastAPI instrumentation library. Configure it to export traces to a simple backend (like console exporter for local debugging initially).

## Prerequisites
- FastAPI application structure.
- Access to `src/main.py`, `pyproject.toml`.
- Conceptual understanding of distributed tracing (spans, traces, exporters).

## Subtask 1: Add Dependencies
- Add the necessary OpenTelemetry packages using `uv`:
  ```bash
  # Core API and SDK
  uv add opentelemetry-api opentelemetry-sdk
  
  # FastAPI instrumentation
  uv add opentelemetry-instrumentation-fastapi
  
  # Standard instrumentors (requests, httpx if used for Gemini client)
  uv add opentelemetry-instrumentation-requests opentelemetry-instrumentation-httpx
  
  # Exporter (e.g., console for testing)
  uv add opentelemetry-exporter-otlp-proto-http
  # Or: uv add opentelemetry-exporter-otlp-proto-grpc
  # Or for simple console output:
  # uv add opentelemetry-exporter-logging 
  ```

## Subtask 2: Configure OpenTelemetry SDK
- In a new file (e.g., `src/core/tracing.py`) or early in `src/main.py`, configure the OpenTelemetry SDK:
  - Set up a Tracer Provider.
  - Configure a Span Exporter (start with `ConsoleSpanExporter` or `OTLPSpanExporter` pointing to a local collector like Jaeger/Tempo if available, or console).
  - Configure a Span Processor (e.g., `BatchSpanProcessor`).
  - Set the global Tracer Provider.

*Example (`src/core/tracing.py` using Console Exporter):*
```python
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

def setup_tracing(service_name: str = "subtranslator"):
    try:
        resource = Resource.create({"service.name": service_name})
        
        # Set up tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure console exporter
        # Replace with OTLPSpanExporter for real backends
        exporter = ConsoleSpanExporter()
        
        # Configure batch span processor
        span_processor = BatchSpanProcessor(exporter)
        tracer_provider.add_span_processor(span_processor)
        
        logging.getLogger(__name__).info("OpenTelemetry tracing configured with ConsoleExporter.")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to configure OpenTelemetry tracing: {e}")

# Call setup_tracing() early in main.py
```

## Subtask 3: Instrument FastAPI and Libraries
- In `src/main.py` (after setting up tracing):
    - Import necessary instrumentation classes:
      ```python
      from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
      # Import instrumentors for libraries used (e.g., httpx if Gemini client uses it)
      # from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
      ```
    - Instrument FastAPI:
      ```python
      # After app = FastAPI() and setup_tracing()
      FastAPIInstrumentor.instrument_app(app)
      ```
    - Instrument other libraries (e.g., HTTPX if used):
      ```python
      # HTTPXClientInstrumentor().instrument()
      ```

## Subtask 4: (Optional) Add Custom Spans
- To get more detailed traces, add custom spans around specific operations, like the call to the Gemini API or SRT parsing.
- Get a tracer instance: `tracer = trace.get_tracer(__name__)`
- Create spans using `with tracer.start_as_current_span("span_name") as span:`

*Example (in `translate_all_chunks`):*
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def translate_all_chunks(...):
    # ...
    with tracer.start_as_current_span("translate_all_chunks_orchestration") as span:
        span.set_attribute("num_chunks", len(sub))
        span.set_attribute("target_language", target_lang)
        # ... gather tasks ...
        async with tracer.start_as_current_span("gather_translation_tasks") as gather_span:
            results = await asyncio.gather(*tasks, return_exceptions=True)
    # ...
```

## Testing
- Run the application.
- Make requests to the API (`/`, `/translate`).
- Observe the console output (if using `ConsoleSpanExporter`). Look for lines representing spans being started and ended for:
    - Incoming FastAPI requests.
    - Outgoing HTTP requests (if `requests` or `httpx` is instrumented and used).
    - Any custom spans added.
- If using a backend like Jaeger/Tempo via OTLP exporter:
    - Check the tracing UI for new traces corresponding to your requests.
    - Examine the trace structure, timing of spans, and any attributes added.
- Verify that trace context is propagated (e.g., all spans within a single request share the same `trace_id`). 