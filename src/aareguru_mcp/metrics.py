"""Prometheus metrics for monitoring MCP server performance."""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Any
import time

# Info metric for service metadata
service_info = Info("aareguru_mcp_service", "Service information")
service_info.info({"version": "1.0.0", "service": "aareguru-mcp"})

# Counter metrics
tool_calls_total = Counter(
    "aareguru_mcp_tool_calls_total",
    "Total number of MCP tool calls",
    ["tool_name", "status"],
)

resource_requests_total = Counter(
    "aareguru_mcp_resource_requests_total",
    "Total number of MCP resource requests",
    ["resource_uri", "status"],
)

prompt_requests_total = Counter(
    "aareguru_mcp_prompt_requests_total",
    "Total number of MCP prompt requests",
    ["prompt_name", "status"],
)

api_requests_total = Counter(
    "aareguru_mcp_api_requests_total",
    "Total number of Aareguru API requests",
    ["endpoint", "status_code"],
)

errors_total = Counter(
    "aareguru_mcp_errors_total",
    "Total number of errors",
    ["error_type", "component"],
)

# Histogram metrics for latency
tool_duration_seconds = Histogram(
    "aareguru_mcp_tool_duration_seconds",
    "Duration of tool calls in seconds",
    ["tool_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

api_request_duration_seconds = Histogram(
    "aareguru_mcp_api_request_duration_seconds",
    "Duration of Aareguru API requests in seconds",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# Gauge metrics
active_requests = Gauge(
    "aareguru_mcp_active_requests",
    "Number of currently active requests",
)

cache_size = Gauge(
    "aareguru_mcp_cache_size",
    "Number of items in cache",
    ["cache_type"],
)


class MetricsCollector:
    """Helper class for collecting metrics with context managers."""

    @staticmethod
    def track_tool_call(tool_name: str):
        """Context manager to track tool call metrics."""

        class ToolCallTracker:
            def __init__(self, name: str):
                self.name = name
                self.start_time = 0.0

            def __enter__(self):
                self.start_time = time.time()
                active_requests.inc()
                return self

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
                duration = time.time() - self.start_time
                tool_duration_seconds.labels(tool_name=self.name).observe(duration)

                status = "error" if exc_type else "success"
                tool_calls_total.labels(tool_name=self.name, status=status).inc()

                if exc_type:
                    errors_total.labels(
                        error_type=exc_type.__name__, component="tool"
                    ).inc()

                active_requests.dec()
                return False  # Don't suppress exceptions

        return ToolCallTracker(tool_name)

    @staticmethod
    def track_api_request(endpoint: str):
        """Context manager to track API request metrics."""

        class APIRequestTracker:
            def __init__(self, endpoint: str):
                self.endpoint = endpoint
                self.start_time = 0.0
                self.status_code = 0

            def __enter__(self):
                self.start_time = time.time()
                return self

            def set_status(self, status_code: int):
                """Set the HTTP status code for the request."""
                self.status_code = status_code

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
                duration = time.time() - self.start_time
                api_request_duration_seconds.labels(endpoint=self.endpoint).observe(
                    duration
                )

                status_code = self.status_code if self.status_code else (500 if exc_type else 200)
                api_requests_total.labels(
                    endpoint=self.endpoint, status_code=str(status_code)
                ).inc()

                if exc_type:
                    errors_total.labels(
                        error_type=exc_type.__name__, component="api_client"
                    ).inc()

                return False  # Don't suppress exceptions

        return APIRequestTracker(endpoint)

    @staticmethod
    def track_resource_request(resource_uri: str):
        """Track resource request metrics."""

        class ResourceRequestTracker:
            def __init__(self, uri: str):
                self.uri = uri

            def __enter__(self):
                active_requests.inc()
                return self

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
                status = "error" if exc_type else "success"
                resource_requests_total.labels(resource_uri=self.uri, status=status).inc()

                if exc_type:
                    errors_total.labels(
                        error_type=exc_type.__name__, component="resource"
                    ).inc()

                active_requests.dec()
                return False

        return ResourceRequestTracker(resource_uri)

    @staticmethod
    def track_prompt_request(prompt_name: str):
        """Track prompt request metrics."""

        class PromptRequestTracker:
            def __init__(self, name: str):
                self.name = name

            def __enter__(self):
                active_requests.inc()
                return self

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
                status = "error" if exc_type else "success"
                prompt_requests_total.labels(prompt_name=self.name, status=status).inc()

                if exc_type:
                    errors_total.labels(
                        error_type=exc_type.__name__, component="prompt"
                    ).inc()

                active_requests.dec()
                return False

        return PromptRequestTracker(prompt_name)
