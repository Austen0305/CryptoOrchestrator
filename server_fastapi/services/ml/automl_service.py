"""
AutoML Service - Automated hyperparameter tuning and optimization
"""
from typing import Dict, Any, Optional, List, Callable, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

# Try importing optimization libraries
try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not available; Bayesian optimization will be limited.")

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer, Categorical
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    logger.warning("scikit-optimize not available; Bayesian optimization will be limited.")


class SearchStrategy(str, Enum):
    """Hyperparameter search strategies"""
    GRID = "grid"
    RANDOM = "random"
    BAYESIAN = "bayesian"


class HyperparameterRange(BaseModel):
    """Hyperparameter range definition"""
    name: str
    param_type: str  # 'int', 'float', 'categorical'
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    values: Optional[List[Any]] = None  # For categorical


class OptimizationConfig(BaseModel):
    """AutoML optimization configuration"""
    model_type: str  # 'lstm', 'gru', 'transformer', 'xgboost'
    hyperparameter_ranges: Dict[str, HyperparameterRange]
    search_strategy: SearchStrategy = SearchStrategy.BAYESIAN
    n_trials: int = 100
    n_jobs: int = 1  # Parallel trials
    timeout: Optional[int] = None  # Timeout in seconds
    metric: str = "accuracy"  # Metric to optimize
    direction: str = "maximize"  # 'maximize' or 'minimize'


class OptimizationResult(BaseModel):
    """Optimization result"""
    best_params: Dict[str, Any]
    best_score: float
    n_trials: int
    optimization_time: float
    trial_results: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AutoMLService:
    """Service for automated machine learning and hyperparameter tuning"""
    
    def __init__(self):
        logger.info("AutoML Service initialized")
    
    def optimize_hyperparameters(
        self,
        config: OptimizationConfig,
        objective_function: Callable[[Dict[str, Any]], float],
        model_engine: Any = None
    ) -> OptimizationResult:
        """Optimize hyperparameters using specified search strategy"""
        try:
            if config.search_strategy == SearchStrategy.GRID:
                return self._grid_search(config, objective_function, model_engine)
            elif config.search_strategy == SearchStrategy.RANDOM:
                return self._random_search(config, objective_function, model_engine)
            elif config.search_strategy == SearchStrategy.BAYESIAN:
                return self._bayesian_optimization(config, objective_function, model_engine)
            else:
                raise ValueError(f"Unknown search strategy: {config.search_strategy}")
        
        except Exception as e:
            logger.error(f"Hyperparameter optimization failed: {e}")
            raise
    
    def _grid_search(
        self,
        config: OptimizationConfig,
        objective_function: Callable[[Dict[str, Any]], float],
        model_engine: Any
    ) -> OptimizationResult:
        """Grid search hyperparameter optimization"""
        import itertools
        import random
        import time
        
        start_time = time.time()
        
        # Generate all parameter combinations
        param_combinations = []
        param_names = []
        param_values = []
        
        for name, param_range in config.hyperparameter_ranges.items():
            param_names.append(name)
            
            if param_range.param_type == 'int':
                values = list(range(
                    int(param_range.min),
                    int(param_range.max) + 1,
                    int(param_range.step) if param_range.step else 1
                ))
            elif param_range.param_type == 'float':
                values = np.arange(
                    param_range.min,
                    param_range.max + (param_range.step or 0.1),
                    param_range.step or 0.1
                ).tolist()
            elif param_range.param_type == 'categorical':
                values = param_range.values or []
            else:
                raise ValueError(f"Unknown parameter type: {param_range.param_type}")
            
            param_values.append(values)
        
        # Generate all combinations
        all_combinations = list(itertools.product(*param_values))
        
        # Limit combinations if too many
        if len(all_combinations) > config.n_trials:
            import random
            all_combinations = random.sample(all_combinations, config.n_trials)
        
        trial_results = []
        best_score = float('-inf') if config.direction == 'maximize' else float('inf')
        best_params = {}
        
        for i, combination in enumerate(all_combinations):
            params = dict(zip(param_names, combination))
            
            try:
                score = objective_function(params)
                trial_results.append({
                    'trial': i + 1,
                    'params': params,
                    'score': score
                })
                
                if (config.direction == 'maximize' and score > best_score) or \
                   (config.direction == 'minimize' and score < best_score):
                    best_score = score
                    best_params = params
            except Exception as e:
                logger.warning(f"Trial {i+1} failed: {e}")
                continue
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            n_trials=len(trial_results),
            optimization_time=optimization_time,
            trial_results=trial_results
        )
    
    def _random_search(
        self,
        config: OptimizationConfig,
        objective_function: Callable[[Dict[str, Any]], float],
        model_engine: Any
    ) -> OptimizationResult:
        """Random search hyperparameter optimization"""
        import random
        import time
        
        start_time = time.time()
        
        trial_results = []
        best_score = float('-inf') if config.direction == 'maximize' else float('inf')
        best_params = {}
        
        for i in range(config.n_trials):
            params = {}
            
            # Sample random values for each parameter
            for name, param_range in config.hyperparameter_ranges.items():
                if param_range.param_type == 'int':
                    params[name] = random.randint(int(param_range.min), int(param_range.max))
                elif param_range.param_type == 'float':
                    params[name] = random.uniform(param_range.min, param_range.max)
                elif param_range.param_type == 'categorical':
                    params[name] = random.choice(param_range.values or [])
            
            try:
                score = objective_function(params)
                trial_results.append({
                    'trial': i + 1,
                    'params': params,
                    'score': score
                })
                
                if (config.direction == 'maximize' and score > best_score) or \
                   (config.direction == 'minimize' and score < best_score):
                    best_score = score
                    best_params = params
            except Exception as e:
                logger.warning(f"Trial {i+1} failed: {e}")
                continue
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            n_trials=len(trial_results),
            optimization_time=optimization_time,
            trial_results=trial_results
        )
    
    def _bayesian_optimization(
        self,
        config: OptimizationConfig,
        objective_function: Callable[[Dict[str, Any]], float],
        model_engine: Any
    ) -> OptimizationResult:
        """Bayesian optimization using Optuna or scikit-optimize"""
        import time
        
        start_time = time.time()
        
        # Try Optuna first
        if OPTUNA_AVAILABLE:
            return self._optuna_optimization(config, objective_function, model_engine)
        elif SKOPT_AVAILABLE:
            return self._skopt_optimization(config, objective_function, model_engine)
        else:
            logger.warning("No Bayesian optimization library available, falling back to random search")
            return self._random_search(config, objective_function, model_engine)
    
    def _optuna_optimization(
        self,
        config: OptimizationConfig,
        objective_function: Callable[[Dict[str, Any]], float],
        model_engine: Any
    ) -> OptimizationResult:
        """Bayesian optimization using Optuna"""
        import time
        
        start_time = time.time()
        trial_results = []
        
        def optuna_objective(trial):
            params = {}
            
            for name, param_range in config.hyperparameter_ranges.items():
                if param_range.param_type == 'int':
                    params[name] = trial.suggest_int(
                        name,
                        int(param_range.min),
                        int(param_range.max),
                        step=int(param_range.step) if param_range.step else 1
                    )
                elif param_range.param_type == 'float':
                    params[name] = trial.suggest_float(
                        name,
                        param_range.min,
                        param_range.max,
                        step=param_range.step
                    )
                elif param_range.param_type == 'categorical':
                    params[name] = trial.suggest_categorical(
                        name,
                        param_range.values or []
                    )
            
            score = objective_function(params)
            
            trial_results.append({
                'trial': trial.number + 1,
                'params': params,
                'score': score
            })
            
            return score
        
        study = optuna.create_study(
            direction=config.direction,
            study_name=f"{config.model_type}_optimization"
        )
        
        study.optimize(
            optuna_objective,
            n_trials=config.n_trials,
            n_jobs=config.n_jobs,
            timeout=config.timeout
        )
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            best_params=study.best_params,
            best_score=study.best_value,
            n_trials=len(trial_results),
            optimization_time=optimization_time,
            trial_results=trial_results
        )
    
    def _skopt_optimization(
        self,
        config: OptimizationConfig,
        objective_function: Callable[[Dict[str, Any]], float],
        model_engine: Any
    ) -> OptimizationResult:
        """Bayesian optimization using scikit-optimize"""
        import time
        
        start_time = time.time()
        
        # Define search space
        dimensions = []
        param_names = []
        
        for name, param_range in config.hyperparameter_ranges.items():
            param_names.append(name)
            
            if param_range.param_type == 'int':
                dimensions.append(Integer(int(param_range.min), int(param_range.max)))
            elif param_range.param_type == 'float':
                dimensions.append(Real(param_range.min, param_range.max))
            elif param_range.param_type == 'categorical':
                dimensions.append(Categorical(param_range.values or []))
        
        def skopt_objective(params_list):
            params = dict(zip(param_names, params_list))
            score = objective_function(params)
            return -score if config.direction == 'maximize' else score
        
        result = gp_minimize(
            skopt_objective,
            dimensions,
            n_calls=config.n_trials,
            n_jobs=config.n_jobs,
            random_state=42
        )
        
        best_params = dict(zip(param_names, result.x))
        best_score = -result.fun if config.direction == 'maximize' else result.fun
        
        optimization_time = time.time() - start_time
        
        trial_results = [
            {
                'trial': i + 1,
                'params': dict(zip(param_names, params_list)),
                'score': -score if config.direction == 'maximize' else score
            }
            for i, (params_list, score) in enumerate(zip(result.x_iters, result.func_vals))
        ]
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            n_trials=len(trial_results),
            optimization_time=optimization_time,
            trial_results=trial_results
        )


# Global service instance
automl_service = AutoMLService()
