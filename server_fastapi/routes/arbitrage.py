"""
Multi-Exchange Arbitrage Scanner and Executor
Detect and execute arbitrage opportunities across multiple exchanges
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/arbitrage", tags=["Multi-Exchange Arbitrage"])


class ArbitrageType(str, Enum):
    """Types of arbitrage opportunities"""
    SIMPLE = "simple"  # Buy on Exchange A, sell on Exchange B
    TRIANGULAR = "triangular"  # A->B->C->A on same exchange
    CROSS_EXCHANGE_TRIANGULAR = "cross_exchange_triangular"  # Triangular across exchanges


class ArbitrageOpportunity(BaseModel):
    """Detected arbitrage opportunity"""
    opportunity_id: str
    type: ArbitrageType
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_percent: float
    profit_percent: float  # After fees
    estimated_profit_usd: float
    buy_fee_percent: float
    sell_fee_percent: float
    timestamp: str
    expires_at: str
    latency_ms: float
    execution_confidence: float = Field(..., description="Confidence score 0-100")


class TriangularArbitrageOpportunity(BaseModel):
    """Triangular arbitrage across 3 trading pairs"""
    opportunity_id: str
    exchange: str
    pair1: str  # e.g., BTC/USDT
    pair2: str  # e.g., ETH/BTC
    pair3: str  # e.g., ETH/USDT
    profit_percent: float
    estimated_profit_usd: float
    total_fees_percent: float
    timestamp: str
    confidence: float


class ArbitrageExecution(BaseModel):
    """Arbitrage execution result"""
    execution_id: str
    opportunity_id: str
    status: str  # "success", "partial", "failed"
    buy_order_id: Optional[str] = None
    sell_order_id: Optional[str] = None
    actual_profit_usd: float
    execution_time_ms: float
    slippage_percent: float
    error_message: Optional[str] = None


class ArbitrageConfig(BaseModel):
    """Arbitrage scanner configuration"""
    enabled_exchanges: List[str]
    min_profit_percent: float = Field(0.5, description="Minimum profit % after fees")
    max_position_size_usd: float = Field(1000.0, description="Max position size per trade")
    auto_execute: bool = Field(False, description="Automatically execute opportunities")
    blacklist_symbols: List[str] = Field([], description="Symbols to ignore")
    max_latency_ms: float = Field(500.0, description="Max acceptable latency")
    min_volume_24h_usd: float = Field(100000.0, description="Min 24h volume")


class ExchangePriceData(BaseModel):
    """Price data from an exchange"""
    exchange: str
    symbol: str
    bid: float  # Best bid (highest buy price)
    ask: float  # Best ask (lowest sell price)
    spread_percent: float
    volume_24h: float
    fee_percent: float
    latency_ms: float
    timestamp: str


class ArbitrageStats(BaseModel):
    """Arbitrage statistics"""
    total_opportunities_detected: int
    total_executed: int
    total_profit_usd: float
    success_rate: float
    avg_profit_percent: float
    best_opportunity: Optional[Dict] = None
    active_opportunities: int


# Global state
active_opportunities: Dict[str, ArbitrageOpportunity] = {}
execution_history: List[ArbitrageExecution] = []
scanner_running = False
scanner_config: Optional[ArbitrageConfig] = None


class ArbitrageScanner:
    """Multi-exchange arbitrage scanner"""
    
    def __init__(self):
        self.price_cache: Dict[str, Dict[str, ExchangePriceData]] = {}
        self.opportunities: List[ArbitrageOpportunity] = []
        self.is_scanning = False
    
    async def fetch_exchange_prices(
        self,
        exchange: str,
        symbols: List[str]
    ) -> Dict[str, ExchangePriceData]:
        """Fetch current prices from an exchange"""
        # Mock implementation - integrate with ccxt
        import random
        
        prices = {}
        for symbol in symbols:
            base_price = 50000.0  # Mock BTC price
            spread = random.uniform(0.001, 0.01)
            
            bid = base_price * (1 - spread / 2)
            ask = base_price * (1 + spread / 2)
            
            prices[symbol] = ExchangePriceData(
                exchange=exchange,
                symbol=symbol,
                bid=bid,
                ask=ask,
                spread_percent=spread * 100,
                volume_24h=random.uniform(100000, 10000000),
                fee_percent=0.1,  # 0.1% trading fee
                latency_ms=random.uniform(50, 300),
                timestamp=datetime.now().isoformat()
            )
        
        return prices
    
    async def scan_simple_arbitrage(
        self,
        symbols: List[str],
        exchanges: List[str],
        config: ArbitrageConfig
    ) -> List[ArbitrageOpportunity]:
        """Scan for simple arbitrage opportunities"""
        opportunities = []
        
        # Fetch prices from all exchanges in parallel
        fetch_tasks = [
            self.fetch_exchange_prices(exchange, symbols)
            for exchange in exchanges
        ]
        
        exchange_prices = await asyncio.gather(*fetch_tasks)
        
        # Build price dictionary
        all_prices: Dict[str, Dict[str, ExchangePriceData]] = {}
        for i, exchange in enumerate(exchanges):
            all_prices[exchange] = exchange_prices[i]
        
        # Compare prices across exchanges
        for symbol in symbols:
            if symbol in config.blacklist_symbols:
                continue
            
            # Find best bid (highest price to sell at)
            best_sell_exchange = max(
                exchanges,
                key=lambda e: all_prices[e][symbol].bid
            )
            best_sell_price = all_prices[best_sell_exchange][symbol].bid
            
            # Find best ask (lowest price to buy at)
            best_buy_exchange = min(
                exchanges,
                key=lambda e: all_prices[e][symbol].ask
            )
            best_buy_price = all_prices[best_buy_exchange][symbol].ask
            
            # Skip if same exchange
            if best_buy_exchange == best_sell_exchange:
                continue
            
            # Calculate spread and profit
            spread_percent = ((best_sell_price - best_buy_price) / best_buy_price) * 100
            
            buy_fee = all_prices[best_buy_exchange][symbol].fee_percent
            sell_fee = all_prices[best_sell_exchange][symbol].fee_percent
            
            profit_percent = spread_percent - buy_fee - sell_fee
            
            # Check minimum profit threshold
            if profit_percent < config.min_profit_percent:
                continue
            
            # Check volume
            min_volume = min(
                all_prices[best_buy_exchange][symbol].volume_24h,
                all_prices[best_sell_exchange][symbol].volume_24h
            )
            
            if min_volume < config.min_volume_24h_usd:
                continue
            
            # Check latency
            max_latency = max(
                all_prices[best_buy_exchange][symbol].latency_ms,
                all_prices[best_sell_exchange][symbol].latency_ms
            )
            
            if max_latency > config.max_latency_ms:
                continue
            
            # Calculate estimated profit
            estimated_profit = (config.max_position_size_usd * profit_percent) / 100
            
            # Calculate execution confidence
            confidence = self._calculate_confidence(
                spread_percent,
                profit_percent,
                max_latency,
                min_volume
            )
            
            opportunity = ArbitrageOpportunity(
                opportunity_id=f"arb_{symbol}_{int(datetime.now().timestamp())}",
                type=ArbitrageType.SIMPLE,
                symbol=symbol,
                buy_exchange=best_buy_exchange,
                sell_exchange=best_sell_exchange,
                buy_price=best_buy_price,
                sell_price=best_sell_price,
                spread_percent=spread_percent,
                profit_percent=profit_percent,
                estimated_profit_usd=estimated_profit,
                buy_fee_percent=buy_fee,
                sell_fee_percent=sell_fee,
                timestamp=datetime.now().isoformat(),
                expires_at=(datetime.now() + timedelta(seconds=30)).isoformat(),
                latency_ms=max_latency,
                execution_confidence=confidence
            )
            
            opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_confidence(
        self,
        spread_percent: float,
        profit_percent: float,
        latency_ms: float,
        volume_24h: float
    ) -> float:
        """Calculate execution confidence score"""
        confidence = 100.0
        
        # Reduce confidence based on latency
        if latency_ms > 200:
            confidence -= (latency_ms - 200) * 0.1
        
        # Increase confidence with higher spread
        confidence += min(spread_percent * 5, 20)
        
        # Increase confidence with higher volume
        volume_score = min(volume_24h / 1000000, 10)
        confidence += volume_score
        
        # Reduce if profit margin is thin
        if profit_percent < 1.0:
            confidence -= (1.0 - profit_percent) * 20
        
        return max(0, min(100, confidence))
    
    async def execute_arbitrage(
        self,
        opportunity: ArbitrageOpportunity,
        position_size_usd: float
    ) -> ArbitrageExecution:
        """Execute arbitrage trade"""
        start_time = datetime.now()
        
        execution = ArbitrageExecution(
            execution_id=f"exec_{opportunity.opportunity_id}",
            opportunity_id=opportunity.opportunity_id,
            status="pending",
            actual_profit_usd=0.0,
            execution_time_ms=0.0,
            slippage_percent=0.0
        )
        
        try:
            # Execute buy order
            buy_result = await self._place_order(
                opportunity.buy_exchange,
                opportunity.symbol,
                "buy",
                opportunity.buy_price,
                position_size_usd
            )
            
            execution.buy_order_id = buy_result["order_id"]
            
            # Execute sell order
            sell_result = await self._place_order(
                opportunity.sell_exchange,
                opportunity.symbol,
                "sell",
                opportunity.sell_price,
                position_size_usd
            )
            
            execution.sell_order_id = sell_result["order_id"]
            
            # Calculate actual profit
            actual_profit = (
                sell_result["executed_value"] - buy_result["executed_value"]
                - buy_result["fee"] - sell_result["fee"]
            )
            
            # Calculate slippage
            expected_profit = (position_size_usd * opportunity.profit_percent) / 100
            slippage_percent = ((expected_profit - actual_profit) / expected_profit) * 100
            
            execution.actual_profit_usd = actual_profit
            execution.slippage_percent = slippage_percent
            execution.status = "success"
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            logger.error(f"Arbitrage execution failed: {e}")
        
        execution.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return execution
    
    async def _place_order(
        self,
        exchange: str,
        symbol: str,
        side: str,
        price: float,
        size_usd: float
    ) -> Dict:
        """Place order on exchange"""
        # Mock implementation - integrate with ccxt
        import random
        
        await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate network latency
        
        return {
            "order_id": f"order_{exchange}_{int(datetime.now().timestamp())}",
            "executed_value": size_usd * (1 + random.uniform(-0.001, 0.001)),
            "fee": size_usd * 0.001
        }


# Global scanner instance
scanner = ArbitrageScanner()


async def arbitrage_scan_loop(config: ArbitrageConfig):
    """Background task for continuous scanning"""
    global scanner_running
    
    logger.info("Starting arbitrage scanner...")
    
    while scanner_running:
        try:
            # Scan for opportunities
            opportunities = await scanner.scan_simple_arbitrage(
                symbols=["BTC/USDT", "ETH/USDT", "BNB/USDT"],
                exchanges=config.enabled_exchanges,
                config=config
            )
            
            # Store active opportunities
            for opp in opportunities:
                active_opportunities[opp.opportunity_id] = opp
                
                # Auto-execute if enabled
                if config.auto_execute and opp.execution_confidence > 80:
                    execution = await scanner.execute_arbitrage(
                        opp,
                        config.max_position_size_usd
                    )
                    execution_history.append(execution)
                    logger.info(f"Auto-executed arbitrage: {execution.status}")
            
            # Clean up expired opportunities
            now = datetime.now()
            expired = [
                opp_id for opp_id, opp in active_opportunities.items()
                if datetime.fromisoformat(opp.expires_at) < now
            ]
            for opp_id in expired:
                del active_opportunities[opp_id]
            
        except Exception as e:
            logger.error(f"Arbitrage scan error: {e}")
        
        await asyncio.sleep(5)  # Scan every 5 seconds


@router.post("/start")
async def start_scanner(
    config: ArbitrageConfig,
    background_tasks: BackgroundTasks
):
    """
    Start arbitrage scanner
    
    Continuously monitors exchanges for arbitrage opportunities
    """
    global scanner_running, scanner_config
    
    if scanner_running:
        raise HTTPException(status_code=400, detail="Scanner already running")
    
    scanner_running = True
    scanner_config = config
    
    background_tasks.add_task(arbitrage_scan_loop, config)
    
    logger.info(f"Started arbitrage scanner with {len(config.enabled_exchanges)} exchanges")
    
    return {
        "success": True,
        "message": "Arbitrage scanner started",
        "config": config
    }


@router.post("/stop")
async def stop_scanner():
    """Stop arbitrage scanner"""
    global scanner_running
    
    if not scanner_running:
        raise HTTPException(status_code=400, detail="Scanner not running")
    
    scanner_running = False
    
    logger.info("Stopped arbitrage scanner")
    
    return {"success": True, "message": "Scanner stopped"}


@router.get("/opportunities", response_model=List[ArbitrageOpportunity])
async def get_opportunities(
    min_profit: Optional[float] = None,
    symbol: Optional[str] = None,
    limit: int = 50
):
    """
    Get current arbitrage opportunities
    
    Opportunities expire after 30 seconds
    """
    opportunities = list(active_opportunities.values())
    
    if min_profit:
        opportunities = [o for o in opportunities if o.profit_percent >= min_profit]
    
    if symbol:
        opportunities = [o for o in opportunities if o.symbol == symbol]
    
    # Sort by profit
    opportunities.sort(key=lambda o: o.profit_percent, reverse=True)
    
    return opportunities[:limit]


@router.post("/execute/{opportunity_id}", response_model=ArbitrageExecution)
async def execute_opportunity(
    opportunity_id: str,
    position_size_usd: float = 1000.0
):
    """
    Manually execute an arbitrage opportunity
    
    Executes buy and sell orders simultaneously
    """
    if opportunity_id not in active_opportunities:
        raise HTTPException(status_code=404, detail="Opportunity not found or expired")
    
    opportunity = active_opportunities[opportunity_id]
    
    # Check if expired
    if datetime.fromisoformat(opportunity.expires_at) < datetime.now():
        raise HTTPException(status_code=400, detail="Opportunity has expired")
    
    execution = await scanner.execute_arbitrage(opportunity, position_size_usd)
    execution_history.append(execution)
    
    # Remove from active opportunities
    del active_opportunities[opportunity_id]
    
    logger.info(f"Executed arbitrage {opportunity_id}: {execution.status}")
    
    return execution


@router.get("/history", response_model=List[ArbitrageExecution])
async def get_execution_history(limit: int = 100):
    """Get arbitrage execution history"""
    return execution_history[-limit:]


@router.get("/stats", response_model=ArbitrageStats)
async def get_arbitrage_stats():
    """Get arbitrage statistics"""
    successful = [e for e in execution_history if e.status == "success"]
    
    total_profit = sum(e.actual_profit_usd for e in successful)
    success_rate = (len(successful) / len(execution_history) * 100) if execution_history else 0
    
    avg_profit = (
        sum(e.actual_profit_usd for e in successful) / len(successful)
        if successful else 0
    )
    
    best_exec = max(successful, key=lambda e: e.actual_profit_usd) if successful else None
    
    return ArbitrageStats(
        total_opportunities_detected=len(active_opportunities) + len(execution_history),
        total_executed=len(execution_history),
        total_profit_usd=total_profit,
        success_rate=success_rate,
        avg_profit_percent=avg_profit,
        best_opportunity={
            "execution_id": best_exec.execution_id,
            "profit_usd": best_exec.actual_profit_usd
        } if best_exec else None,
        active_opportunities=len(active_opportunities)
    )


@router.get("/status")
async def get_scanner_status():
    """Get scanner status"""
    return {
        "running": scanner_running,
        "active_opportunities": len(active_opportunities),
        "total_executed": len(execution_history),
        "config": scanner_config
    }
