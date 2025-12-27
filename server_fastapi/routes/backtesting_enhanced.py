"""
Enhanced Backtesting Engine with Monte Carlo Simulation and Walk-Forward Analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["Enhanced Backtesting"])


class BacktestStrategy(BaseModel):
    """Strategy configuration for backtesting"""

    strategy_id: str
    parameters: Dict[str, float] = Field(..., description="Strategy parameters")
    initial_capital: float = Field(10000.0, ge=100)
    position_size_pct: float = Field(0.1, ge=0.01, le=1.0)
    stop_loss_pct: Optional[float] = Field(None, ge=0.001, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.001)


class BacktestConfig(BaseModel):
    """Backtesting configuration"""

    symbol: str
    start_date: str
    end_date: str
    timeframe: str = Field("1h", description="Candle timeframe")
    strategy: BacktestStrategy
    commission_rate: float = Field(0.001, description="Trading commission (0.1%)")
    slippage_pct: float = Field(0.001, description="Slippage percentage")


class MonteCarloConfig(BaseModel):
    """Monte Carlo simulation configuration"""

    backtest_config: BacktestConfig
    num_simulations: int = Field(1000, ge=100, le=10000)
    confidence_level: float = Field(0.95, ge=0.5, le=0.99)
    randomize_trades: bool = Field(True, description="Randomize trade order")
    randomize_prices: bool = Field(False, description="Add random noise to prices")


class WalkForwardConfig(BaseModel):
    """Walk-forward analysis configuration"""

    backtest_config: BacktestConfig
    in_sample_days: int = Field(90, description="In-sample optimization period")
    out_sample_days: int = Field(30, description="Out-of-sample testing period")
    anchor: bool = Field(False, description="Anchored vs rolling window")
    optimize_metric: str = Field("sharpe_ratio", description="Metric to optimize")


@dataclass
class Trade:
    """Single trade result"""

    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    side: str  # 'long' or 'short'
    size: float
    pnl: float
    pnl_pct: float
    commission: float
    slippage: float


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""

    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_trade: float
    num_trades: int
    num_winning: int
    num_losing: int
    avg_holding_period_hours: float
    recovery_factor: float
    expectancy: float


class BacktestResult(BaseModel):
    """Backtesting result"""

    backtest_id: str
    symbol: str
    start_date: str
    end_date: str
    strategy_id: str
    initial_capital: float
    final_capital: float
    metrics: Dict
    equity_curve: List[Dict[str, float]]
    trades: List[Dict]
    drawdown_periods: List[Dict]


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation result"""

    simulation_id: str
    num_simulations: int
    confidence_level: float
    base_metrics: Dict
    simulated_returns: List[float]
    confidence_interval: Dict[str, float]
    risk_of_ruin: float
    expected_return: float
    worst_case: Dict
    best_case: Dict
    percentile_metrics: Dict[int, Dict]


class WalkForwardResult(BaseModel):
    """Walk-forward analysis result"""

    analysis_id: str
    num_periods: int
    in_sample_metrics: List[Dict]
    out_sample_metrics: List[Dict]
    overall_metrics: Dict
    degradation_factor: float
    consistency_score: float
    optimal_parameters: List[Dict]


class BacktestEngine:
    """Enhanced backtesting engine"""

    def __init__(self):
        self.results_cache: Dict[str, BacktestResult] = {}

    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Execute standard backtest"""
        logger.info(f"Starting backtest for {config.symbol}")

        # Fetch historical data
        candles = await self._fetch_market_data(
            config.symbol, config.start_date, config.end_date, config.timeframe
        )

        # Generate trading signals
        signals = await self._generate_signals(candles, config.strategy)

        # Execute trades
        trades = await self._simulate_trades(candles, signals, config)

        # Calculate performance metrics
        metrics = self._calculate_metrics(trades, config.strategy.initial_capital)

        # Build equity curve
        equity_curve = self._build_equity_curve(trades, config.strategy.initial_capital)

        # Identify drawdown periods
        drawdown_periods = self._identify_drawdown_periods(equity_curve)

        backtest_id = f"bt_{config.symbol}_{int(datetime.now().timestamp())}"

        result = BacktestResult(
            backtest_id=backtest_id,
            symbol=config.symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            strategy_id=config.strategy.strategy_id,
            initial_capital=config.strategy.initial_capital,
            final_capital=equity_curve[-1]["equity"],
            metrics=self._metrics_to_dict(metrics),
            equity_curve=[
                {"timestamp": e["timestamp"].isoformat(), "equity": e["equity"]}
                for e in equity_curve
            ],
            trades=[self._trade_to_dict(t) for t in trades],
            drawdown_periods=[
                {
                    "start": d["start"].isoformat(),
                    "end": d["end"].isoformat(),
                    "depth_pct": d["depth_pct"],
                }
                for d in drawdown_periods
            ],
        )

        self.results_cache[backtest_id] = result
        return result

    async def run_monte_carlo(self, config: MonteCarloConfig) -> MonteCarloResult:
        """Run Monte Carlo simulation"""
        logger.info(f"Starting Monte Carlo simulation ({config.num_simulations} runs)")

        # Run base backtest
        base_result = await self.run_backtest(config.backtest_config)
        base_trades = [self._dict_to_trade(t) for t in base_result.trades]

        simulated_returns = []
        all_metrics = []

        for i in range(config.num_simulations):
            # Randomize trades
            if config.randomize_trades:
                simulated_trades = self._randomize_trade_order(base_trades)
            else:
                simulated_trades = base_trades.copy()

            # Add price noise if enabled
            if config.randomize_prices:
                simulated_trades = self._add_price_noise(simulated_trades)

            # Calculate metrics
            metrics = self._calculate_metrics(
                simulated_trades, config.backtest_config.strategy.initial_capital
            )

            simulated_returns.append(metrics.total_return_pct)
            all_metrics.append(metrics)

        # Calculate statistics
        returns_array = np.array(simulated_returns)
        confidence_interval = self._calculate_confidence_interval(
            returns_array, config.confidence_level
        )

        risk_of_ruin = self._calculate_risk_of_ruin(all_metrics)

        # Find best/worst cases
        best_idx = np.argmax(returns_array)
        worst_idx = np.argmin(returns_array)

        simulation_id = (
            f"mc_{config.backtest_config.symbol}_{int(datetime.now().timestamp())}"
        )

        return MonteCarloResult(
            simulation_id=simulation_id,
            num_simulations=config.num_simulations,
            confidence_level=config.confidence_level,
            base_metrics=self._metrics_to_dict(
                self._calculate_metrics(
                    base_trades, config.backtest_config.strategy.initial_capital
                )
            ),
            simulated_returns=simulated_returns,
            confidence_interval={
                "lower": float(confidence_interval[0]),
                "upper": float(confidence_interval[1]),
                "median": float(np.median(returns_array)),
            },
            risk_of_ruin=risk_of_ruin,
            expected_return=float(np.mean(returns_array)),
            worst_case=self._metrics_to_dict(all_metrics[worst_idx]),
            best_case=self._metrics_to_dict(all_metrics[best_idx]),
            percentile_metrics={
                10: self._metrics_to_dict(all_metrics[int(len(all_metrics) * 0.1)]),
                50: self._metrics_to_dict(all_metrics[int(len(all_metrics) * 0.5)]),
                90: self._metrics_to_dict(all_metrics[int(len(all_metrics) * 0.9)]),
            },
        )

    async def run_walk_forward(self, config: WalkForwardConfig) -> WalkForwardResult:
        """Run walk-forward analysis"""
        logger.info("Starting walk-forward analysis")

        start_date = datetime.fromisoformat(config.backtest_config.start_date)
        end_date = datetime.fromisoformat(config.backtest_config.end_date)

        in_sample_results = []
        out_sample_results = []
        optimal_params = []

        current_start = start_date

        while current_start < end_date:
            # Define in-sample period
            in_sample_end = current_start + timedelta(days=config.in_sample_days)
            if in_sample_end > end_date:
                break

            # Optimize on in-sample data
            optimal_parameters = await self._optimize_parameters(
                config.backtest_config,
                current_start.isoformat(),
                in_sample_end.isoformat(),
                config.optimize_metric,
            )

            optimal_params.append(
                {"period": current_start.isoformat(), "parameters": optimal_parameters}
            )

            # Test on out-of-sample data
            out_sample_start = in_sample_end
            out_sample_end = out_sample_start + timedelta(days=config.out_sample_days)

            if out_sample_end > end_date:
                out_sample_end = end_date

            # Run backtest with optimal parameters
            test_config = config.backtest_config.copy(deep=True)
            test_config.start_date = out_sample_start.isoformat()
            test_config.end_date = out_sample_end.isoformat()
            test_config.strategy.parameters = optimal_parameters

            result = await self.run_backtest(test_config)

            out_sample_results.append(result.metrics)

            # Move window
            if config.anchor:
                # Anchored: keep start, extend end
                current_start = start_date
            else:
                # Rolling: move both start and end
                current_start = out_sample_start

        # Calculate overall metrics
        overall_metrics = self._aggregate_walk_forward_metrics(out_sample_results)

        # Calculate degradation factor (out-sample vs in-sample performance)
        degradation_factor = self._calculate_degradation_factor(
            in_sample_results, out_sample_results
        )

        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(out_sample_results)

        analysis_id = (
            f"wf_{config.backtest_config.symbol}_{int(datetime.now().timestamp())}"
        )

        return WalkForwardResult(
            analysis_id=analysis_id,
            num_periods=len(out_sample_results),
            in_sample_metrics=in_sample_results,
            out_sample_metrics=out_sample_results,
            overall_metrics=overall_metrics,
            degradation_factor=degradation_factor,
            consistency_score=consistency_score,
            optimal_parameters=optimal_params,
        )

    # Helper methods

    async def _fetch_market_data(
        self, symbol: str, start: str, end: str, timeframe: str
    ) -> List[Dict]:
        """Fetch historical market data"""
        # Mock implementation - integrate with actual data source
        import random

        dates = []
        current = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        candles = []
        price = 50000.0

        while current < end_dt:
            change = random.uniform(-0.02, 0.02)
            price *= 1 + change

            candles.append(
                {
                    "timestamp": current,
                    "open": price * (1 + random.uniform(-0.001, 0.001)),
                    "high": price * (1 + random.uniform(0, 0.01)),
                    "low": price * (1 + random.uniform(-0.01, 0)),
                    "close": price,
                    "volume": random.uniform(100, 1000),
                }
            )

            current += timedelta(hours=1)

        return candles

    async def _generate_signals(
        self, candles: List[Dict], strategy: BacktestStrategy
    ) -> List[Dict]:
        """Generate trading signals from strategy"""
        # Mock implementation - use actual strategy
        signals = []
        for i, candle in enumerate(candles):
            if i % 10 == 0:  # Buy every 10 candles
                signals.append(
                    {
                        "timestamp": candle["timestamp"],
                        "signal": "buy",
                        "price": candle["close"],
                    }
                )
            elif i % 10 == 5:  # Sell 5 candles later
                signals.append(
                    {
                        "timestamp": candle["timestamp"],
                        "signal": "sell",
                        "price": candle["close"],
                    }
                )

        return signals

    async def _simulate_trades(
        self, candles: List[Dict], signals: List[Dict], config: BacktestConfig
    ) -> List[Trade]:
        """Simulate trade execution"""
        trades = []
        position = None

        for signal in signals:
            price = signal["price"]
            slippage = price * config.slippage_pct
            commission = price * config.commission_rate

            if signal["signal"] == "buy" and position is None:
                position = {
                    "entry_time": signal["timestamp"],
                    "entry_price": price + slippage,
                    "size": config.strategy.position_size_pct
                    * config.strategy.initial_capital
                    / price,
                }

            elif signal["signal"] == "sell" and position is not None:
                exit_price = price - slippage
                pnl = (exit_price - position["entry_price"]) * position[
                    "size"
                ] - 2 * commission
                pnl_pct = (exit_price / position["entry_price"] - 1) * 100

                trades.append(
                    Trade(
                        entry_time=position["entry_time"],
                        exit_time=signal["timestamp"],
                        entry_price=position["entry_price"],
                        exit_price=exit_price,
                        side="long",
                        size=position["size"],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        commission=2 * commission,
                        slippage=2 * slippage,
                    )
                )

                position = None

        return trades

    def _calculate_metrics(
        self, trades: List[Trade], initial_capital: float
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return self._empty_metrics()

        total_return = sum(t.pnl for t in trades)
        total_return_pct = (total_return / initial_capital) * 100

        returns = [t.pnl_pct for t in trades]
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        # Sharpe ratio
        returns_array = np.array(returns)
        sharpe = (
            (np.mean(returns_array) / np.std(returns_array)) * np.sqrt(252)
            if np.std(returns_array) > 0
            else 0
        )

        # Sortino ratio (downside deviation)
        downside_returns = returns_array[returns_array < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1
        sortino = (
            (np.mean(returns_array) / downside_std) * np.sqrt(252)
            if downside_std > 0
            else 0
        )

        # Max drawdown
        equity_curve = self._build_equity_curve(trades, initial_capital)
        max_dd = self._calculate_max_drawdown(equity_curve)

        # Calmar ratio
        annualized_return = (
            total_return_pct * (252 / len(trades)) if len(trades) > 0 else 0
        )
        calmar = annualized_return / abs(max_dd) if max_dd != 0 else 0

        # Win rate and profit factor
        win_rate = len(winning_trades) / len(trades) if trades else 0
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Average metrics
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        avg_trade = total_return / len(trades) if trades else 0

        # Holding period
        holding_periods = [
            (t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades
        ]
        avg_holding = np.mean(holding_periods) if holding_periods else 0

        # Recovery factor
        recovery_factor = total_return / abs(max_dd) if max_dd != 0 else 0

        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))

        return PerformanceMetrics(
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_dd * initial_capital,
            max_drawdown_pct=max_dd,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            num_trades=len(trades),
            num_winning=len(winning_trades),
            num_losing=len(losing_trades),
            avg_holding_period_hours=avg_holding,
            recovery_factor=recovery_factor,
            expectancy=expectancy,
        )

    def _build_equity_curve(
        self, trades: List[Trade], initial_capital: float
    ) -> List[Dict]:
        """Build equity curve from trades"""
        equity = initial_capital
        curve = [{"timestamp": datetime.now(), "equity": equity}]

        for trade in trades:
            equity += trade.pnl
            curve.append({"timestamp": trade.exit_time, "equity": equity})

        return curve

    def _calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """Calculate maximum drawdown percentage"""
        peak = equity_curve[0]["equity"]
        max_dd = 0.0

        for point in equity_curve:
            if point["equity"] > peak:
                peak = point["equity"]
            dd = (peak - point["equity"]) / peak
            if dd > max_dd:
                max_dd = dd

        return max_dd

    def _identify_drawdown_periods(self, equity_curve: List[Dict]) -> List[Dict]:
        """Identify significant drawdown periods"""
        # Implementation omitted for brevity
        return []

    def _randomize_trade_order(self, trades: List[Trade]) -> List[Trade]:
        """Randomize trade order for Monte Carlo"""
        import random

        randomized = trades.copy()
        random.shuffle(randomized)
        return randomized

    def _add_price_noise(self, trades: List[Trade]) -> List[Trade]:
        """Add random noise to trade prices"""
        import random

        noisy_trades = []
        for trade in trades:
            noise = random.uniform(-0.005, 0.005)
            new_trade = Trade(
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                entry_price=trade.entry_price * (1 + noise),
                exit_price=trade.exit_price * (1 + noise),
                side=trade.side,
                size=trade.size,
                pnl=trade.pnl * (1 + noise),
                pnl_pct=trade.pnl_pct,
                commission=trade.commission,
                slippage=trade.slippage,
            )
            noisy_trades.append(new_trade)
        return noisy_trades

    def _calculate_confidence_interval(
        self, returns: np.ndarray, confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval"""
        alpha = 1 - confidence_level
        lower = np.percentile(returns, alpha / 2 * 100)
        upper = np.percentile(returns, (1 - alpha / 2) * 100)
        return (lower, upper)

    def _calculate_risk_of_ruin(self, metrics_list: List[PerformanceMetrics]) -> float:
        """Calculate risk of ruin (probability of losing all capital)"""
        ruined = sum(1 for m in metrics_list if m.total_return_pct <= -90)
        return ruined / len(metrics_list)

    async def _optimize_parameters(
        self, config: BacktestConfig, start: str, end: str, metric: str
    ) -> Dict[str, float]:
        """Optimize strategy parameters"""
        # Mock implementation - use actual optimization
        return config.strategy.parameters

    def _aggregate_walk_forward_metrics(self, results: List[Dict]) -> Dict:
        """Aggregate walk-forward results"""
        if not results:
            return {}

        return {
            "avg_return": np.mean([r.get("total_return_pct", 0) for r in results]),
            "avg_sharpe": np.mean([r.get("sharpe_ratio", 0) for r in results]),
            "consistency": np.std([r.get("total_return_pct", 0) for r in results]),
        }

    def _calculate_degradation_factor(
        self, in_sample: List[Dict], out_sample: List[Dict]
    ) -> float:
        """Calculate performance degradation from in-sample to out-sample"""
        if not in_sample or not out_sample:
            return 0.0

        in_avg = np.mean([r.get("total_return_pct", 0) for r in in_sample])
        out_avg = np.mean([r.get("total_return_pct", 0) for r in out_sample])

        return (in_avg - out_avg) / in_avg if in_avg != 0 else 0.0

    def _calculate_consistency_score(self, results: List[Dict]) -> float:
        """Calculate consistency score (inverse of std dev)"""
        returns = [r.get("total_return_pct", 0) for r in results]
        return 1.0 / (1.0 + np.std(returns))

    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics"""
        return PerformanceMetrics(
            total_return=0,
            total_return_pct=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            max_drawdown=0,
            max_drawdown_pct=0,
            win_rate=0,
            profit_factor=0,
            avg_win=0,
            avg_loss=0,
            avg_trade=0,
            num_trades=0,
            num_winning=0,
            num_losing=0,
            avg_holding_period_hours=0,
            recovery_factor=0,
            expectancy=0,
        )

    def _metrics_to_dict(self, metrics: PerformanceMetrics) -> Dict:
        """Convert metrics to dictionary"""
        return {
            "total_return": metrics.total_return,
            "total_return_pct": metrics.total_return_pct,
            "sharpe_ratio": metrics.sharpe_ratio,
            "sortino_ratio": metrics.sortino_ratio,
            "calmar_ratio": metrics.calmar_ratio,
            "max_drawdown": metrics.max_drawdown,
            "max_drawdown_pct": metrics.max_drawdown_pct,
            "win_rate": metrics.win_rate,
            "profit_factor": metrics.profit_factor,
            "avg_win": metrics.avg_win,
            "avg_loss": metrics.avg_loss,
            "num_trades": metrics.num_trades,
        }

    def _trade_to_dict(self, trade: Trade) -> Dict:
        """Convert trade to dictionary"""
        return {
            "entry_time": trade.entry_time.isoformat(),
            "exit_time": trade.exit_time.isoformat(),
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "side": trade.side,
            "pnl": trade.pnl,
            "pnl_pct": trade.pnl_pct,
        }

    def _dict_to_trade(self, data: Dict) -> Trade:
        """Convert dictionary to trade"""
        return Trade(
            entry_time=datetime.fromisoformat(data["entry_time"]),
            exit_time=datetime.fromisoformat(data["exit_time"]),
            entry_price=data["entry_price"],
            exit_price=data["exit_price"],
            side=data["side"],
            size=data.get("size", 1.0),
            pnl=data["pnl"],
            pnl_pct=data["pnl_pct"],
            commission=data.get("commission", 0),
            slippage=data.get("slippage", 0),
        )


# Global engine instance
backtest_engine = BacktestEngine()


@router.post("/run", response_model=BacktestResult)
async def run_backtest(config: BacktestConfig):
    """Run standard backtest"""
    try:
        result = await backtest_engine.run_backtest(config)
        return result
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monte-carlo", response_model=MonteCarloResult)
async def run_monte_carlo_simulation(config: MonteCarloConfig):
    """Run Monte Carlo simulation"""
    try:
        result = await backtest_engine.run_monte_carlo(config)
        return result
    except Exception as e:
        logger.error(f"Monte Carlo simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/walk-forward", response_model=WalkForwardResult)
async def run_walk_forward_analysis(config: WalkForwardConfig):
    """Run walk-forward analysis"""
    try:
        result = await backtest_engine.run_walk_forward(config)
        return result
    except Exception as e:
        logger.error(f"Walk-forward analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(backtest_id: str):
    """Get backtest result by ID"""
    if backtest_id not in backtest_engine.results_cache:
        raise HTTPException(status_code=404, detail="Backtest not found")

    return backtest_engine.results_cache[backtest_id]
