# Task 5: Add Application Metrics

## Project Context
The application currently lacks observability features like metrics. Adding basic metrics can help monitor request rates, errors, and latency, providing valuable insights into application performance and health.

## Goal
Integrate basic application metrics using a suitable FastAPI library, such as `prometheus-fastapi-instrumentator`, to expose standard request metrics via a `/metrics` endpoint.

## Prerequisites
- FastAPI application structure.
- Access to `src/main.py` and `pyproject.toml` (or `requirements.txt`).
- Basic understanding of Prometheus metrics types (counter, gauge, histogram).

## Subtask 1: Add Dependency
- Add the metrics library to the project dependencies using `uv`.
  ```bash
  uv add prometheus-fastapi-instrumentator
  # or add "prometheus-fastapi-instrumentator" to pyproject.toml and run uv pip sync
  ```

## Subtask 2: Instrument the FastAPI App
- In `src/main.py`:
    - Import the instrumentator class: `from prometheus_fastapi_instrumentator import Instrumentator`
    - After the `app = FastAPI()` instance is created, instantiate and expose the instrumentator:
      ```python
      # ... after app = FastAPI()
      
      # Instrument the app
      Instrumentator().instrument(app).expose(app)
      
      # ... rest of app setup (middleware, routers, etc.)
      ```
    - This basic setup automatically provides several default metrics, including:
        - `http_requests_total`: Counter for total requests.
        - `http_requests_inprogress`: Gauge for requests currently being processed.
        - `http_request_duration_seconds`: Histogram/Summary of request latencies.
        - `http_response_size_bytes`: Histogram/Summary of response sizes.
        - `http_request_size_bytes`: Histogram/Summary of request sizes.

## Subtask 3: (Optional) Customize Metrics
- The `prometheus-fastapi-instrumentator` library allows customization (e.g., adding custom labels, changing metric names, adding custom metrics).
- **Example (Adding custom label):**
  ```python
  Instrumentator().instrument(app).expose(app, include_in_schema=False)
  
  # Example: Add a custom label based on speed_mode if possible
  # This might require a more complex setup or custom middleware if the value
  # isn't easily accessible during instrumentation.
  ```
- **Example (Adding custom metric):**
  ```python
  from prometheus_client import Counter
  
  TRANSLATIONS_COMPLETED = Counter(
      "subtranslator_translations_completed_total",
      "Total number of successful subtitle translations completed",
      ["target_lang", "speed_mode"]
  )
  
  # In your /translate endpoint logic (after successful translation):
  TRANSLATIONS_COMPLETED.labels(target_lang=target_lang, speed_mode=speed_mode).inc()
  ```
- For this initial task, focus on the default instrumentation. Customization can be a follow-up task.

## Subtask 4: Verify Metrics Endpoint
- Run the application using `uvicorn`.
- Access the `/metrics` endpoint in your browser or using `curl localhost:<port>/metrics`.
- Verify that a Prometheus-compatible metrics output is displayed.
- Observe the default metrics (e.g., `http_requests_total`, `http_request_duration_seconds`).

## Subtask 5: Test Metric Collection
- Make several requests to different application endpoints (`/`, `/translate` with valid and invalid inputs).
- Refresh the `/metrics` endpoint.
- Verify that the values of the metrics change accordingly:
    - `http_requests_total` should increment for each request.
    - `http_request_duration_seconds` buckets should populate based on request latency.
    - If error handlers are triggered, metrics related to specific status codes should reflect this.

## Testing
- Primarily involves running the application and manually inspecting the `/metrics` endpoint after making requests.
- Automated tests could potentially scrape the `/metrics` endpoint and assert the presence of specific metric names, but verifying exact values is often brittle.
- Ensure the `/metrics` endpoint is accessible and returns valid Prometheus format. 