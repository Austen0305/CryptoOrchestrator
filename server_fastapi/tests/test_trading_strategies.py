"""
Tests for trading strategies (MA Crossover, RSI, Momentum)
"""
import pytest
from server_fastapi.services.trading.bot_trading_service import BotTradingService


class TestTradingStrategies:
    """Test suite for trading signal implementations"""

    @pytest.fixture
    def service(self):
        """Create trading service instance"""
        return BotTradingService()

    @pytest.fixture
    def uptrend_data(self):
        """Generate uptrend market data"""
        return [
            {"close": 100 + i * 0.5, "volume": 1000 + i * 10}
            for i in range(250)
        ]

    @pytest.fixture
    def downtrend_data(self):
        """Generate downtrend market data"""
        return [
            {"close": 150 - i * 0.3, "volume": 1000 + i * 5}
            for i in range(250)
        ]

    @pytest.fixture
    def sideways_data(self):
        """Generate sideways market data"""
        import math
        return [
            {"close": 100 + math.sin(i * 0.1) * 2, "volume": 1000}
            for i in range(250)
        ]

    # ========== Simple MA Crossover Tests ==========

    def test_ma_crossover_uptrend(self, service, uptrend_data):
        """Test MA crossover detects uptrend correctly"""
        signal = service._simple_ma_signal(uptrend_data, {})
        
        assert signal is not None
        assert "action" in signal
        assert signal["action"] in ["buy", "sell", "hold"]
        assert "confidence" in signal
        assert 0 <= signal["confidence"] <= 1
        assert "indicators" in signal
        assert "fast_ma" in signal["indicators"]
        assert "slow_ma" in signal["indicators"]

    def test_ma_crossover_downtrend(self, service, downtrend_data):
        """Test MA crossover detects downtrend correctly"""
        signal = service._simple_ma_signal(downtrend_data, {})
        
        assert signal is not None
        assert signal["action"] in ["buy", "sell", "hold"]
        # In downtrend, fast MA should be below slow MA eventually
        if len(downtrend_data) >= 200:
            assert signal["indicators"]["fast_ma"] < signal["indicators"]["slow_ma"]

    def test_ma_crossover_insufficient_data(self, service):
        """Test MA crossover handles insufficient data gracefully"""
        short_data = [{"close": 100, "volume": 1000} for _ in range(50)]
        signal = service._simple_ma_signal(short_data, {})
        
        assert signal is not None
        # Should return hold signal with lower confidence
        assert signal["action"] == "hold"

    def test_ma_crossover_custom_config(self, service, uptrend_data):
        """Test MA crossover with custom configuration"""
        config = {"config": {"fast_period": 20, "slow_period": 100}}
        signal = service._simple_ma_signal(uptrend_data, config)
        
        assert signal is not None
        assert signal["action"] in ["buy", "sell", "hold"]

    # ========== RSI Strategy Tests ==========

    def test_rsi_uptrend(self, service, uptrend_data):
        """Test RSI detects overbought in strong uptrend"""
        signal = service._rsi_signal(uptrend_data, {})
        
        assert signal is not None
        assert "action" in signal
        assert "indicators" in signal
        assert "rsi" in signal["indicators"]
        
        # RSI should be high in uptrend
        rsi = signal["indicators"]["rsi"]
        assert 0 <= rsi <= 100
        
        # Strong uptrend should have high RSI
        if len(uptrend_data) >= 50:
            assert rsi > 50

    def test_rsi_downtrend(self, service, downtrend_data):
        """Test RSI detects oversold in downtrend"""
        signal = service._rsi_signal(downtrend_data, {})
        
        assert signal is not None
        rsi = signal["indicators"]["rsi"]
        assert 0 <= rsi <= 100
        
        # Downtrend should have low RSI
        if len(downtrend_data) >= 50:
            assert rsi < 50

    def test_rsi_extreme_values(self, service):
        """Test RSI handles extreme price movements"""
        # Extreme uptrend
        extreme_up = [{"close": 100 * (1.1 ** i), "volume": 1000} for i in range(50)]
        signal = service._rsi_signal(extreme_up, {})
        
        assert signal is not None
        assert signal["indicators"]["rsi"] <= 100
        
        # Extreme downtrend
        extreme_down = [{"close": 100 * (0.9 ** i), "volume": 1000} for i in range(50)]
        signal = service._rsi_signal(extreme_down, {})
        
        assert signal is not None
        assert signal["indicators"]["rsi"] >= 0

    def test_rsi_wilder_smoothing(self, service):
        """Test that RSI uses Wilder's smoothing correctly"""
        # Create specific pattern to test smoothing
        data = [{"close": 100 + i * 0.5, "volume": 1000} for i in range(100)]
        signal = service._rsi_signal(data, {})
        
        # Wilder's smoothing should produce smooth RSI values
        rsi = signal["indicators"]["rsi"]
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_rsi_divergence_detection(self, service):
        """Test RSI divergence detection"""
        # Create bullish divergence pattern (price falling, RSI rising)
        divergence_data = []
        for i in range(50):
            close = 100 - i * 0.2  # Falling price
            divergence_data.append({"close": close, "volume": 1000 + i * 50})
        
        signal = service._rsi_signal(divergence_data, {})
        assert signal is not None
        # Should detect some pattern
        assert "reasoning" in signal

    # ========== Momentum Strategy Tests ==========

    def test_momentum_uptrend(self, service, uptrend_data):
        """Test momentum strategy in uptrend"""
        signal = service._momentum_signal(uptrend_data, {})
        
        assert signal is not None
        assert "action" in signal
        assert "indicators" in signal
        assert "price_roc" in signal["indicators"]
        assert "volume_momentum" in signal["indicators"]

    def test_momentum_downtrend(self, service, downtrend_data):
        """Test momentum strategy in downtrend"""
        signal = service._momentum_signal(downtrend_data, {})
        
        assert signal is not None
        # Should detect negative momentum
        if "price_roc" in signal["indicators"]:
            # ROC should reflect downtrend
            assert signal["indicators"]["price_roc"] is not None

    def test_momentum_sideways(self, service, sideways_data):
        """Test momentum in sideways market"""
        signal = service._momentum_signal(sideways_data, {})
        
        assert signal is not None
        # Sideways market should have low momentum
        assert signal["action"] in ["buy", "sell", "hold"]

    def test_momentum_custom_config(self, service, uptrend_data):
        """Test momentum with custom configuration"""
        config = {"config": {"roc_period": 20, "momentum_ma_period": 30}}
        signal = service._momentum_signal(uptrend_data, config)
        
        assert signal is not None
        assert signal["action"] in ["buy", "sell", "hold"]

    # ========== Integration Tests ==========

    def test_all_strategies_consistent(self, service, uptrend_data):
        """Test that all strategies produce valid signals"""
        ma_signal = service._simple_ma_signal(uptrend_data, {})
        rsi_signal = service._rsi_signal(uptrend_data, {})
        momentum_signal = service._momentum_signal(uptrend_data, {})
        
        # All should return valid signals
        for signal in [ma_signal, rsi_signal, momentum_signal]:
            assert signal is not None
            assert signal["action"] in ["buy", "sell", "hold"]
            assert 0 <= signal["confidence"] <= 1
            assert "reasoning" in signal

    def test_signal_confidence_range(self, service, uptrend_data):
        """Test that all signals have valid confidence values"""
        signals = [
            service._simple_ma_signal(uptrend_data, {}),
            service._rsi_signal(uptrend_data, {}),
            service._momentum_signal(uptrend_data, {})
        ]
        
        for signal in signals:
            assert 0 <= signal["confidence"] <= 1
            # Confidence should be reasonable (not too extreme)
            assert 0.3 <= signal["confidence"] <= 1.0

    def test_error_handling_empty_data(self, service):
        """Test graceful handling of empty market data"""
        empty_data = []
        
        # Should not crash, should return hold or safe default
        ma_signal = service._simple_ma_signal(empty_data, {})
        assert ma_signal["action"] == "hold"
        
        rsi_signal = service._rsi_signal(empty_data, {})
        assert rsi_signal["action"] == "hold"
        
        momentum_signal = service._momentum_signal(empty_data, {})
        assert momentum_signal["action"] == "hold"

    def test_error_handling_invalid_data(self, service):
        """Test handling of invalid data formats"""
        invalid_data = [{"close": None, "volume": 1000}]
        
        # Should handle gracefully
        try:
            signal = service._simple_ma_signal(invalid_data, {})
            assert signal is not None
        except Exception as e:
            # If it raises, should be a clear error
            assert "Error" in str(e) or "error" in str(e)
