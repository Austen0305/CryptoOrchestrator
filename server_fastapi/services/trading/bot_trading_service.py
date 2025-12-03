"""
Bot trading service for trading cycle execution
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.ml.enhanced_ml_engine import EnhancedMLEngine, MLPrediction
from ...services.ml.ensemble_engine import EnsembleEngine, EnsemblePrediction
from ...services.ml.neural_network_engine import NeuralNetworkEngine
from ...services.ml.adaptive_learning import adaptive_learning_service
from ...services.advanced_risk_manager import AdvancedRiskManager, RiskProfile
from .bot_control_service import BotControlService
from .bot_monitoring_service import BotMonitoringService
from .smart_bot_engine import SmartBotEngine, MarketSignal

logger = logging.getLogger(__name__)


class BotTradingService:
    """Service for executing trading cycles and managing bot trading logic"""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.control_service = BotControlService(session=session)
        self.monitoring_service = BotMonitoringService(session=session)

        # Initialize ML engines
        self.ml_engines = {
            'ml_enhanced': EnhancedMLEngine(),
            'ensemble': EnsembleEngine(),
            'neural_network': NeuralNetworkEngine()
        }

        # Initialize smart bot engine
        self.smart_engine = SmartBotEngine()

        # Use singleton instance for risk manager
        self.risk_manager = AdvancedRiskManager.get_instance()
        
        # Initialize trading safety service
        from .trading_safety_service import get_trading_safety_service
        self.safety_service = get_trading_safety_service()

    async def execute_trading_cycle(self, bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one complete trading cycle for a bot"""
        try:
            bot_id = bot_config['id']
            user_id = bot_config['user_id']
            strategy = bot_config.get('strategy', 'simple_ma')

            logger.info(f"Executing trading cycle for bot {bot_id} ({strategy})")

            # Check if bot is still active before proceeding
            if not await self.control_service.is_bot_active(bot_id, user_id):
                logger.info(f"Bot {bot_id} is no longer active, skipping cycle")
                return {"action": "skipped", "reason": "bot_inactive"}

            # Validate start conditions
            validation = await self.monitoring_service.validate_bot_start_conditions(bot_id, user_id)
            if not validation["can_start"]:
                logger.warning(f"Bot {bot_id} cannot proceed with trading: {validation['blockers']}")
                return {"action": "blocked", "reason": "safety_validation_failed", "details": validation}

            # Get market data (mock implementation)
            market_data = await self._get_market_data(bot_config)

            # Get trading signal
            signal = await self._get_trading_signal(strategy, market_data, bot_config)

            if not signal or signal['action'] not in ['buy', 'sell']:
                logger.info(f"No trading action for bot {bot_id}")
                return {"action": "hold", "signal": signal}

            # Calculate risk profile
            risk_profile = await self._calculate_risk_profile(market_data, bot_config)

            # Prepare trade details
            trade_details = self._prepare_trade_details(bot_config, signal, market_data, risk_profile)
            
            # Add trading mode to trade details
            trade_details['mode'] = bot_config.get('mode', 'paper')
            trade_details['exchange'] = bot_config.get('exchange', 'binance')

            # Validate trade with existing safety system (backward compatibility)
            from ..trading.safe_trading_system import SafeTradingSystem
            safe_system = SafeTradingSystem()
            validation = await safe_system.validate_trade(trade_details)

            if not validation["valid"]:
                logger.warning(f"Trade blocked by safety system for bot {bot_id}: {validation['errors']}")
                return {"action": "blocked", "reason": "safety_validation_failed", "details": validation}
            
            # Additional validation with new trading safety service
            # Get account balance and positions (mock for now, replace with real data)
            account_balance = await self._get_account_balance(user_id, trade_details['exchange'])
            current_positions = await self._get_current_positions(user_id, trade_details['exchange'])
            
            # Validate with trading safety service
            safety_result = self.safety_service.validate_trade(
                symbol=trade_details['symbol'],
                side=trade_details['action'],
                quantity=trade_details['quantity'],
                price=trade_details['price'],
                account_balance=account_balance,
                current_positions=current_positions
            )
            
            if not safety_result['valid']:
                logger.warning(f"Trade blocked by trading safety service for bot {bot_id}: {safety_result['reason']}")
                return {
                    "action": "blocked",
                    "reason": "safety_limits_exceeded",
                    "details": safety_result
                }
            
            # Apply any adjustments from safety service
            if safety_result.get('adjustments'):
                original_qty = trade_details['quantity']
                trade_details['quantity'] = safety_result['adjustments']['adjusted_quantity']
                logger.info(
                    f"Position size adjusted by safety service for bot {bot_id}: "
                    f"{original_qty:.6f} -> {trade_details['quantity']:.6f}"
                )

            # Execute trade
            trade_result = await self._execute_trade(trade_details)

            # Record trade result with both systems
            await safe_system.record_trade_result(trade_details, trade_result.get('pnl', 0.0))
            
            # Record with new safety service
            if trade_result.get('success'):
                # Generate trade ID if not present
                trade_id = trade_result.get('order_id') or f"{bot_id}_{datetime.now().timestamp()}"
                
                # Calculate P&L (for now, 0 until position is closed)
                pnl = trade_result.get('pnl', 0.0)
                
                # Record trade result
                self.safety_service.record_trade_result(
                    trade_id=str(trade_id),
                    pnl=pnl,
                    symbol=trade_details['symbol'],
                    side=trade_details['action'],
                    quantity=trade_details['quantity'],
                    price=trade_result.get('executed_price', trade_details['price'])
                )
                
                # Automatically create stop-loss and take-profit orders
                position_id = f"pos_{trade_id}"
                executed_price = trade_result.get('executed_price', trade_details['price'])
                
                try:
                    from .sl_tp_service import get_sl_tp_service
                    sl_tp_service = get_sl_tp_service()
                    
                    # Get stop-loss and take-profit percentages from risk profile
                    stop_loss_pct = trade_details.get('risk_profile', {}).get('stop_loss_pct', 0.02)  # 2% default
                    take_profit_pct = trade_details.get('risk_profile', {}).get('take_profit_pct', 0.05)  # 5% default
                    
                    # Create stop-loss order
                    sl_order = sl_tp_service.create_stop_loss(
                        position_id=position_id,
                        symbol=trade_details['symbol'],
                        side=trade_details['action'],
                        quantity=trade_details['quantity'],
                        entry_price=executed_price,
                        stop_loss_pct=stop_loss_pct,
                        user_id=str(user_id),
                        bot_id=str(bot_id)
                    )
                    
                    logger.info(
                        f"Auto-created stop-loss for position {position_id}: "
                        f"Entry ${executed_price:.2f}, Stop ${sl_order['trigger_price']:.2f}"
                    )
                    
                    # Create take-profit order
                    tp_order = sl_tp_service.create_take_profit(
                        position_id=position_id,
                        symbol=trade_details['symbol'],
                        side=trade_details['action'],
                        quantity=trade_details['quantity'],
                        entry_price=executed_price,
                        take_profit_pct=take_profit_pct,
                        user_id=str(user_id),
                        bot_id=str(bot_id)
                    )
                    
                    logger.info(
                        f"Auto-created take-profit for position {position_id}: "
                        f"Entry ${executed_price:.2f}, Target ${tp_order['trigger_price']:.2f}"
                    )
                    
                    # Store order IDs in trade result for reference
                    trade_result['stop_loss_order_id'] = sl_order['order_id']
                    trade_result['take_profit_order_id'] = tp_order['order_id']
                    
                except Exception as e:
                    logger.error(f"Failed to create SL/TP orders for position {position_id}: {e}")
                    # Don't fail the trade, just log the error
                
                logger.info(f"Trade result recorded with safety service for bot {bot_id}")

            # Adaptive Learning: Learn from trade
            try:
                trade_record = {
                    "id": trade_result.get('trade_id', f"{bot_id}_{int(datetime.now().timestamp())}"),
                    "pnl": trade_result.get('pnl', 0.0),
                    "symbol": bot_config.get('tradingPair', 'UNKNOWN'),
                }
                adaptive_learning_service.analyze_trade_pattern(trade_record, market_data)
                logger.info(f"Bot {bot_id} trade pattern analyzed for adaptive learning")
            except Exception as learn_error:
                logger.warning(f"Error in adaptive learning for bot {bot_id}: {learn_error}")

            logger.info(f"Bot {bot_id} executed {signal['action']} trade")
            return {
                "action": signal['action'],
                "trade_details": trade_details,
                "trade_result": trade_result,
                "signal": signal
            }

        except Exception as e:
            logger.error(f"Error executing trading cycle for bot {bot_config['id']}: {str(e)}")
            return {"action": "error", "error": str(e)}

    async def run_bot_loop(self, bot_id: str, user_id: int):
        """Background task to run bot trading loop"""
        try:
            logger.info(f"Starting trading loop for bot {bot_id} (user {user_id})")

            while True:
                try:
                    # Check if bot is still active
                    bot_status = await self.control_service.get_bot_status(bot_id, user_id)
                    if not bot_status or not bot_status.get('active', False):
                        logger.info(f"Bot {bot_id} is no longer active, stopping loop")
                        break

                    # Execute trading cycle
                    result = await self.execute_trading_cycle(bot_status)

                    # Log cycle result
                    if result['action'] in ['buy', 'sell']:
                        logger.info(f"Bot {bot_id} cycle result: {result['action']}")
                    elif result['action'] == 'error':
                        logger.error(f"Bot {bot_id} cycle error: {result.get('error', 'unknown')}")

                except Exception as e:
                    logger.error(f"Error in trading cycle for bot {bot_id}: {str(e)}")
                    # Don't break loop for individual cycle errors

                # Wait before next cycle (5 minutes)
                await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Critical error in bot loop {bot_id}: {str(e)}")
            # Ensure bot is marked as inactive on critical error
            try:
                await self.control_service.update_bot_status(bot_id, user_id, False, 'error')
            except Exception as stop_error:
                logger.error(f"Error stopping bot {bot_id} after critical error: {stop_error}")

    async def _get_market_data(self, bot_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get real market data from exchange APIs"""
        try:
            # Get exchange name from bot config
            exchange_name = bot_config.get('exchange', 'binance')
            symbol = bot_config.get('tradingPair') or bot_config.get('symbol', 'BTC/USDT')
            timeframe = bot_config.get('timeframe', '1h')
            limit = bot_config.get('candle_limit', 100)
            
            # Import exchange service and key service
            from ..exchange_service import ExchangeService
            from ..auth.exchange_key_service import exchange_key_service
            
            # Get user's API keys for this exchange
            user_id_str = str(bot_config.get('user_id', ''))
            api_key_data = await exchange_key_service.get_api_key(
                user_id_str, exchange_name, include_secrets=True
            )
            
            if not api_key_data or not api_key_data.get('is_validated', False):
                logger.warning(f"No validated API keys for {exchange_name}, cannot fetch real market data")
                raise ValueError(f"No validated API keys for {exchange_name}")
            
            # Create exchange service with user's API keys
            exchange_service = ExchangeService(
                name=exchange_name,
                use_mock=False,  # Force real mode
                api_key=api_key_data.get('api_key'),
                api_secret=api_key_data.get('api_secret')
            )
            
            # Connect to exchange
            await exchange_service.connect()
            if not exchange_service.is_connected():
                raise ConnectionError(f"Failed to connect to {exchange_name}")
            
            # Fetch real OHLCV data
            ohlcv_data = await exchange_service.get_ohlcv(symbol, timeframe, limit)
            
            if not ohlcv_data:
                logger.warning(f"No market data returned for {symbol} on {exchange_name}")
                raise ValueError(f"No market data available for {symbol}")
            
            # Convert to expected format
            market_data = []
            for candle in ohlcv_data:
                if len(candle) >= 6:  # [timestamp, open, high, low, close, volume]
                    market_data.append({
                        "timestamp": int(candle[0]),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5])
                    })
            
            if not market_data:
                raise ValueError(f"Failed to parse market data for {symbol}")
            
            logger.info(f"Fetched {len(market_data)} candles for {symbol} from {exchange_name}")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}", exc_info=True)
            # In production, we should not fall back to mock data
            from ..config.settings import get_settings
            settings = get_settings()
            if settings.production_mode or settings.is_production:
                raise  # Re-raise in production - no mock fallback
            else:
                # Only allow mock fallback in development
                logger.warning("Falling back to mock data in development mode")
                return [{
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "open": 50000,
                    "high": 50200,
                    "low": 49900,
                    "close": 50100,
                    "volume": 1.5
                }]

    async def _get_trading_signal(self, strategy: str, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get trading signal based on strategy"""
        try:
            # Check if using smart adaptive strategy
            if strategy == 'smart_adaptive' or bot_config.get('config', {}).get('use_smart_engine', False):
                logger.info(f"Using SmartBotEngine for analysis")
                
                # Prepare market data for smart engine
                smart_data = self._prepare_smart_market_data(market_data, bot_config)
                
                # Get smart analysis
                signal: MarketSignal = await self.smart_engine.analyze_market(smart_data)
                
                confidence_threshold = bot_config.get('config', {}).get('confidence_threshold', 0.65)
                
                if signal.confidence >= confidence_threshold:
                    logger.info(
                        f"SmartEngine signal: {signal.action.upper()} "
                        f"(confidence: {signal.confidence:.2%}, risk: {signal.risk_score:.2f}, "
                        f"strength: {signal.strength:.2f})"
                    )
                    return {
                        "action": signal.action,
                        "confidence": signal.confidence,
                        "reasoning": ', '.join(signal.reasoning),
                        "risk_score": signal.risk_score,
                        "signal_strength": signal.strength,
                        "timestamp": signal.timestamp.isoformat()
                    }
                else:
                    logger.info(f"SmartEngine confidence too low: {signal.confidence:.2%}")
                    return {
                        "action": "hold",
                        "confidence": signal.confidence,
                        "reasoning": f"Confidence below threshold ({confidence_threshold:.2%})",
                        "risk_score": signal.risk_score
                    }
            
            if strategy in self.ml_engines:
                # ML-based strategies
                ml_engine = self.ml_engines[strategy]
                prediction = await ml_engine.predict(market_data)

                if prediction and hasattr(prediction, 'action'):
                    confidence_threshold = bot_config.get('config', {}).get('ml_config', {}).get('confidence_threshold', 0.6)

                    if prediction.confidence > confidence_threshold:
                        return {
                            "action": prediction.action,
                            "confidence": prediction.confidence,
                            "reasoning": getattr(prediction, 'reasoning', 'ML prediction')
                        }

            elif strategy == 'simple_ma':
                # Simple moving average crossover strategy
                return self._simple_ma_signal(market_data, bot_config)

            elif strategy == 'rsi':
                # RSI (Relative Strength Index) strategy
                return self._rsi_signal(market_data, bot_config)
            
            elif strategy == 'momentum':
                # Momentum-based strategy
                return self._momentum_signal(market_data, bot_config)

            # Default hold signal
            return {"action": "hold", "confidence": 0.5, "reasoning": "Unknown strategy - holding"}

        except Exception as e:
            logger.error(f"Error getting trading signal for strategy {strategy}: {str(e)}")
            return None
    
    def _prepare_smart_market_data(self, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare market data for smart bot engine"""
        import numpy as np
        
        # Extract OHLCV data
        candles = []
        for candle in market_data:
            candles.append({
                'timestamp': candle.get('timestamp'),
                'open': float(candle.get('open', 0)),
                'high': float(candle.get('high', 0)),
                'low': float(candle.get('low', 0)),
                'close': float(candle.get('close', 0)),
                'volume': float(candle.get('volume', 0))
            })
        
        # Generate synthetic orderbook if not present
        if candles:
            current_price = candles[-1]['close']
            orderbook = {
                'bids': [[current_price * 0.999, 10.0], [current_price * 0.998, 20.0]],
                'asks': [[current_price * 1.001, 10.0], [current_price * 1.002, 20.0]]
            }
        else:
            orderbook = {'bids': [], 'asks': []}
        
        return {
            'symbol': bot_config.get('symbol', 'BTC/USDT'),
            'candles': candles,
            'volume': [c['volume'] for c in candles],
            'orderbook': orderbook
        }

    def _simple_ma_signal(self, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple Moving Average Crossover strategy.
        Generates buy signal when fast MA (50) crosses above slow MA (200).
        Generates sell signal when fast MA (50) crosses below slow MA (200).
        Includes volume confirmation filter.
        """
        try:
            if len(market_data) < 200:
                logger.warning(f"Insufficient data for MA crossover: {len(market_data)} candles (need 200)")
                return {"action": "hold", "confidence": 0.3, "reasoning": "Insufficient data for MA analysis"}
            
            # Extract close prices and volumes
            closes = [float(candle['close']) for candle in market_data]
            volumes = [float(candle['volume']) for candle in market_data]
            
            # Calculate SMAs
            fast_period = bot_config.get('config', {}).get('fast_ma_period', 50)
            slow_period = bot_config.get('config', {}).get('slow_ma_period', 200)
            volume_period = bot_config.get('config', {}).get('volume_period', 20)
            
            # Calculate current and previous fast MA (50-period SMA)
            fast_ma_current = sum(closes[-fast_period:]) / fast_period
            fast_ma_prev = sum(closes[-(fast_period + 1):-1]) / fast_period
            
            # Calculate current and previous slow MA (200-period SMA)
            slow_ma_current = sum(closes[-slow_period:]) / slow_period
            slow_ma_prev = sum(closes[-(slow_period + 1):-1]) / slow_period
            
            # Calculate average volume for confirmation
            avg_volume = sum(volumes[-volume_period:]) / volume_period
            current_volume = volumes[-1]
            volume_confirmed = current_volume > avg_volume
            
            # Calculate momentum for confidence scoring
            momentum = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0
            
            # Determine signal
            action = "hold"
            confidence = 0.5
            reasoning = []
            
            # Bullish crossover: fast MA crosses above slow MA
            if fast_ma_prev <= slow_ma_prev and fast_ma_current > slow_ma_current:
                action = "buy"
                base_confidence = 0.7
                reasoning.append("Fast MA crossed above slow MA (golden cross)")
                
                # Boost confidence with volume confirmation
                if volume_confirmed:
                    base_confidence += 0.1
                    reasoning.append("Volume confirms the move")
                
                # Boost confidence with positive momentum
                if momentum > 0.02:
                    base_confidence += 0.1
                    reasoning.append(f"Strong positive momentum ({momentum:.2%})")
                
                confidence = min(base_confidence, 0.95)
                
            # Bearish crossover: fast MA crosses below slow MA
            elif fast_ma_prev >= slow_ma_prev and fast_ma_current < slow_ma_current:
                action = "sell"
                base_confidence = 0.7
                reasoning.append("Fast MA crossed below slow MA (death cross)")
                
                # Boost confidence with volume confirmation
                if volume_confirmed:
                    base_confidence += 0.1
                    reasoning.append("Volume confirms the move")
                
                # Boost confidence with negative momentum
                if momentum < -0.02:
                    base_confidence += 0.1
                    reasoning.append(f"Strong negative momentum ({momentum:.2%})")
                
                confidence = min(base_confidence, 0.95)
                
            else:
                # No crossover - trend following
                if fast_ma_current > slow_ma_current:
                    # Uptrend but no new crossover
                    reasoning.append("Uptrend: fast MA above slow MA")
                    if momentum > 0.01:
                        action = "buy"
                        confidence = 0.55 + (0.1 if volume_confirmed else 0)
                        reasoning.append("Continued upward momentum")
                else:
                    # Downtrend but no new crossover
                    reasoning.append("Downtrend: fast MA below slow MA")
                    if momentum < -0.01:
                        action = "sell"
                        confidence = 0.55 + (0.1 if volume_confirmed else 0)
                        reasoning.append("Continued downward momentum")
            
            logger.info(f"MA Signal: {action} with {confidence:.2%} confidence - {'; '.join(reasoning)}")
            
            return {
                "action": action,
                "confidence": confidence,
                "reasoning": "; ".join(reasoning),
                "indicators": {
                    "fast_ma": fast_ma_current,
                    "slow_ma": slow_ma_current,
                    "momentum": momentum,
                    "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 1.0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating MA signal: {e}", exc_info=True)
            return {"action": "hold", "confidence": 0.3, "reasoning": f"Error in MA calculation: {str(e)}"}

    def _rsi_signal(self, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        RSI (Relative Strength Index) trading strategy.
        Generates buy signal when RSI < 30 (oversold).
        Generates sell signal when RSI > 70 (overbought).
        Includes divergence detection and trend confirmation.
        """
        try:
            rsi_period = bot_config.get('config', {}).get('rsi_period', 14)
            oversold_threshold = bot_config.get('config', {}).get('rsi_oversold', 30)
            overbought_threshold = bot_config.get('config', {}).get('rsi_overbought', 70)
            
            if len(market_data) < rsi_period + 1:
                logger.warning(f"Insufficient data for RSI: {len(market_data)} candles (need {rsi_period + 1})")
                return {"action": "hold", "confidence": 0.3, "reasoning": "Insufficient data for RSI analysis"}
            
            # Extract close prices
            closes = [float(candle['close']) for candle in market_data]
            
            # Calculate RSI
            rsi = self._calculate_rsi(closes, rsi_period)
            
            if rsi is None:
                return {"action": "hold", "confidence": 0.3, "reasoning": "Unable to calculate RSI"}
            
            # Calculate RSI from previous period for divergence
            prev_rsi = self._calculate_rsi(closes[:-1], rsi_period)
            
            # Calculate price momentum for confirmation
            current_price = closes[-1]
            prev_price = closes[-5] if len(closes) >= 5 else closes[0]
            price_momentum = (current_price - prev_price) / prev_price
            
            action = "hold"
            confidence = 0.5
            reasoning = []
            
            # Oversold condition - potential buy
            if rsi < oversold_threshold:
                action = "buy"
                base_confidence = 0.65
                reasoning.append(f"RSI ({rsi:.1f}) indicates oversold condition")
                
                # Check for bullish divergence (price lower but RSI higher)
                if prev_rsi is not None and rsi > prev_rsi and price_momentum < 0:
                    base_confidence += 0.15
                    reasoning.append("Bullish divergence detected")
                
                # Deeper oversold = higher confidence
                if rsi < 20:
                    base_confidence += 0.1
                    reasoning.append("Extremely oversold")
                
                confidence = min(base_confidence, 0.95)
                
            # Overbought condition - potential sell
            elif rsi > overbought_threshold:
                action = "sell"
                base_confidence = 0.65
                reasoning.append(f"RSI ({rsi:.1f}) indicates overbought condition")
                
                # Check for bearish divergence (price higher but RSI lower)
                if prev_rsi is not None and rsi < prev_rsi and price_momentum > 0:
                    base_confidence += 0.15
                    reasoning.append("Bearish divergence detected")
                
                # More overbought = higher confidence
                if rsi > 80:
                    base_confidence += 0.1
                    reasoning.append("Extremely overbought")
                
                confidence = min(base_confidence, 0.95)
                
            else:
                # RSI in neutral zone
                reasoning.append(f"RSI ({rsi:.1f}) in neutral zone")
                
                # Check for emerging trends
                if prev_rsi is not None:
                    if rsi > prev_rsi and rsi > 50:
                        action = "buy"
                        confidence = 0.55
                        reasoning.append("RSI trending upward")
                    elif rsi < prev_rsi and rsi < 50:
                        action = "sell"
                        confidence = 0.55
                        reasoning.append("RSI trending downward")
            
            logger.info(f"RSI Signal: {action} with {confidence:.2%} confidence - RSI: {rsi:.1f}")
            
            return {
                "action": action,
                "confidence": confidence,
                "reasoning": "; ".join(reasoning),
                "indicators": {
                    "rsi": rsi,
                    "prev_rsi": prev_rsi,
                    "price_momentum": price_momentum
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating RSI signal: {e}", exc_info=True)
            return {"action": "hold", "confidence": 0.3, "reasoning": f"Error in RSI calculation: {str(e)}"}
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate RSI (Relative Strength Index) using Wilder's smoothing method.
        
        This implementation uses the standard RSI formula:
        1. Calculate price changes
        2. Separate gains and losses
        3. Use Wilder's Smoothed Moving Average (SMMA) for average gain/loss
        4. RS = Avg Gain / Avg Loss
        5. RSI = 100 - (100 / (1 + RS))
        
        Returns RSI value between 0 and 100.
        """
        if len(closes) < period + 1:
            return None
        
        # Calculate price changes
        changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        
        if len(changes) < period:
            return None
        
        # Separate gains and losses
        gains = [max(change, 0) for change in changes]
        losses = [abs(min(change, 0)) for change in changes]
        
        # Calculate initial SMA for first period
        first_avg_gain = sum(gains[:period]) / period
        first_avg_loss = sum(losses[:period]) / period
        
        # Apply Wilder's smoothing for remaining periods
        avg_gain = first_avg_gain
        avg_loss = first_avg_loss
        
        for i in range(period, len(changes)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _momentum_signal(self, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Momentum-based trading strategy.
        Calculates 12-period Rate of Change (ROC) for price and volume momentum.
        Generates signals based on momentum acceleration.
        """
        try:
            roc_period = bot_config.get('config', {}).get('roc_period', 12)
            ma_period = bot_config.get('config', {}).get('momentum_ma_period', 20)
            
            if len(market_data) < max(roc_period, ma_period) + 5:
                return {"action": "hold", "confidence": 0.3, "reasoning": "Insufficient data for momentum analysis"}
            
            closes = [float(candle['close']) for candle in market_data]
            volumes = [float(candle['volume']) for candle in market_data]
            
            # Calculate Price Rate of Change (ROC)
            current_price = closes[-1]
            prev_price = closes[-roc_period - 1]
            price_roc = ((current_price - prev_price) / prev_price) * 100
            
            # Calculate Volume momentum
            current_volume = volumes[-1]
            avg_volume = sum(volumes[-roc_period:]) / roc_period
            volume_momentum = (current_volume - avg_volume) / avg_volume if avg_volume > 0 else 0
            
            # Calculate acceleration (change in momentum)
            prev_price_for_prev_roc = closes[-roc_period - 2]
            price_at_prev_roc = closes[-2]
            prev_roc = ((price_at_prev_roc - prev_price_for_prev_roc) / prev_price_for_prev_roc) * 100
            acceleration = price_roc - prev_roc
            
            # Moving average filter
            ma = sum(closes[-ma_period:]) / ma_period
            above_ma = current_price > ma
            
            action = "hold"
            confidence = 0.5
            reasoning = []
            
            # Strong positive momentum with acceleration
            if price_roc > 2 and acceleration > 0:
                action = "buy"
                base_confidence = 0.6
                reasoning.append(f"Positive momentum ({price_roc:.1f}%)")
                
                if acceleration > 1:
                    base_confidence += 0.1
                    reasoning.append("Accelerating momentum")
                
                if volume_momentum > 0.5:
                    base_confidence += 0.1
                    reasoning.append("Volume confirming")
                
                if above_ma:
                    base_confidence += 0.05
                    reasoning.append("Price above MA")
                
                confidence = min(base_confidence, 0.9)
                
            # Strong negative momentum with deceleration
            elif price_roc < -2 and acceleration < 0:
                action = "sell"
                base_confidence = 0.6
                reasoning.append(f"Negative momentum ({price_roc:.1f}%)")
                
                if acceleration < -1:
                    base_confidence += 0.1
                    reasoning.append("Decelerating momentum")
                
                if volume_momentum > 0.5:
                    base_confidence += 0.1
                    reasoning.append("Volume confirming")
                
                if not above_ma:
                    base_confidence += 0.05
                    reasoning.append("Price below MA")
                
                confidence = min(base_confidence, 0.9)
                
            else:
                reasoning.append(f"Neutral momentum (ROC: {price_roc:.1f}%)")
            
            return {
                "action": action,
                "confidence": confidence,
                "reasoning": "; ".join(reasoning),
                "indicators": {
                    "price_roc": price_roc,
                    "volume_momentum": volume_momentum,
                    "acceleration": acceleration,
                    "above_ma": above_ma
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating momentum signal: {e}", exc_info=True)
            return {"action": "hold", "confidence": 0.3, "reasoning": f"Error in momentum calculation: {str(e)}"}

    async def _calculate_risk_profile(self, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> RiskProfile:
        """Calculate risk profile for trading"""
        try:
            current_price = market_data[-1]['close'] if market_data else 50000.0

            return await self.risk_manager.calculate_optimal_risk_profile(
                current_price=current_price,
                volatility=0.02,  # Mock volatility
                market_conditions={
                    'regime': 'normal',
                    'trend': {'strength': 0.6}
                }
            )

        except Exception as e:
            logger.error(f"Error calculating risk profile: {str(e)}")
            # Return default risk profile
            return RiskProfile(
                max_position_size=0.1,
                stop_loss_pct=0.02,
                take_profit_pct=0.05,
                risk_per_trade=0.01
            )

    def _prepare_trade_details(self, bot_config: Dict[str, Any], signal: Dict[str, Any], market_data: List[Dict[str, Any]], risk_profile: RiskProfile) -> Dict[str, Any]:
        """Prepare trade details for execution"""
        current_price = market_data[-1]['close'] if market_data else 50000.0

        return {
            "symbol": bot_config.get('symbol', 'BTC/USD'),
            "action": signal['action'],
            "quantity": bot_config.get('config', {}).get('max_position_size', 1.0),
            "price": current_price,
            "bot_id": bot_config['id'],
            "user_id": bot_config['user_id'],
            "strategy": bot_config.get('strategy', 'unknown'),
            "confidence": signal.get('confidence', 0.5),
            "risk_profile": {
                "max_position_size": risk_profile.max_position_size,
                "stop_loss_pct": risk_profile.stop_loss_pct,
                "take_profit_pct": risk_profile.take_profit_pct,
                "risk_per_trade": risk_profile.risk_per_trade
            }
        }

    async def _execute_trade(self, trade_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute real trade via RealMoneyTradingService"""
        try:
            from ..trading.real_money_service import real_money_trading_service
            from ..auth.exchange_key_service import exchange_key_service
            
            user_id = trade_details.get('user_id')
            symbol = trade_details.get('symbol', 'BTC/USDT')
            action = trade_details.get('action', 'buy')
            quantity = trade_details.get('quantity', 0.0)
            price = trade_details.get('price')
            bot_id = trade_details.get('bot_id')
            
            # Determine exchange from bot config or default
            exchange = trade_details.get('exchange', 'binance')
            
            # Check if this is paper trading mode
            trading_mode = trade_details.get('mode', 'paper')
            if trading_mode == 'paper':
                # Use paper trading service instead
                from ..backtesting.paper_trading_service import PaperTradingService
                paper_service = PaperTradingService()
                paper_trade = await paper_service.execute_paper_trade(
                    user_id=str(user_id),
                    symbol=symbol,
                    side=action,
                    quantity=quantity,
                    price=price or 0.0
                )
                return {
                    "success": True,
                    "order_id": paper_trade.id,
                    "executed_price": paper_trade.price,
                    "executed_quantity": paper_trade.quantity,
                    "pnl": paper_trade.pnl or 0.0,
                    "mode": "paper"
                }
            
            # Real money trading - validate API keys first
            user_id_str = str(user_id)
            api_key_data = await exchange_key_service.get_api_key(
                user_id_str, exchange, include_secrets=False  # Just check existence
            )
            
            if not api_key_data or not api_key_data.get('is_validated', False):
                raise ValueError(f"No validated API keys for {exchange}. Cannot execute real money trade.")
            
            # Execute real money trade
            order_type = trade_details.get('order_type', 'market')
            result = await real_money_trading_service.execute_real_money_trade(
                user_id=user_id_str,
                exchange=exchange,
                pair=symbol,
                side=action,
                order_type=order_type,
                amount=quantity,
                price=price,
                bot_id=bot_id
            )
            
            logger.info(f"Real money trade executed: {result.get('order_id')} for bot {bot_id}")
            
            return {
                "success": result.get('success', True),
                "order_id": result.get('order_id'),
                "executed_price": result.get('price', price),
                "executed_quantity": quantity,
                "pnl": 0.0,  # P&L calculated when position is closed
                "mode": "real",
                "status": result.get('status')
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}", exc_info=True)
            # In production, don't fall back to mock
            from ..config.settings import get_settings
            settings = get_settings()
            if settings.production_mode or settings.is_production:
                raise  # Re-raise in production
            else:
                # Development fallback only
                logger.warning("Trade execution failed, returning mock result in development")
                return {
                    "success": False,
                    "order_id": None,
                    "executed_price": trade_details.get('price'),
                    "executed_quantity": 0.0,
                    "pnl": 0.0,
                    "error": str(e)
                }
    
    async def _get_account_balance(self, user_id: str, exchange: str) -> float:
        """
        Get current account balance for user on exchange.
        
        Args:
            user_id: User identifier
            exchange: Exchange name (e.g., 'binance')
            
        Returns:
            Current account balance in USD
        """
        try:
            # Try to get real balance from exchange service
            from ..exchange.exchange_service import exchange_service
            
            # Get user's exchange API keys
            from ..auth.exchange_key_service import exchange_key_service
            api_key_data = await exchange_key_service.get_api_key(
                str(user_id), exchange, include_secrets=False
            )
            
            if api_key_data and api_key_data.get('is_validated'):
                # Get real balance (implementation depends on exchange service)
                # For now, return a default value
                # TODO: Implement actual balance fetching
                logger.info(f"Getting account balance for user {user_id} on {exchange}")
                return 10000.0  # Default for now
            else:
                # Paper trading mode or no API keys
                logger.info(f"Using default balance for user {user_id} (paper trading)")
                return 10000.0  # Default paper trading balance
                
        except Exception as e:
            logger.warning(f"Error getting account balance: {e}, using default")
            return 10000.0  # Safe default
    
    async def _get_current_positions(self, user_id: str, exchange: str) -> Dict[str, Dict[str, Any]]:
        """
        Get current open positions for user on exchange.
        
        Args:
            user_id: User identifier
            exchange: Exchange name (e.g., 'binance')
            
        Returns:
            Dictionary of positions keyed by symbol
        """
        try:
            # Try to get real positions from exchange service
            from ..exchange.exchange_service import exchange_service
            
            # Get user's exchange API keys
            from ..auth.exchange_key_service import exchange_key_service
            api_key_data = await exchange_key_service.get_api_key(
                str(user_id), exchange, include_secrets=False
            )
            
            if api_key_data and api_key_data.get('is_validated'):
                # Get real positions (implementation depends on exchange service)
                # For now, return empty dict
                # TODO: Implement actual position fetching
                logger.info(f"Getting positions for user {user_id} on {exchange}")
                return {}  # Empty for now
            else:
                # Paper trading mode or no API keys
                logger.info(f"Using empty positions for user {user_id} (paper trading)")
                return {}
                
        except Exception as e:
            logger.warning(f"Error getting positions: {e}, using empty positions")
            return {}  # Safe default