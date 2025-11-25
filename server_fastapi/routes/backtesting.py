import os
import sqlite3
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from ..services.backtesting_engine import BacktestingEngine, BacktestConfig, BacktestResult
from ..services.ml.ensemble_engine import MarketData
from ..services.backtesting.paper_trading_service import PaperTradingService
from ..services.backtesting.strategy_optimizer import StrategyOptimizer, OptimizationConfig, ParameterRange

logger = logging.getLogger(__name__)

router = APIRouter()

# Database setup for backtest results
BACKTEST_DB = os.getenv('BACKTEST_RESULTS_DB', 'backtest_results.db')

def init_backtest_db():
    """Initialize database for backtest results storage"""
    with sqlite3.connect(BACKTEST_DB) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id TEXT PRIMARY KEY,
                bot_id TEXT NOT NULL,
                total_return REAL NOT NULL,
                sharpe_ratio REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                win_rate REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                profit_factor REAL NOT NULL,
                trades TEXT NOT NULL,
                equity_curve TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_bot_id ON backtest_results(bot_id)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON backtest_results(created_at DESC)
        ''')
        conn.commit()

# Initialize database on startup
init_backtest_db()

# Dependency injection
def get_backtesting_engine() -> BacktestingEngine:
    return BacktestingEngine()

def get_paper_trading_service() -> PaperTradingService:
    return PaperTradingService()

def get_strategy_optimizer() -> StrategyOptimizer:
    return StrategyOptimizer()

# Request/Response models
class RunBacktestRequest(BaseModel):
    botId: str
    historicalData: List[Dict[str, Any]]  # Will be converted to MarketData
    initialBalance: Optional[float] = 1000.0
    commission: Optional[float] = 0.001
    userId: Optional[str] = None

class BacktestSummary(BaseModel):
    id: Optional[str] = None
    botId: str
    totalReturn: float
    sharpeRatio: float
    maxDrawdown: float
    winRate: float
    totalTrades: int
    profitFactor: float
    trades: List[Dict[str, Any]]
    equityCurve: List[Dict[str, Any]]
    createdAt: Optional[datetime] = None

class SaveBacktestRequest(BaseModel):
    result: BacktestSummary
    userId: str

class PaperTradeRequest(BaseModel):
    userId: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float

class OptimizationRequest(BaseModel):
    strategyName: str
    parameters: Dict[str, Dict[str, Any]]  # parameter -> {min, max, step}
    populationSize: Optional[int] = 50
    generations: Optional[int] = 20
    historicalData: List[Dict[str, Any]]
    botId: str
    userId: str

class ParameterSweepRequest(BaseModel):
    strategyName: str
    paramRanges: Dict[str, Dict[str, Any]]  # parameter -> {min, max, step}
    historicalData: List[Dict[str, Any]]
    botId: str
    maxCombinations: Optional[int] = 1000

@router.post("/run", response_model=BacktestSummary)
async def run_backtest(
    request: RunBacktestRequest,
    backtesting_engine: BacktestingEngine = Depends(get_backtesting_engine)
) -> BacktestSummary:
    """Run a backtest for a bot with historical data"""
    try:
        # Validate input
        if not request.botId:
            raise HTTPException(status_code=400, detail="botId is required")
        if not request.historicalData or len(request.historicalData) < 100:
            raise HTTPException(status_code=400, detail="Insufficient historical data (minimum 100 data points required)")

        # Convert historical data to MarketData objects
        historical_data = [
            MarketData(
                timestamp=data['timestamp'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume']
            )
            for data in request.historicalData
        ]

        # Create backtest config
        config = BacktestConfig(
            botId=request.botId,
            initialBalance=request.initialBalance,
            commission=request.commission
        )

        # Run backtest
        result = await backtesting_engine.run_backtest(config, historical_data)

        # Auto-save result if userId provided
        result_id = result.id
        if request.userId and not result_id:
            result_id = str(uuid.uuid4())
            try:
                with sqlite3.connect(BACKTEST_DB) as conn:
                    conn.execute('''
                        INSERT INTO backtest_results
                        (id, bot_id, total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, profit_factor, trades, equity_curve, user_id, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        result_id,
                        result.botId,
                        result.totalReturn,
                        result.sharpeRatio,
                        result.maxDrawdown,
                        result.winRate,
                        result.totalTrades,
                        result.profitFactor,
                        json.dumps(result.trades),
                        json.dumps(result.equityCurve),
                        request.userId,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to auto-save backtest result: {e}")

        # Convert to response format
        summary = BacktestSummary(
            id=result_id,
            botId=result.botId,
            totalReturn=result.totalReturn,
            sharpeRatio=result.sharpeRatio,
            maxDrawdown=result.maxDrawdown,
            winRate=result.winRate,
            totalTrades=result.totalTrades,
            profitFactor=result.profitFactor,
            trades=result.trades,
            equityCurve=result.equityCurve,
            createdAt=result.createdAt
        )

        logger.info(f"Backtest completed for bot {request.botId}: {result.totalTrades} trades, {result.totalReturn:.2%} return")
        return summary

    except ValueError as e:
        logger.error(f"Backtest validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backtest")


@router.post("/paper-trade", response_model=dict)
async def execute_paper_trade(
    request: PaperTradeRequest,
    paper_trading: PaperTradingService = Depends(get_paper_trading_service)
):
    """Execute a paper trade"""
    try:
        if not request.userId:
            raise HTTPException(status_code=400, detail="userId is required")

        trade = await paper_trading.execute_paper_trade(
            user_id=request.userId,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price
        )

        return {
            "success": True,
            "trade": trade.dict(),
            "message": f"Paper trade executed: {request.side} {request.quantity} {request.symbol} at {request.price}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Paper trade execution failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute paper trade")


@router.get("/paper-portfolio/{user_id}", response_model=dict)
async def get_paper_portfolio(
    user_id: str,
    paper_trading: PaperTradingService = Depends(get_paper_trading_service)
):
    """Get paper trading portfolio"""
    try:
        portfolio = await paper_trading.get_paper_portfolio(user_id)
        return {
            "portfolio": portfolio.dict(),
            "message": f"Portfolio retrieved for user {user_id}"
        }

    except Exception as e:
        logger.error(f"Failed to get paper portfolio for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get paper portfolio")


@router.get("/paper-trades/{user_id}", response_model=dict)
async def get_paper_trades(
    user_id: str,
    limit: Optional[int] = 50,
    paper_trading: PaperTradingService = Depends(get_paper_trading_service)
):
    """Get paper trading history"""
    try:
        trades = await paper_trading.get_paper_trades(user_id, limit)
        return {
            "trades": [trade.dict() for trade in trades],
            "total": len(trades),
            "message": f"Retrieved {len(trades)} paper trades for user {user_id}"
        }

    except Exception as e:
        logger.error(f"Failed to get paper trades for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get paper trades")


@router.post("/paper-reset/{user_id}", response_model=dict)
async def reset_paper_trading(
    user_id: str,
    paper_trading: PaperTradingService = Depends(get_paper_trading_service)
):
    """Reset paper trading account"""
    try:
        success = await paper_trading.reset_paper_trading(user_id)
        if success:
            return {
                "success": True,
                "message": f"Paper trading account reset for user {user_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reset paper trading account")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset paper trading for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset paper trading account")


@router.post("/optimize", response_model=dict)
async def run_strategy_optimization(
    request: OptimizationRequest,
    optimizer: StrategyOptimizer = Depends(get_strategy_optimizer)
):
    """Run strategy optimization"""
    try:
        if not request.userId:
            raise HTTPException(status_code=400, detail="userId is required")

        # Convert historical data to MarketData objects
        historical_data = [
            MarketData(
                timestamp=data['timestamp'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume']
            )
            for data in request.historicalData
        ]

        # Create optimization config
        param_ranges = {}
        for param_name, param_config in request.parameters.items():
            param_ranges[param_name] = ParameterRange(
                min=param_config['min'],
                max=param_config['max'],
                step=param_config.get('step')
            )

        config = OptimizationConfig(
            strategy_name=request.strategyName,
            parameters=param_ranges,
            population_size=request.populationSize,
            generations=request.generations
        )

        # Run optimization
        results = await optimizer.optimize_strategy(config, historical_data, request.botId)

        return {
            "success": True,
            "results": [result.dict() for result in results],
            "message": f"Strategy optimization completed for {request.strategyName}"
        }

    except Exception as e:
        logger.error(f"Strategy optimization failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to run strategy optimization")


@router.post("/parameter-sweep", response_model=dict)
async def run_parameter_sweep(
    request: ParameterSweepRequest,
    optimizer: StrategyOptimizer = Depends(get_strategy_optimizer)
):
    """Run parameter sweep analysis"""
    try:
        # Convert historical data to MarketData objects
        historical_data = [
            MarketData(
                timestamp=data['timestamp'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume']
            )
            for data in request.historicalData
        ]

        # Convert parameter ranges
        param_ranges = {}
        for param_name, param_config in request.paramRanges.items():
            param_ranges[param_name] = ParameterRange(
                min=param_config['min'],
                max=param_config['max'],
                step=param_config.get('step')
            )

        # Run parameter sweep
        results = await optimizer.run_parameter_sweep(
            param_ranges=param_ranges,
            strategy_name=request.strategyName,
            historical_data=historical_data,
            bot_id=request.botId,
            max_combinations=request.maxCombinations
        )

        return {
            "success": True,
            "results": results,
            "message": f"Parameter sweep completed for {request.strategyName}"
        }

    except Exception as e:
        logger.error(f"Parameter sweep failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to run parameter sweep")


@router.get("/optimal-parameters/{strategy_name}", response_model=dict)
async def get_optimal_parameters(
    strategy_name: str,
    limit: Optional[int] = 10,
    optimizer: StrategyOptimizer = Depends(get_strategy_optimizer)
):
    """Get optimal parameters for a strategy"""
    try:
        results = await optimizer.get_optimal_parameters(strategy_name, limit=limit)

        return {
            "success": True,
            "optimal_parameters": [result.dict() for result in results],
            "message": f"Retrieved {len(results)} optimal parameter sets for {strategy_name}"
        }

    except Exception as e:
        logger.error(f"Failed to get optimal parameters for {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get optimal parameters")

@router.post("/save", response_model=BacktestSummary)
async def save_backtest_result(
    request: SaveBacktestRequest
) -> BacktestSummary:
    """Save backtest result to persistent storage"""
    try:
        if not request.result.botId:
            raise HTTPException(status_code=400, detail="botId is required")

        # Generate ID if not provided
        result_id = request.result.id or str(uuid.uuid4())

        with sqlite3.connect(BACKTEST_DB) as conn:
            conn.execute('''
                INSERT INTO backtest_results
                (id, bot_id, total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, profit_factor, trades, equity_curve, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_id,
                request.result.botId,
                request.result.totalReturn,
                request.result.sharpeRatio,
                request.result.maxDrawdown,
                request.result.winRate,
                request.result.totalTrades,
                request.result.profitFactor,
                json.dumps(request.result.trades),
                json.dumps(request.result.equityCurve),
                request.userId,
                datetime.now().isoformat()
            ))
            conn.commit()

        # Return saved result with ID and timestamp
        saved_result = BacktestSummary(
            id=result_id,
            botId=request.result.botId,
            totalReturn=request.result.totalReturn,
            sharpeRatio=request.result.sharpeRatio,
            maxDrawdown=request.result.maxDrawdown,
            winRate=request.result.winRate,
            totalTrades=request.result.totalTrades,
            profitFactor=request.result.profitFactor,
            trades=request.result.trades,
            equityCurve=request.result.equityCurve,
            createdAt=datetime.now()
        )

        logger.info(f"Backtest result saved: {result_id} for bot {request.result.botId}")
        return saved_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save backtest result: {e}")
        raise HTTPException(status_code=500, detail="Failed to save backtest result")

@router.get("/results", response_model=List[BacktestSummary])
async def get_backtest_results(
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    bot_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[BacktestSummary]:
    """Get stored backtest results"""
    try:
        with sqlite3.connect(BACKTEST_DB) as conn:
            query = '''
                SELECT id, bot_id, total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, profit_factor, trades, equity_curve, created_at
                FROM backtest_results
                WHERE 1=1
            '''
            params = []

            if bot_id:
                query += ' AND bot_id = ?'
                params.append(bot_id)

            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(BacktestSummary(
                id=row[0],
                botId=row[1],
                totalReturn=row[2],
                sharpeRatio=row[3],
                maxDrawdown=row[4],
                winRate=row[5],
                totalTrades=row[6],
                profitFactor=row[7],
                trades=json.loads(row[8]),
                equityCurve=json.loads(row[9]),
                createdAt=datetime.fromisoformat(row[10])
            ))

        logger.info(f"Retrieved {len(results)} backtest results")
        return results

    except Exception as e:
        logger.error(f"Failed to get backtest results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backtest results")

@router.get("/results/{result_id}", response_model=BacktestSummary)
async def get_backtest_result(result_id: str) -> BacktestSummary:
    """Get a specific backtest result by ID"""
    try:
        with sqlite3.connect(BACKTEST_DB) as conn:
            cursor = conn.execute('''
                SELECT id, bot_id, total_return, sharpe_ratio, max_drawdown, win_rate, total_trades, profit_factor, trades, equity_curve, created_at
                FROM backtest_results
                WHERE id = ?
            ''', (result_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Backtest result not found")

        result = BacktestSummary(
            id=row[0],
            botId=row[1],
            totalReturn=row[2],
            sharpeRatio=row[3],
            maxDrawdown=row[4],
            winRate=row[5],
            totalTrades=row[6],
            profitFactor=row[7],
            trades=json.loads(row[8]),
            equityCurve=json.loads(row[9]),
            createdAt=datetime.fromisoformat(row[10])
        )

        logger.info(f"Retrieved backtest result {result_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backtest result {result_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backtest result")