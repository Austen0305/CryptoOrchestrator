"""
Smart Routing Service - Best price, fee-optimized, slippage-aware routing
"""
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel
from datetime import datetime
import logging
from enum import Enum

from .binance_service import BinanceService, binance_service
from .coinbase_service import CoinbaseService, coinbase_service
from .kucoin_service import KuCoinService, kucoin_service
from .kraken_service import KrakenService
from ..exchange_service import ExchangeService

logger = logging.getLogger(__name__)


class Exchange(str, Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KUCOIN = "kucoin"
    KRAKEN = "kraken"
    BYBIT = "bybit"


class RoutingStrategy(str, Enum):
    """Routing strategies"""
    BEST_PRICE = "best_price"  # Lowest price
    FEE_OPTIMIZED = "fee_optimized"  # Lowest fees
    SLIPPAGE_AWARE = "slippage_aware"  # Consider slippage
    COMBINED = "combined"  # Best overall value


class OrderQuote(BaseModel):
    """Order quote from an exchange"""
    exchange: str
    price: float
    amount: float
    fee: float
    estimated_slippage: float
    total_cost: float  # price * amount + fee
    effective_price: float  # (price * amount + fee) / amount
    confidence: float  # 0 to 1


class RoutingResult(BaseModel):
    """Smart routing result"""
    best_exchange: str
    quotes: List[OrderQuote]
    routing_strategy: str
    savings: Optional[float] = None  # Savings vs. worst quote
    timestamp: datetime = datetime.utcnow()


class SmartRoutingService:
    """Service for smart order routing across multiple exchanges"""
    
    def __init__(self):
        self.exchanges: Dict[str, Any] = {}
        self.exchange_fees: Dict[str, Dict[str, float]] = {}
        logger.info("Smart Routing Service initialized")
    
    def register_exchange(self, exchange_name: str, exchange_service: Any) -> None:
        """Register an exchange service"""
        self.exchanges[exchange_name] = exchange_service
        logger.info(f"Registered exchange: {exchange_name}")
    
    async def get_best_price(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        amount: float,
        exchanges: Optional[List[str]] = None
    ) -> RoutingResult:
        """Get best price across exchanges"""
        try:
            if exchanges is None:
                exchanges = list(self.exchanges.keys())
            
            quotes = await self._get_quotes_from_exchanges(symbol, side, amount, exchanges)
            
            if not quotes:
                raise ValueError("No quotes available from any exchange")
            
            # Sort by effective price (lowest for buy, highest for sell)
            reverse = (side == 'sell')  # For sell, higher price is better
            quotes_sorted = sorted(quotes, key=lambda q: q.effective_price, reverse=reverse)
            
            best_quote = quotes_sorted[0]
            worst_quote = quotes_sorted[-1]
            
            # Calculate savings
            if side == 'buy':
                savings = (worst_quote.effective_price - best_quote.effective_price) * amount
            else:
                savings = (best_quote.effective_price - worst_quote.effective_price) * amount
            
            return RoutingResult(
                best_exchange=best_quote.exchange,
                quotes=quotes_sorted,
                routing_strategy=RoutingStrategy.BEST_PRICE.value,
                savings=savings
            )
        
        except Exception as e:
            logger.error(f"Error getting best price: {e}")
            raise
    
    async def get_fee_optimized_route(
        self,
        symbol: str,
        side: str,
        amount: float,
        exchanges: Optional[List[str]] = None
    ) -> RoutingResult:
        """Get fee-optimized route"""
        try:
            if exchanges is None:
                exchanges = list(self.exchanges.keys())
            
            quotes = await self._get_quotes_from_exchanges(symbol, side, amount, exchanges)
            
            if not quotes:
                raise ValueError("No quotes available from any exchange")
            
            # Sort by total fee
            quotes_sorted = sorted(quotes, key=lambda q: q.fee)
            
            best_quote = quotes_sorted[0]
            
            return RoutingResult(
                best_exchange=best_quote.exchange,
                quotes=quotes_sorted,
                routing_strategy=RoutingStrategy.FEE_OPTIMIZED.value
            )
        
        except Exception as e:
            logger.error(f"Error getting fee-optimized route: {e}")
            raise
    
    async def get_slippage_aware_route(
        self,
        symbol: str,
        side: str,
        amount: float,
        exchanges: Optional[List[str]] = None,
        max_slippage: float = 0.005  # 0.5%
    ) -> RoutingResult:
        """Get slippage-aware route"""
        try:
            if exchanges is None:
                exchanges = list(self.exchanges.keys())
            
            quotes = await self._get_quotes_from_exchanges(symbol, side, amount, exchanges)
            
            if not quotes:
                raise ValueError("No quotes available from any exchange")
            
            # Filter by max slippage
            filtered_quotes = [q for q in quotes if q.estimated_slippage <= max_slippage]
            
            if not filtered_quotes:
                # If no quotes meet slippage requirement, return all quotes
                filtered_quotes = quotes
            
            # Sort by effective price
            reverse = (side == 'sell')
            quotes_sorted = sorted(filtered_quotes, key=lambda q: q.effective_price, reverse=reverse)
            
            best_quote = quotes_sorted[0]
            
            return RoutingResult(
                best_exchange=best_quote.exchange,
                quotes=quotes_sorted,
                routing_strategy=RoutingStrategy.SLIPPAGE_AWARE.value
            )
        
        except Exception as e:
            logger.error(f"Error getting slippage-aware route: {e}")
            raise
    
    async def get_combined_route(
        self,
        symbol: str,
        side: str,
        amount: float,
        exchanges: Optional[List[str]] = None,
        price_weight: float = 0.5,
        fee_weight: float = 0.3,
        slippage_weight: float = 0.2
    ) -> RoutingResult:
        """Get combined route considering price, fees, and slippage"""
        try:
            if exchanges is None:
                exchanges = list(self.exchanges.keys())
            
            quotes = await self._get_quotes_from_exchanges(symbol, side, amount, exchanges)
            
            if not quotes:
                raise ValueError("No quotes available from any exchange")
            
            # Normalize values for scoring
            prices = [q.effective_price for q in quotes]
            fees = [q.fee for q in quotes]
            slippages = [q.estimated_slippage for q in quotes]
            
            min_price = min(prices)
            max_price = max(prices)
            max_fee = max(fees) if fees else 1.0
            max_slippage = max(slippages) if slippages else 1.0
            
            # Calculate scores (lower is better for buy, higher for sell)
            for quote in quotes:
                # Price score (normalized 0-1, lower is better for buy)
                if max_price != min_price:
                    price_score = (quote.effective_price - min_price) / (max_price - min_price)
                else:
                    price_score = 0.5
                
                if side == 'sell':
                    price_score = 1.0 - price_score  # Reverse for sell
                
                # Fee score (normalized 0-1, lower is better)
                fee_score = quote.fee / max_fee if max_fee > 0 else 0.5
                
                # Slippage score (normalized 0-1, lower is better)
                slippage_score = quote.estimated_slippage / max_slippage if max_slippage > 0 else 0.5
                
                # Combined score (weighted)
                combined_score = (
                    price_weight * price_score +
                    fee_weight * fee_score +
                    slippage_weight * slippage_score
                )
                
                quote.confidence = 1.0 - combined_score  # Higher confidence = better
            
            # Sort by confidence (higher is better)
            quotes_sorted = sorted(quotes, key=lambda q: q.confidence, reverse=True)
            
            best_quote = quotes_sorted[0]
            
            return RoutingResult(
                best_exchange=best_quote.exchange,
                quotes=quotes_sorted,
                routing_strategy=RoutingStrategy.COMBINED.value
            )
        
        except Exception as e:
            logger.error(f"Error getting combined route: {e}")
            raise
    
    async def _get_quotes_from_exchanges(
        self,
        symbol: str,
        side: str,
        amount: float,
        exchanges: List[str]
    ) -> List[OrderQuote]:
        """Get quotes from multiple exchanges"""
        quotes = []
        
        for exchange_name in exchanges:
            if exchange_name not in self.exchanges:
                continue
            
            try:
                exchange = self.exchanges[exchange_name]
                
                # Get ticker
                ticker = await exchange.get_ticker(symbol)
                if not ticker:
                    continue
                
                # Get order book for slippage estimation
                orderbook = await exchange.get_order_book(symbol, depth=10)
                if not orderbook:
                    continue
                
                # Get fees
                fees = await exchange.get_fees()
                maker_fee = fees.maker if hasattr(fees, 'maker') else 0.001
                taker_fee = fees.taker if hasattr(fees, 'taker') else 0.001
                
                # Use taker fee for market orders
                fee_rate = taker_fee
                
                # Calculate price and slippage
                if side == 'buy':
                    price = ticker.get('ask', ticker.get('last', 0))
                    # Estimate slippage from order book
                    estimated_slippage = self._estimate_slippage(orderbook['asks'], amount, side)
                else:
                    price = ticker.get('bid', ticker.get('last', 0))
                    # Estimate slippage from order book
                    estimated_slippage = self._estimate_slippage(orderbook['bids'], amount, side)
                
                if price == 0:
                    continue
                
                # Calculate fees
                fee = price * amount * fee_rate
                
                # Calculate total cost
                total_cost = price * amount + fee
                effective_price = total_cost / amount if amount > 0 else price
                
                quotes.append(OrderQuote(
                    exchange=exchange_name,
                    price=price,
                    amount=amount,
                    fee=fee,
                    estimated_slippage=estimated_slippage,
                    total_cost=total_cost,
                    effective_price=effective_price,
                    confidence=0.8  # Default confidence
                ))
            
            except Exception as e:
                logger.warning(f"Failed to get quote from {exchange_name}: {e}")
                continue
        
        return quotes
    
    def _estimate_slippage(self, orderbook_side: List[List[float]], amount: float, side: str) -> float:
        """Estimate slippage based on order book depth"""
        try:
            if not orderbook_side:
                return 0.01  # Default 1% slippage if no order book
            
            # Calculate average price for the amount
            remaining = amount
            total_cost = 0.0
            first_price = orderbook_side[0][0] if orderbook_side else 0
            
            for order in orderbook_side:
                if remaining <= 0:
                    break
                
                order_price = order[0]
                order_size = order[1]
                
                filled = min(remaining, order_size)
                total_cost += order_price * filled
                remaining -= filled
            
            if amount == 0 or first_price == 0:
                return 0.01
            
            avg_price = total_cost / amount
            slippage = abs(avg_price - first_price) / first_price
            
            return slippage
        
        except Exception as e:
            logger.error(f"Error estimating slippage: {e}")
            return 0.01  # Default 1% slippage
    
    async def route_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        strategy: RoutingStrategy = RoutingStrategy.COMBINED,
        exchanges: Optional[List[str]] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Route order to best exchange based on strategy"""
        try:
            if strategy == RoutingStrategy.BEST_PRICE:
                result = await self.get_best_price(symbol, side, amount, exchanges)
            elif strategy == RoutingStrategy.FEE_OPTIMIZED:
                result = await self.get_fee_optimized_route(symbol, side, amount, exchanges)
            elif strategy == RoutingStrategy.SLIPPAGE_AWARE:
                max_slippage = kwargs.get('max_slippage', 0.005)
                result = await self.get_slippage_aware_route(symbol, side, amount, exchanges, max_slippage)
            else:  # COMBINED
                price_weight = kwargs.get('price_weight', 0.5)
                fee_weight = kwargs.get('fee_weight', 0.3)
                slippage_weight = kwargs.get('slippage_weight', 0.2)
                result = await self.get_combined_route(
                    symbol, side, amount, exchanges,
                    price_weight, fee_weight, slippage_weight
                )
            
            return result.best_exchange, result.quotes[0].dict()
        
        except Exception as e:
            logger.error(f"Error routing order: {e}")
            raise


# Global service instance
smart_routing_service = SmartRoutingService()

# Initialize with default exchanges (done at module level)
def _init_routing_service():
    """Initialize routing service with available exchanges"""
    smart_routing_service.register_exchange(Exchange.BINANCE.value, binance_service)
    smart_routing_service.register_exchange(Exchange.COINBASE.value, coinbase_service)
    smart_routing_service.register_exchange(Exchange.KUCOIN.value, kucoin_service)
    
    # Try to register Kraken if available
    try:
        from .kraken_service import kraken_service as ks
        if ks:
            smart_routing_service.register_exchange(Exchange.KRAKEN.value, ks)
    except Exception:
        pass  # Kraken not available

_init_routing_service()
