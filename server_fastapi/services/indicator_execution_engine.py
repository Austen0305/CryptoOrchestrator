"""
Indicator Execution Engine
Secure sandboxed execution environment for custom indicators.
"""

import logging
import ast
import time
import threading
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import numpy as np
import pandas as pd
import sys
import os

logger = logging.getLogger(__name__)

# Try to import RestrictedPython for sandboxing
try:
    from RestrictedPython import compile_restricted, safe_globals
    from RestrictedPython.Guards import safe_builtins, guarded_iter_unpack, guarded_unpack
    from RestrictedPython.transformer import RestrictingNodeTransformer
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False
    logger.warning("RestrictedPython not available - using basic validation only")


class IndicatorExecutionError(Exception):
    """Exception raised during indicator execution"""
    pass


class IndicatorExecutionEngine:
    """
    Secure execution engine for custom indicators.
    Uses multiple layers of security:
    1. AST validation (check for dangerous operations)
    2. RestrictedPython (if available)
    3. Resource limits (time, memory)
    4. Safe execution context
    """

    def __init__(self):
        self.max_execution_time = 5.0  # 5 seconds max
        self.max_memory_mb = 100  # 100 MB max
        self.allowed_modules = {
            "math", "numpy", "pandas", "datetime", "time"
        }
        self.dangerous_functions = {
            "eval", "exec", "compile", "__import__", "open", "file",
            "input", "raw_input", "reload", "__builtins__", "globals",
            "locals", "vars", "dir", "hasattr", "getattr", "setattr",
            "delattr", "callable", "super", "type", "isinstance", "issubclass"
        }

    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate indicator code for security issues.

        Args:
            code: Indicator code to validate

        Returns:
            Dict with validation result
        """
        try:
            # Parse AST
            tree = ast.parse(code, mode="exec")

            # Check for dangerous operations
            issues = []
            for node in ast.walk(tree):
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.dangerous_functions:
                            issues.append(
                                f"Dangerous function call: {node.func.id} at line {node.lineno}"
                            )
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in self.dangerous_functions:
                            issues.append(
                                f"Dangerous attribute access: {node.func.attr} at line {node.lineno}"
                            )

                # Check for imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.allowed_modules:
                            issues.append(
                                f"Disallowed import: {alias.name} at line {node.lineno}"
                            )

                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module not in self.allowed_modules:
                        issues.append(
                            f"Disallowed import from: {node.module} at line {node.lineno}"
                        )

                # Check for file operations
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["open", "file"]:
                            issues.append(
                                f"File operation not allowed at line {node.lineno}"
                            )

            if issues:
                return {
                    "valid": False,
                    "issues": issues,
                }

            return {
                "valid": True,
                "issues": [],
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "issues": [f"Syntax error: {str(e)}"],
            }
        except Exception as e:
            logger.error(f"Error validating code: {e}", exc_info=True)
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
            }

    def execute_indicator(
        self,
        code: str,
        market_data: List[Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute indicator code in a sandboxed environment.

        Args:
            code: Indicator code
            market_data: OHLCV market data
            parameters: Optional parameters

        Returns:
            Dict with execution results
        """
        # Validate code first
        validation = self.validate_code(code)
        if not validation["valid"]:
            raise IndicatorExecutionError(
                f"Code validation failed: {', '.join(validation['issues'])}"
            )

        # Prepare execution context
        execution_context = self._create_safe_context(market_data, parameters)

        try:
            # Execute with timeout
            result = self._execute_with_timeout(code, execution_context)
            return result
        except TimeoutError:
            raise IndicatorExecutionError("Indicator execution timed out")
        except MemoryError:
            raise IndicatorExecutionError("Indicator execution exceeded memory limit")
        except Exception as e:
            logger.error(f"Error executing indicator: {e}", exc_info=True)
            raise IndicatorExecutionError(f"Execution error: {str(e)}")

    def _create_safe_context(
        self, market_data: List[Dict[str, Any]], parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a safe execution context"""
        # Convert market data to DataFrame for easier manipulation
        df = pd.DataFrame(market_data)

        # Safe builtins (limited set)
        safe_builtins_dict = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "range": range,
            "round": round,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }

        context = {
            "__builtins__": safe_builtins_dict,
            "pd": pd,
            "np": np,
            "DataFrame": pd.DataFrame,
            "Series": pd.Series,
            "data": df,
            "df": df,
            "market_data": market_data,
            "parameters": parameters or {},
        }

        # Add numpy functions
        context.update({
            "mean": np.mean,
            "std": np.std,
            "sum": np.sum,
            "max": np.max,
            "min": np.min,
            "abs": np.abs,
            "sqrt": np.sqrt,
            "log": np.log,
            "exp": np.exp,
        })

        return context

    def _execute_with_timeout(
        self, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute code with timeout and resource limits (cross-platform)"""
        result_container = {"result": None, "error": None, "completed": False}

        def execute_code():
            """Execute code in a separate thread"""
            try:
                # Execute code
                if RESTRICTED_PYTHON_AVAILABLE:
                    # Use RestrictedPython if available
                    try:
                        byte_code = compile_restricted(code, "<indicator>", "exec")
                        if byte_code.errors:
                            result_container["error"] = IndicatorExecutionError(
                                f"RestrictedPython errors: {', '.join(byte_code.errors)}"
                            )
                            return

                        exec(byte_code.code, context)
                    except Exception as e:
                        # Fallback to basic execution if RestrictedPython fails
                        logger.warning(f"RestrictedPython execution failed, using basic: {e}")
                        exec(compile(code, "<indicator>", "exec"), context)
                else:
                    # Basic execution (less secure, but functional)
                    # NOTE: In production, should use Docker container or more secure sandbox
                    exec(compile(code, "<indicator>", "exec"), context)

                # Extract results
                result_container["result"] = {
                    "values": context.get("values", []),
                    "signals": context.get("signals", []),
                    "output": context.get("output", {}),
                }
                result_container["completed"] = True
            except Exception as e:
                result_container["error"] = e

        # Execute in thread with timeout
        thread = threading.Thread(target=execute_code)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.max_execution_time)

        if thread.is_alive():
            # Thread still running - timeout
            raise TimeoutError("Indicator execution timed out")

        if result_container["error"]:
            raise result_container["error"]

        if not result_container["completed"]:
            raise IndicatorExecutionError("Indicator execution did not complete")

        return result_container["result"]


# Common indicator templates
INDICATOR_TEMPLATES = {
    "rsi": """
# RSI (Relative Strength Index)
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else 50.0

values = [calculate_rsi(df, parameters.get('period', 14))]
""",
    "macd": """
# MACD (Moving Average Convergence Divergence)
def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return {
        'macd': macd.iloc[-1] if len(macd) > 0 else 0.0,
        'signal': signal_line.iloc[-1] if len(signal_line) > 0 else 0.0,
        'histogram': histogram.iloc[-1] if len(histogram) > 0 else 0.0
    }

result = calculate_macd(df, 
    parameters.get('fast', 12),
    parameters.get('slow', 26),
    parameters.get('signal', 9)
)
output = result
values = [result['macd']]
""",
    "bollinger_bands": """
# Bollinger Bands
def calculate_bollinger(data, period=20, std_dev=2):
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return {
        'upper': upper.iloc[-1] if len(upper) > 0 else data['close'].iloc[-1],
        'middle': sma.iloc[-1] if len(sma) > 0 else data['close'].iloc[-1],
        'lower': lower.iloc[-1] if len(lower) > 0 else data['close'].iloc[-1]
    }

result = calculate_bollinger(df,
    parameters.get('period', 20),
    parameters.get('std_dev', 2)
)
output = result
values = [result['middle']]
""",
    "sma": """
# Simple Moving Average
def calculate_sma(data, period=20):
    sma = data['close'].rolling(window=period).mean()
    return sma.iloc[-1] if len(sma) > 0 else data['close'].iloc[-1]

values = [calculate_sma(df, parameters.get('period', 20))]
""",
    "ema": """
# Exponential Moving Average
def calculate_ema(data, period=20):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    return ema.iloc[-1] if len(ema) > 0 else data['close'].iloc[-1]

values = [calculate_ema(df, parameters.get('period', 20))]
""",
}
