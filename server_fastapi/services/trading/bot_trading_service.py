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