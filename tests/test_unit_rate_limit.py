"""Unit tests for rate limiting module."""

from starlette.requests import Request

from aareguru_mcp.rate_limit import limiter, rate_limit_exceeded_handler


class TestRateLimiterConfiguration:
    """Test rate limiter configuration."""

    def test_limiter_exists(self):
        """Test that limiter is properly initialized."""
        assert limiter is not None

    def test_limiter_has_storage(self):
        """Test that limiter has storage backend configured."""
        # Check storage backend is configured
        assert limiter._storage is not None

    def test_limiter_can_be_used_as_decorator(self):
        """Test that limiter can be used as a decorator."""
        from starlette.responses import JSONResponse

        @limiter.limit("10/minute")
        async def test_endpoint(request: Request):
            return JSONResponse({"status": "ok"})

        # Should not raise an error
        assert test_endpoint is not None


class TestRateLimitIntegration:
    """Test rate limiting integration with HTTP endpoints."""

    def test_limiter_can_be_applied_as_decorator(self):
        """Test that limiter can be used as a decorator."""
        from starlette.responses import JSONResponse

        @limiter.limit("10/minute")
        async def test_endpoint(request: Request):
            return JSONResponse({"status": "ok"})

        # Should not raise an error
        assert test_endpoint is not None

    def test_rate_limit_handler_is_callable(self):
        """Test that rate limit exceeded handler is a callable function."""
        assert callable(rate_limit_exceeded_handler)

    def test_multiple_limits_can_be_applied(self):
        """Test that multiple rate limits can be applied to same endpoint."""
        from starlette.responses import JSONResponse

        @limiter.limit("10/minute")
        @limiter.limit("100/hour")
        async def test_endpoint(request: Request):
            return JSONResponse({"status": "ok"})

        # Should not raise an error
        assert test_endpoint is not None
