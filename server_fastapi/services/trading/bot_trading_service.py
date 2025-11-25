"""
Bot trading service for trading cycle execution
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

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

    def __init__(self):
        self.control_service = BotControlService()
        self.monitoring_service = BotMonitoringService()

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

            # Validate trade with safety system
            from ..trading.safe_trading_system import SafeTradingSystem
            safe_system = SafeTradingSystem()
            validation = await safe_system.validate_trade(trade_details)

            if not validation["valid"]:
                logger.warning(f"Trade blocked by safety system for bot {bot_id}: {validation['errors']}")
                return {"action": "blocked", "reason": "safety_validation_failed", "details": validation}

            # Execute trade (mock implementation)
            trade_result = await self._execute_trade(trade_details)

            # Record trade result
            await safe_system.record_trade_result(trade_details, trade_result.get('pnl', 0.0))

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
        """Get market data for trading decisions (mock implementation)"""
        # In a real implementation, this would fetch from exchange APIs
        return [
            {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "open": 50000,
                "high": 50200,
                "low": 49900,
                "close": 50100,
                "volume": 1.5
            }
        ]

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
                # Simple moving average strategy (mock)
                return self._simple_ma_signal(market_data, bot_config)

            elif strategy == 'rsi':
                # RSI strategy (mock)
                return self._rsi_signal(market_data, bot_config)

            # Default hold signal
            return {"action": "hold", "confidence": 0.5, "reasoning": "Default hold"}

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
        """Simple moving average trading signal"""
        # Mock implementation - in reality would calculate actual MAs
        return {"action": "hold", "confidence": 0.5, "reasoning": "Simple MA strategy"}

    def _rsi_signal(self, market_data: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Dict[str, Any]:
        """RSI-based trading signal"""
        # Mock implementation - in reality would calculate RSI
        return {"action": "hold", "confidence": 0.5, "reasoning": "RSI strategy"}

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
        """Execute trade (mock implementation)"""
        # In a real implementation, this would interface with exchange APIs
        logger.info(f"Mock executing trade: {trade_details}")

        # Simulate trade execution
        return {
            "success": True,
            "order_id": f"order-{trade_details['bot_id']}-{int(datetime.now().timestamp())}",
            "executed_price": trade_details['price'],
            "executed_quantity": trade_details['quantity'],
            "pnl": 0.0  # Mock P&L
        }