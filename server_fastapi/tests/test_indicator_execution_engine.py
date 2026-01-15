"""
Tests for Indicator Execution Engine
"""

import pytest

from server_fastapi.services.indicator_execution_engine import (
    IndicatorExecutionEngine,
    IndicatorExecutionError,
)


class TestIndicatorExecutionEngine:
    """Tests for IndicatorExecutionEngine"""

    @pytest.fixture
    def engine(self):
        """Create execution engine instance"""
        return IndicatorExecutionEngine()

    def test_validate_code_safe(self, engine):
        """Test validating safe code"""
        code = """
def calculate_rsi(data, period=14):
    return 50.0

values = [calculate_rsi(df, 14)]
"""

        result = engine.validate_code(code)
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_code_dangerous_function(self, engine):
        """Test validating code with dangerous function"""
        code = """
import os
os.system("rm -rf /")
"""

        result = engine.validate_code(code)
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert any("os" in issue.lower() for issue in result["issues"])

    def test_validate_code_eval(self, engine):
        """Test validating code with eval"""
        code = """
result = eval("__import__('os').system('ls')")
"""

        result = engine.validate_code(code)
        assert result["valid"] is False
        assert any("eval" in issue.lower() for issue in result["issues"])

    def test_validate_code_file_operation(self, engine):
        """Test validating code with file operation"""
        code = """
f = open("/etc/passwd", "r")
content = f.read()
"""

        result = engine.validate_code(code)
        assert result["valid"] is False
        assert any(
            "file" in issue.lower() or "open" in issue.lower()
            for issue in result["issues"]
        )

    def test_execute_indicator_simple(self, engine):
        """Test executing a simple indicator"""
        code = """
values = [50.0]
"""

        market_data = [
            {"open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000},
        ]

        result = engine.execute_indicator(code, market_data)

        assert "values" in result
        assert result["values"] == [50.0]

    def test_execute_indicator_with_calculation(self, engine):
        """Test executing indicator with calculation"""
        code = """
import numpy as np
values = [np.mean([100, 105, 99, 103])]
"""

        market_data = [
            {"open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000},
        ]

        result = engine.execute_indicator(code, market_data)

        assert "values" in result
        assert len(result["values"]) > 0

    def test_execute_indicator_with_parameters(self, engine):
        """Test executing indicator with parameters"""
        code = """
period = parameters.get('period', 14)
values = [period * 2]
"""

        market_data = [
            {"open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000},
        ]

        result = engine.execute_indicator(code, market_data, parameters={"period": 20})

        assert "values" in result
        assert result["values"] == [40]  # 20 * 2

    def test_execute_indicator_timeout(self, engine):
        """Test that indicator execution times out"""
        code = """
import time
time.sleep(10)  # Sleep longer than timeout
values = [50.0]
"""

        market_data = [
            {"open": 100, "high": 105, "low": 99, "close": 103, "volume": 1000},
        ]

        with pytest.raises(IndicatorExecutionError) as exc_info:
            engine.execute_indicator(code, market_data)

        assert "timeout" in str(exc_info.value).lower()

    def test_execute_indicator_syntax_error(self, engine):
        """Test handling syntax errors"""
        code = """
def calculate_rsi(data, period=14
    return 50.0
"""


        result = engine.validate_code(code)
        assert result["valid"] is False
        assert len(result["issues"]) > 0
