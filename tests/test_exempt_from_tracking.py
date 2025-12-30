"""Tests for exempt_from_tracking parameter behavior.

This module tests that LMPs with exempt_from_tracking=True return consistent
values (just the result, not a 3-tuple) matching the behavior when
exempt_from_tracking=False.

Fixes: https://github.com/MadcowD/ell/issues/394
"""

import pytest

import ell
from ell.lmp.function import function as ell_function


class TestExemptFromTrackingReturnValue:
    """Test that exempt_from_tracking doesn't change return value structure."""

    def test_tool_exempt_from_tracking_returns_result_not_tuple(self):
        """Test @ell.tool with exempt_from_tracking=True returns result, not 3-tuple."""

        @ell.tool(exempt_from_tracking=True)
        def test_tool(x: int) -> str:
            """A test tool."""
            return f"result: {x}"

        result = test_tool(42)

        # Should return a string, not a tuple
        assert isinstance(result, str), (
            f"Expected str, got {type(result).__name__}. "
            f"exempt_from_tracking=True should not return a 3-tuple."
        )
        assert result == "result: 42"

    def test_tool_exempt_from_tracking_false_with_tracking_disabled(self):
        """Test @ell.tool with exempt_from_tracking=False also returns result when no store."""
        # When there's no store configured, even non-exempt tools should return just the result

        @ell.tool(exempt_from_tracking=False)
        def test_tool_tracked(x: int) -> str:
            """A test tool."""
            return f"tracked result: {x}"

        result = test_tool_tracked(42)

        # Should return a string, not a tuple (when no store is configured)
        assert isinstance(result, str), (
            f"Expected str, got {type(result).__name__}."
        )
        assert result == "tracked result: 42"

    def test_function_exempt_from_tracking_returns_result_not_tuple(self):
        """Test @ell.function with exempt_from_tracking=True returns result, not 3-tuple."""

        @ell_function(exempt_from_tracking=True)
        def test_fn(x: int) -> int:
            return x * 2

        result = test_fn(21)

        # Should return an int, not a tuple
        assert isinstance(result, int), (
            f"Expected int, got {type(result).__name__}. "
            f"exempt_from_tracking=True should not return a 3-tuple."
        )
        assert result == 42


class TestExemptFromTrackingAttributes:
    """Test that exempt_from_tracking attribute is properly set."""

    def test_tool_has_exempt_attribute(self):
        """Test @ell.tool sets __ell_exempt_from_tracking attribute."""

        @ell.tool(exempt_from_tracking=True)
        def test_tool(x: int) -> str:
            """Test tool."""
            return str(x)

        # Use getattr to avoid Python name mangling issues
        assert hasattr(test_tool, '_TestExemptFromTrackingAttributes__ell_exempt_from_tracking') or \
               getattr(test_tool, '__ell_exempt_from_tracking', None) is True, \
               "exempt_from_tracking attribute should be True"

    def test_function_has_exempt_attribute(self):
        """Test @ell.function sets __ell_exempt_from_tracking attribute."""

        @ell_function(exempt_from_tracking=True)
        def test_fn():
            pass

        # Use getattr to avoid Python name mangling issues
        assert getattr(test_fn, '__ell_exempt_from_tracking', None) is True, \
               "exempt_from_tracking attribute should be True"


class TestToolReturnValueConsistency:
    """Test that tool return values are consistent."""

    def test_tool_returns_equivalent_value_regardless_of_exempt(self):
        """Both exempt and non-exempt tools should return equivalent values."""

        @ell.tool(exempt_from_tracking=True)
        def exempt_tool(x: int) -> str:
            """Exempt tool."""
            return f"value: {x}"

        @ell.tool(exempt_from_tracking=False)
        def tracked_tool(x: int) -> str:
            """Tracked tool."""
            return f"value: {x}"

        exempt_result = exempt_tool(1)
        tracked_result = tracked_tool(1)

        # Both should return string-like values (str or _lstr)
        # The important thing is neither returns a tuple
        assert not isinstance(exempt_result, tuple), (
            f"exempt_from_tracking=True returned a tuple: {exempt_result}"
        )
        assert not isinstance(tracked_result, tuple), (
            f"exempt_from_tracking=False returned a tuple: {tracked_result}"
        )
        # Values should be equal when compared as strings
        assert str(exempt_result) == str(tracked_result), (
            f"Values don't match: {exempt_result!r} vs {tracked_result!r}"
        )

    def test_tool_with_complex_return(self):
        """Test tool with dict return value."""

        @ell.tool(exempt_from_tracking=True)
        def dict_tool(x: int) -> dict:
            """Returns a dict."""
            return {"value": x, "doubled": x * 2}

        result = dict_tool(5)

        # Should return a dict, not a tuple
        assert isinstance(result, dict), (
            f"Expected dict, got {type(result).__name__}."
        )
        assert result == {"value": 5, "doubled": 10}
