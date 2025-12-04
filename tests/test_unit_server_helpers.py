"""Unit tests for server helper functions.

Tests safety assessment, seasonal advice, Swiss German explanations, and
other helper functions used by server tools.
"""

from datetime import datetime
from unittest.mock import patch

from aareguru_mcp.helpers import (
    _check_safety_warning,
    _get_safety_assessment,
    _get_seasonal_advice,
    _get_swiss_german_explanation,
)


class TestSeasonalAdvice:
    """Test _get_seasonal_advice for all seasons."""

    def test_winter_november(self):
        """Test winter advice for November."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 11, 15)
            result = _get_seasonal_advice()
            assert "Winter" in result
            assert "freezing" in result.lower()

    def test_winter_december(self):
        """Test winter advice for December."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 12, 15)
            result = _get_seasonal_advice()
            assert "Winter" in result

    def test_winter_january(self):
        """Test winter advice for January."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 15)
            result = _get_seasonal_advice()
            assert "Winter" in result

    def test_winter_february(self):
        """Test winter advice for February."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 2, 15)
            result = _get_seasonal_advice()
            assert "Winter" in result

    def test_winter_march(self):
        """Test winter advice for March."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 3, 15)
            result = _get_seasonal_advice()
            assert "Winter" in result

    def test_spring_april(self):
        """Test spring advice for April."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 4, 15)
            result = _get_seasonal_advice()
            assert "Spring" in result
            assert "snowmelt" in result.lower() or "wetsuit" in result.lower()

    def test_spring_may(self):
        """Test spring advice for May."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 5, 15)
            result = _get_seasonal_advice()
            assert "Spring" in result

    def test_summer_june(self):
        """Test summer advice for June."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 6, 15)
            result = _get_seasonal_advice()
            assert "Summer" in result
            assert "sunscreen" in result.lower()

    def test_summer_july(self):
        """Test summer advice for July."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 7, 15)
            result = _get_seasonal_advice()
            assert "Summer" in result

    def test_summer_august(self):
        """Test summer advice for August."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 8, 15)
            result = _get_seasonal_advice()
            assert "Summer" in result

    def test_autumn_september(self):
        """Test autumn advice for September."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 9, 15)
            result = _get_seasonal_advice()
            assert "Autumn" in result
            assert "colder" in result.lower()

    def test_autumn_october(self):
        """Test autumn advice for October."""
        with patch("aareguru_mcp.helpers.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 10, 15)
            result = _get_seasonal_advice()
            assert "Autumn" in result


class TestSafetyWarning:
    """Test _check_safety_warning for all flow levels."""

    def test_none_flow(self):
        """Test with None flow returns None."""
        result = _check_safety_warning(None)
        assert result is None

    def test_safe_flow_no_warning(self):
        """Test flow below threshold returns None."""
        result = _check_safety_warning(100.0, threshold=220)
        assert result is None

    def test_elevated_flow_caution(self):
        """Test elevated flow (above threshold but below 300) returns CAUTION."""
        result = _check_safety_warning(250.0, threshold=220)
        assert result is not None
        assert "CAUTION" in result

    def test_danger_flow(self):
        """Test dangerous flow (300-430) returns DANGER."""
        result = _check_safety_warning(350.0)
        assert result is not None
        assert "DANGER" in result
        assert "NOT recommended" in result

    def test_extreme_danger_flow(self):
        """Test extreme danger flow (>430) returns EXTREME DANGER."""
        result = _check_safety_warning(500.0)
        assert result is not None
        assert "EXTREME DANGER" in result
        assert "life-threatening" in result

    def test_default_threshold(self):
        """Test that None threshold defaults to 220."""
        result = _check_safety_warning(250.0, threshold=None)
        assert result is not None
        assert "CAUTION" in result


class TestSwissGermanExplanation:
    """Test _get_swiss_german_explanation for all phrases."""

    def test_none_text_returns_none(self):
        """Test with None text returns None."""
        result = _get_swiss_german_explanation(None)
        assert result is None

    def test_empty_text_returns_none(self):
        """Test with empty text returns None."""
        result = _get_swiss_german_explanation("")
        assert result is None

    def test_geil_aber_chli_chalt(self):
        """Test 'geil aber chli chalt' phrase."""
        result = _get_swiss_german_explanation("geil aber chli chalt")
        assert result is not None
        assert "Awesome" in result

    def test_schoen_warm(self):
        """Test 'schön warm' phrase."""
        result = _get_swiss_german_explanation("schön warm")
        assert result is not None
        assert "warm" in result.lower()

    def test_arschkalt(self):
        """Test 'arschkalt' phrase."""
        result = _get_swiss_german_explanation("arschkalt")
        assert result is not None
        assert "Freezing" in result

    def test_perfekt(self):
        """Test 'perfekt' phrase."""
        result = _get_swiss_german_explanation("perfekt")
        assert result is not None
        assert "Perfect" in result

    def test_chli_chalt(self):
        """Test 'chli chalt' phrase."""
        result = _get_swiss_german_explanation("chli chalt")
        assert result is not None
        assert "cold" in result.lower()

    def test_brrr(self):
        """Test 'brrr' phrase."""
        result = _get_swiss_german_explanation("brrr")
        assert result is not None
        assert "cold" in result.lower()

    def test_unknown_phrase_returns_none(self):
        """Test unknown phrase returns None."""
        result = _get_swiss_german_explanation("something random")
        assert result is None

    def test_case_insensitive(self):
        """Test matching is case insensitive."""
        result = _get_swiss_german_explanation("GEIL ABER CHLI CHALT")
        assert result is not None


class TestSafetyAssessment:
    """Test _get_safety_assessment for all flow levels."""

    def test_none_flow(self):
        """Test with None flow returns Unknown."""
        assessment, level = _get_safety_assessment(None)
        assert "Unknown" in assessment
        assert level == 0

    def test_safe_flow_under_100(self):
        """Test safe flow (<100) returns Safe, level 1."""
        assessment, level = _get_safety_assessment(50.0)
        assert "Safe" in assessment
        assert level == 1

    def test_moderate_flow(self):
        """Test moderate flow (100-threshold) returns Moderate, level 2."""
        assessment, level = _get_safety_assessment(150.0, threshold=220)
        assert "Moderate" in assessment
        assert level == 2

    def test_elevated_flow(self):
        """Test elevated flow (threshold-300) returns Elevated, level 3."""
        assessment, level = _get_safety_assessment(250.0, threshold=220)
        assert "Elevated" in assessment
        assert level == 3

    def test_high_flow(self):
        """Test high flow (300-430) returns High/dangerous, level 4."""
        assessment, level = _get_safety_assessment(350.0)
        assert "High" in assessment or "dangerous" in assessment.lower()
        assert level == 4

    def test_very_high_flow(self):
        """Test very high flow (>430) returns Very high/extremely, level 5."""
        assessment, level = _get_safety_assessment(500.0)
        assert "Very high" in assessment or "extremely" in assessment.lower()
        assert level == 5
