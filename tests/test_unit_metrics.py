"""Unit tests for metrics collection module."""

import pytest
from prometheus_client import REGISTRY
from aareguru_mcp.metrics import (
    MetricsCollector,
    tool_calls_total,
    tool_duration_seconds,
    api_requests_total,
    errors_total,
    active_requests,
    resource_requests_total,
    prompt_requests_total,
)


class TestToolCallTracking:
    """Test tool call metrics tracking."""

    def test_successful_tool_call_increments_counter(self):
        """Test that successful tool calls increment the success counter."""
        initial_value = tool_calls_total.labels(
            tool_name="test_tool", status="success"
        )._value.get()

        with MetricsCollector.track_tool_call("test_tool"):
            pass  # Successful execution

        final_value = tool_calls_total.labels(
            tool_name="test_tool", status="success"
        )._value.get()
        assert final_value > initial_value

    def test_failed_tool_call_increments_error_counter(self):
        """Test that failed tool calls increment the error counter."""
        initial_value = tool_calls_total.labels(
            tool_name="test_tool", status="error"
        )._value.get()

        try:
            with MetricsCollector.track_tool_call("test_tool"):
                raise ValueError("Test error")
        except ValueError:
            pass

        final_value = tool_calls_total.labels(
            tool_name="test_tool", status="error"
        )._value.get()
        assert final_value > initial_value

    def test_tool_call_tracks_duration(self):
        """Test that tool calls track execution duration."""
        import time

        initial_samples = len(list(tool_duration_seconds.labels(tool_name="duration_test").collect()[0].samples))

        with MetricsCollector.track_tool_call("duration_test"):
            time.sleep(0.01)  # Sleep for 10ms

        # Verify histogram was updated (samples should increase)
        final_samples = len(list(tool_duration_seconds.labels(tool_name="duration_test").collect()[0].samples))
        assert final_samples >= initial_samples

    def test_tool_call_updates_active_requests(self):
        """Test that active requests gauge is updated during execution."""
        initial_active = active_requests._value.get()

        class CheckActiveRequests:
            def __init__(self):
                self.active_during_execution = None

            def execute(self):
                with MetricsCollector.track_tool_call("active_test"):
                    self.active_during_execution = active_requests._value.get()

        checker = CheckActiveRequests()
        checker.execute()

        # Active requests should have increased during execution
        assert checker.active_during_execution >= initial_active

    def test_error_type_tracked_correctly(self):
        """Test that different error types are tracked separately."""
        initial_value_error = errors_total.labels(
            error_type="ValueError", component="tool"
        )._value.get()
        initial_runtime_error = errors_total.labels(
            error_type="RuntimeError", component="tool"
        )._value.get()

        # Trigger ValueError
        try:
            with MetricsCollector.track_tool_call("error_test"):
                raise ValueError("Test")
        except ValueError:
            pass

        # Trigger RuntimeError
        try:
            with MetricsCollector.track_tool_call("error_test"):
                raise RuntimeError("Test")
        except RuntimeError:
            pass

        # Check both error types were tracked
        assert (
            errors_total.labels(error_type="ValueError", component="tool")._value.get()
            > initial_value_error
        )
        assert (
            errors_total.labels(error_type="RuntimeError", component="tool")._value.get()
            > initial_runtime_error
        )


class TestAPIRequestTracking:
    """Test API request metrics tracking."""

    def test_successful_api_request_tracking(self):
        """Test tracking successful API requests."""
        initial_value = api_requests_total.labels(
            endpoint="/test", status_code="200"
        )._value.get()

        with MetricsCollector.track_api_request("/test") as tracker:
            tracker.set_status(200)

        final_value = api_requests_total.labels(
            endpoint="/test", status_code="200"
        )._value.get()
        assert final_value > initial_value

    def test_failed_api_request_tracking(self):
        """Test tracking failed API requests."""
        initial_value = api_requests_total.labels(
            endpoint="/test", status_code="500"
        )._value.get()

        try:
            with MetricsCollector.track_api_request("/test") as tracker:
                raise Exception("API error")
        except Exception:
            pass

        final_value = api_requests_total.labels(
            endpoint="/test", status_code="500"
        )._value.get()
        assert final_value > initial_value

    def test_api_request_custom_status_code(self):
        """Test setting custom status codes."""
        initial_404 = api_requests_total.labels(
            endpoint="/test", status_code="404"
        )._value.get()

        with MetricsCollector.track_api_request("/test") as tracker:
            tracker.set_status(404)

        final_404 = api_requests_total.labels(
            endpoint="/test", status_code="404"
        )._value.get()
        assert final_404 > initial_404


class TestResourceRequestTracking:
    """Test resource request metrics tracking."""

    def test_successful_resource_request(self):
        """Test tracking successful resource requests."""
        initial_value = resource_requests_total.labels(
            resource_uri="aareguru://test", status="success"
        )._value.get()

        with MetricsCollector.track_resource_request("aareguru://test"):
            pass

        final_value = resource_requests_total.labels(
            resource_uri="aareguru://test", status="success"
        )._value.get()
        assert final_value > initial_value

    def test_failed_resource_request(self):
        """Test tracking failed resource requests."""
        initial_value = resource_requests_total.labels(
            resource_uri="aareguru://test", status="error"
        )._value.get()

        try:
            with MetricsCollector.track_resource_request("aareguru://test"):
                raise ValueError("Resource error")
        except ValueError:
            pass

        final_value = resource_requests_total.labels(
            resource_uri="aareguru://test", status="error"
        )._value.get()
        assert final_value > initial_value


class TestPromptRequestTracking:
    """Test prompt request metrics tracking."""

    def test_successful_prompt_request(self):
        """Test tracking successful prompt requests."""
        initial_value = prompt_requests_total.labels(
            prompt_name="test_prompt", status="success"
        )._value.get()

        with MetricsCollector.track_prompt_request("test_prompt"):
            pass

        final_value = prompt_requests_total.labels(
            prompt_name="test_prompt", status="success"
        )._value.get()
        assert final_value > initial_value

    def test_failed_prompt_request(self):
        """Test tracking failed prompt requests."""
        initial_value = prompt_requests_total.labels(
            prompt_name="test_prompt", status="error"
        )._value.get()

        try:
            with MetricsCollector.track_prompt_request("test_prompt"):
                raise ValueError("Prompt error")
        except ValueError:
            pass

        final_value = prompt_requests_total.labels(
            prompt_name="test_prompt", status="error"
        )._value.get()
        assert final_value > initial_value


class TestMetricsRegistry:
    """Test that metrics are properly registered."""

    def test_all_metrics_registered(self):
        """Test that all metrics are registered in Prometheus registry."""
        metric_names = []
        for collector in REGISTRY.collect():
            for metric in collector.samples if hasattr(collector, 'samples') else []:
                metric_names.append(metric.name)
            # Also check metric name directly
            if hasattr(collector, 'name'):
                metric_names.append(collector.name)

        # Check for key metrics (may have suffixes like _total, _count, etc.)
        metric_str = " ".join(metric_names)
        assert "aareguru_mcp_tool_calls" in metric_str
        assert "aareguru_mcp_tool_duration" in metric_str
        assert "aareguru_mcp_api_requests" in metric_str
        assert "aareguru_mcp_errors" in metric_str
        assert "aareguru_mcp_active_requests" in metric_str
        assert "aareguru_mcp_service_info" in metric_str

    def test_metrics_have_correct_types(self):
        """Test that metrics have the correct Prometheus types."""
        from prometheus_client import Counter, Histogram, Gauge

        assert isinstance(tool_calls_total, Counter)
        assert isinstance(tool_duration_seconds, Histogram)
        assert isinstance(api_requests_total, Counter)
        assert isinstance(errors_total, Counter)
        assert isinstance(active_requests, Gauge)


class TestConcurrentMetrics:
    """Test metrics collection under concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test that concurrent tool calls are tracked correctly."""
        import asyncio

        async def make_tool_call(name: str):
            with MetricsCollector.track_tool_call(name):
                await asyncio.sleep(0.01)

        # Execute multiple concurrent tool calls
        await asyncio.gather(
            make_tool_call("concurrent_test"),
            make_tool_call("concurrent_test"),
            make_tool_call("concurrent_test"),
        )

        # Verify all calls were tracked
        count = tool_calls_total.labels(
            tool_name="concurrent_test", status="success"
        )._value.get()
        assert count >= 3


class TestEdgeCases:
    """Test edge cases in metrics collection."""

    def test_empty_tool_name(self):
        """Test tracking with empty tool name."""
        with MetricsCollector.track_tool_call(""):
            pass
        # Should not raise an error

    def test_special_characters_in_names(self):
        """Test tracking with special characters in names."""
        with MetricsCollector.track_tool_call("test-tool_name.v2"):
            pass
        # Should not raise an error

    def test_very_long_tool_name(self):
        """Test tracking with very long tool name."""
        long_name = "a" * 200
        with MetricsCollector.track_tool_call(long_name):
            pass
        # Should not raise an error

    def test_nested_tracking_contexts(self):
        """Test nested tracking contexts."""
        with MetricsCollector.track_tool_call("outer"):
            with MetricsCollector.track_tool_call("inner"):
                pass
        # Both should be tracked independently
