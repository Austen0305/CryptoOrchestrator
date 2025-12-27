"""
Strategy optimizer for backtesting
"""

import os
import sqlite3
import json
import asyncio
import random
import math
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel
from datetime import datetime
import logging
import uuid
from concurrent.futures import ProcessPoolExecutor
import itertools

from ..backtesting_engine import BacktestingEngine, BacktestConfig, BacktestResult
from ..ml.ensemble_engine import MarketData

logger = logging.getLogger(__name__)


class OptimizationResult(BaseModel):
    id: str
    strategy_name: str
    parameters: Dict[str, Any]
    fitness_score: float
    backtest_results: Dict[str, Any]
    created_at: datetime


class ParameterRange(BaseModel):
    min: float
    max: float
    step: Optional[float] = None


class OptimizationConfig(BaseModel):
    strategy_name: str
    parameters: Dict[str, ParameterRange]
    population_size: int = 50
    generations: int = 20
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    tournament_size: int = 5


class StrategyOptimizer:
    """Strategy optimizer using genetic algorithms and parameter sweep"""

    def __init__(self):
        self.db_path = os.getenv("STRATEGY_OPTIMIZATION_DB", "strategy_optimization.db")
        self.backtesting_engine = BacktestingEngine()
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for storing optimization results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS optimization_results (
                    id TEXT PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    fitness_score REAL NOT NULL,
                    backtest_results TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_strategy_name ON optimization_results(strategy_name)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_fitness_score ON optimization_results(fitness_score DESC)
            """
            )
            conn.commit()

    async def optimize_strategy(
        self, config: OptimizationConfig, historical_data: List[MarketData], bot_id: str
    ) -> List[OptimizationResult]:
        """Optimize strategy parameters using genetic algorithm"""
        logger.info(f"Starting genetic optimization for {config.strategy_name}")

        # Initialize population
        population = self._initialize_population(config)

        best_results = []

        for generation in range(config.generations):
            logger.info(f"Generation {generation + 1}/{config.generations}")

            # Evaluate fitness for current population
            fitness_scores = await self._evaluate_population(
                population, historical_data, bot_id
            )

            # Store best result from this generation
            best_idx = fitness_scores.index(max(fitness_scores))
            best_params = population[best_idx]
            best_score = fitness_scores[best_idx]

            # Create backtest config for best parameters
            backtest_config = BacktestConfig(
                botId=bot_id, initialBalance=1000.0, commission=0.001
            )

            # Run backtest with best parameters
            backtest_result = await self.backtesting_engine.run_backtest(
                backtest_config, historical_data
            )

            # Store optimization result
            result = OptimizationResult(
                id=str(uuid.uuid4()),
                strategy_name=config.strategy_name,
                parameters=best_params,
                fitness_score=best_score,
                backtest_results=backtest_result.dict(),
                created_at=datetime.now(),
            )

            await self._save_optimization_result(result)
            best_results.append(result)

            # Create next generation
            population = self._create_next_generation(
                population, fitness_scores, config
            )

        logger.info(f"Optimization completed for {config.strategy_name}")
        return best_results[-5:]  # Return last 5 generations' best results

    async def run_parameter_sweep(
        self,
        param_ranges: Dict[str, ParameterRange],
        strategy_name: str,
        historical_data: List[MarketData],
        bot_id: str,
        max_combinations: int = 1000,
    ) -> Dict[str, Any]:
        """Run parameter sweep analysis"""
        logger.info(f"Starting parameter sweep for {strategy_name}")

        # Generate all parameter combinations
        param_combinations = self._generate_parameter_combinations(
            param_ranges, max_combinations
        )

        results = []

        # Evaluate each combination
        for i, params in enumerate(param_combinations):
            if i % 10 == 0:
                logger.info(f"Evaluating combination {i + 1}/{len(param_combinations)}")

            try:
                # Create backtest config with current parameters
                backtest_config = BacktestConfig(
                    botId=bot_id, initialBalance=1000.0, commission=0.001
                )

                # Run backtest
                backtest_result = await self.backtesting_engine.run_backtest(
                    backtest_config, historical_data
                )

                # Calculate fitness score (Sharpe ratio + total return)
                fitness_score = backtest_result.sharpeRatio + (
                    backtest_result.totalReturn * 0.1
                )

                result = OptimizationResult(
                    id=str(uuid.uuid4()),
                    strategy_name=strategy_name,
                    parameters=params,
                    fitness_score=fitness_score,
                    backtest_results=backtest_result.dict(),
                    created_at=datetime.now(),
                )

                await self._save_optimization_result(result)
                results.append(result)

            except Exception as e:
                logger.error(f"Error evaluating parameters {params}: {e}")
                continue

        # Sort by fitness score
        results.sort(key=lambda x: x.fitness_score, reverse=True)

        # Calculate statistics
        fitness_scores = [r.fitness_score for r in results]
        best_params = results[0].parameters if results else {}
        best_score = results[0].fitness_score if results else 0

        return {
            "total_combinations": len(param_combinations),
            "evaluated_combinations": len(results),
            "best_parameters": best_params,
            "best_fitness_score": best_score,
            "average_fitness": (
                sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
            ),
            "fitness_std": (
                math.sqrt(
                    sum(
                        (x - (sum(fitness_scores) / len(fitness_scores))) ** 2
                        for x in fitness_scores
                    )
                    / len(fitness_scores)
                )
                if fitness_scores
                else 0
            ),
            "top_results": [r.dict() for r in results[:10]],
        }

    async def get_optimal_parameters(
        self,
        strategy_name: str,
        market_conditions: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[OptimizationResult]:
        """Get optimal parameters for market conditions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, strategy_name, parameters, fitness_score, backtest_results, created_at
                FROM optimization_results
                WHERE strategy_name = ?
                ORDER BY fitness_score DESC
                LIMIT ?
            """,
                (strategy_name, limit),
            )
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                OptimizationResult(
                    id=row[0],
                    strategy_name=row[1],
                    parameters=json.loads(row[2]),
                    fitness_score=row[3],
                    backtest_results=json.loads(row[4]),
                    created_at=datetime.fromisoformat(row[5]),
                )
            )

        return results

    def _initialize_population(
        self, config: OptimizationConfig
    ) -> List[Dict[str, Any]]:
        """Initialize random population"""
        population = []
        for _ in range(config.population_size):
            individual = {}
            for param_name, param_range in config.parameters.items():
                if param_range.step:
                    # Discrete parameter
                    steps = (
                        int((param_range.max - param_range.min) / param_range.step) + 1
                    )
                    individual[param_name] = (
                        param_range.min
                        + random.randint(0, steps - 1) * param_range.step
                    )
                else:
                    # Continuous parameter
                    individual[param_name] = random.uniform(
                        param_range.min, param_range.max
                    )
            population.append(individual)
        return population

    async def _evaluate_population(
        self,
        population: List[Dict[str, Any]],
        historical_data: List[MarketData],
        bot_id: str,
    ) -> List[float]:
        """Evaluate fitness of population"""
        fitness_scores = []

        for params in population:
            try:
                # Create backtest config with current parameters
                backtest_config = BacktestConfig(
                    botId=bot_id, initialBalance=1000.0, commission=0.001
                )

                # Run backtest
                backtest_result = await self.backtesting_engine.run_backtest(
                    backtest_config, historical_data
                )

                # Calculate fitness score (weighted combination of metrics)
                fitness_score = (
                    backtest_result.sharpeRatio * 0.4
                    + backtest_result.totalReturn * 0.3
                    + backtest_result.winRate * 0.2
                    + (
                        backtest_result.profitFactor
                        if backtest_result.profitFactor != float("inf")
                        else 10
                    )
                    * 0.1
                )

                fitness_scores.append(fitness_score)

            except Exception as e:
                logger.error(f"Error evaluating parameters {params}: {e}")
                fitness_scores.append(-999)  # Very low score for failed evaluations

        return fitness_scores

    def _create_next_generation(
        self,
        population: List[Dict[str, Any]],
        fitness_scores: List[float],
        config: OptimizationConfig,
    ) -> List[Dict[str, Any]]:
        """Create next generation using tournament selection, crossover, and mutation"""
        new_population = []

        while len(new_population) < config.population_size:
            # Tournament selection
            parent1 = self._tournament_selection(
                population, fitness_scores, config.tournament_size
            )
            parent2 = self._tournament_selection(
                population, fitness_scores, config.tournament_size
            )

            # Crossover
            if random.random() < config.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            # Mutation
            child1 = self._mutate(child1, config.mutation_rate, config.parameters)
            child2 = self._mutate(child2, config.mutation_rate, config.parameters)

            new_population.extend([child1, child2])

        return new_population[: config.population_size]

    def _tournament_selection(
        self,
        population: List[Dict[str, Any]],
        fitness_scores: List[float],
        tournament_size: int,
    ) -> Dict[str, Any]:
        """Tournament selection"""
        tournament = random.sample(
            list(zip(population, fitness_scores)), tournament_size
        )
        return max(tournament, key=lambda x: x[1])[0]

    def _crossover(
        self, parent1: Dict[str, Any], parent2: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Single point crossover"""
        if not parent1:
            return parent1, parent2

        crossover_point = random.randint(1, len(parent1) - 1)
        child1 = {}
        child2 = {}

        for i, key in enumerate(parent1.keys()):
            if i < crossover_point:
                child1[key] = parent1[key]
                child2[key] = parent2[key]
            else:
                child1[key] = parent2[key]
                child2[key] = parent1[key]

        return child1, child2

    def _mutate(
        self,
        individual: Dict[str, Any],
        mutation_rate: float,
        parameters: Dict[str, ParameterRange],
    ) -> Dict[str, Any]:
        """Gaussian mutation"""
        mutated = individual.copy()

        for param_name, param_range in parameters.items():
            if random.random() < mutation_rate:
                current_value = mutated[param_name]

                # Gaussian mutation
                mutation = random.gauss(0, (param_range.max - param_range.min) * 0.1)
                new_value = current_value + mutation

                # Clamp to bounds
                new_value = max(param_range.min, min(param_range.max, new_value))

                # If discrete, round to step
                if param_range.step:
                    new_value = round(new_value / param_range.step) * param_range.step

                mutated[param_name] = new_value

        return mutated

    def _generate_parameter_combinations(
        self, param_ranges: Dict[str, ParameterRange], max_combinations: int
    ) -> List[Dict[str, Any]]:
        """Generate parameter combinations for sweep"""
        # Create discrete values for each parameter
        param_values = {}
        for param_name, param_range in param_ranges.items():
            if param_range.step:
                values = []
                current = param_range.min
                while current <= param_range.max:
                    values.append(current)
                    current += param_range.step
                param_values[param_name] = values
            else:
                # For continuous parameters, create 10 evenly spaced values
                step = (param_range.max - param_range.min) / 9
                param_values[param_name] = [
                    param_range.min + i * step for i in range(10)
                ]

        # Generate combinations
        param_names = list(param_values.keys())
        all_combinations = list(
            itertools.product(*[param_values[name] for name in param_names])
        )

        # Limit combinations if too many
        if len(all_combinations) > max_combinations:
            # Randomly sample combinations
            indices = random.sample(range(len(all_combinations)), max_combinations)
            all_combinations = [all_combinations[i] for i in indices]

        # Convert to dict format
        combinations = []
        for combo in all_combinations:
            combinations.append(dict(zip(param_names, combo)))

        return combinations

    async def _save_optimization_result(self, result: OptimizationResult):
        """Save optimization result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO optimization_results (id, strategy_name, parameters, fitness_score, backtest_results, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    result.id,
                    result.strategy_name,
                    json.dumps(result.parameters),
                    result.fitness_score,
                    json.dumps(result.backtest_results),
                    result.created_at.isoformat(),
                ),
            )
            conn.commit()
