"""
Strategy Template Service - Built-in strategy templates
"""
from typing import Dict, List, Optional
from enum import Enum


class StrategyType(str, Enum):
    """Strategy types"""
    RSI = "rsi"
    MACD = "macd"
    BREAKOUT = "breakout"
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    CUSTOM = "custom"


class StrategyCategory(str, Enum):
    """Strategy categories"""
    TECHNICAL = "technical"
    ML = "ml"
    HYBRID = "hybrid"


class StrategyTemplate:
    """Base class for strategy templates"""
    
    def __init__(
        self,
        name: str,
        description: str,
        strategy_type: StrategyType,
        category: StrategyCategory,
        config: Dict,
        logic: Optional[Dict] = None
    ):
        self.name = name
        self.description = description
        self.strategy_type = strategy_type
        self.category = category
        self.config = config
        self.logic = logic or {}
    
    def to_dict(self) -> Dict:
        """Convert template to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type.value,
            "category": self.category.value,
            "config": self.config,
            "logic": self.logic
        }


class StrategyTemplateService:
    """Service for managing strategy templates"""
    
    # Built-in templates
    TEMPLATES: Dict[str, StrategyTemplate] = {}
    
    @classmethod
    def initialize_templates(cls):
        """Initialize built-in strategy templates"""
        
        # RSI Strategy Template
        cls.TEMPLATES[StrategyType.RSI.value] = StrategyTemplate(
            name="RSI Mean Reversion",
            description="Mean reversion strategy using RSI (Relative Strength Index). "
                       "Buys when RSI is oversold (<30) and sells when overbought (>70).",
            strategy_type=StrategyType.RSI,
            category=StrategyCategory.TECHNICAL,
            config={
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70,
                "stop_loss_pct": 2.0,
                "take_profit_pct": 5.0,
                "timeframe": "1h",
                "position_size_pct": 10
            },
            logic={
                "indicators": [
                    {"name": "RSI", "period": 14}
                ],
                "buy_conditions": [
                    {"indicator": "RSI", "operator": "<", "value": 30}
                ],
                "sell_conditions": [
                    {"indicator": "RSI", "operator": ">", "value": 70}
                ]
            }
        )
        
        # MACD Strategy Template
        cls.TEMPLATES[StrategyType.MACD.value] = StrategyTemplate(
            name="MACD Crossover",
            description="Trend following strategy using MACD (Moving Average Convergence Divergence). "
                       "Buys on bullish crossover and sells on bearish crossover.",
            strategy_type=StrategyType.MACD,
            category=StrategyCategory.TECHNICAL,
            config={
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "stop_loss_pct": 2.5,
                "take_profit_pct": 6.0,
                "timeframe": "4h",
                "position_size_pct": 10
            },
            logic={
                "indicators": [
                    {"name": "MACD", "fast": 12, "slow": 26, "signal": 9}
                ],
                "buy_conditions": [
                    {"indicator": "MACD", "crossover": "above", "signal_line": True}
                ],
                "sell_conditions": [
                    {"indicator": "MACD", "crossover": "below", "signal_line": True}
                ]
            }
        )
        
        # Breakout Strategy Template
        cls.TEMPLATES[StrategyType.BREAKOUT.value] = StrategyTemplate(
            name="Breakout Trading",
            description="Breakout strategy that buys when price breaks above resistance "
                       "and sells when it breaks below support. Uses volume confirmation.",
            strategy_type=StrategyType.BREAKOUT,
            category=StrategyCategory.TECHNICAL,
            config={
                "lookback_period": 20,
                "volume_multiplier": 1.5,
                "stop_loss_pct": 3.0,
                "take_profit_pct": 8.0,
                "timeframe": "1h",
                "position_size_pct": 10
            },
            logic={
                "indicators": [
                    {"name": "High", "period": 20},
                    {"name": "Low", "period": 20},
                    {"name": "Volume", "period": 20}
                ],
                "buy_conditions": [
                    {"price": ">", "resistance": "20_high"},
                    {"volume": ">", "avg_volume": "*", "multiplier": 1.5}
                ],
                "sell_conditions": [
                    {"price": "<", "support": "20_low"}
                ]
            }
        )
        
        # LSTM Strategy Template
        cls.TEMPLATES[StrategyType.LSTM.value] = StrategyTemplate(
            name="LSTM Neural Network",
            description="Deep learning strategy using LSTM (Long Short-Term Memory) neural network. "
                       "Predicts price movements based on historical patterns.",
            strategy_type=StrategyType.LSTM,
            category=StrategyCategory.ML,
            config={
                "sequence_length": 60,
                "lstm_units": 128,
                "dropout": 0.2,
                "epochs": 100,
                "batch_size": 32,
                "lookback_periods": 60,
                "confidence_threshold": 0.7,
                "stop_loss_pct": 3.0,
                "take_profit_pct": 7.0,
                "timeframe": "1h",
                "position_size_pct": 10
            },
            logic={
                "model_type": "LSTM",
                "features": ["close", "volume", "high", "low", "open"],
                "prediction_horizon": 24,
                "buy_conditions": [
                    {"prediction": ">", "confidence": 0.7, "direction": "up"}
                ],
                "sell_conditions": [
                    {"prediction": ">", "confidence": 0.7, "direction": "down"}
                ]
            }
        )
        
        # Transformer Strategy Template
        cls.TEMPLATES[StrategyType.TRANSFORMER.value] = StrategyTemplate(
            name="Transformer Attention Model",
            description="State-of-the-art strategy using Transformer architecture with attention mechanism. "
                       "Captures long-range dependencies in price patterns.",
            strategy_type=StrategyType.TRANSFORMER,
            category=StrategyCategory.ML,
            config={
                "sequence_length": 128,
                "d_model": 256,
                "num_heads": 8,
                "num_layers": 6,
                "dropout": 0.1,
                "epochs": 150,
                "batch_size": 32,
                "lookback_periods": 128,
                "confidence_threshold": 0.75,
                "stop_loss_pct": 3.5,
                "take_profit_pct": 8.5,
                "timeframe": "4h",
                "position_size_pct": 10
            },
            logic={
                "model_type": "Transformer",
                "features": ["close", "volume", "high", "low", "open", "indicators"],
                "prediction_horizon": 48,
                "attention_mechanism": True,
                "buy_conditions": [
                    {"prediction": ">", "confidence": 0.75, "direction": "up"}
                ],
                "sell_conditions": [
                    {"prediction": ">", "confidence": 0.75, "direction": "down"}
                ]
            }
        )
    
    @classmethod
    def get_template(cls, strategy_type: str) -> Optional[StrategyTemplate]:
        """Get a template by type"""
        if not cls.TEMPLATES:
            cls.initialize_templates()
        return cls.TEMPLATES.get(strategy_type)
    
    @classmethod
    def get_all_templates(cls) -> List[Dict]:
        """Get all templates"""
        if not cls.TEMPLATES:
            cls.initialize_templates()
        return [template.to_dict() for template in cls.TEMPLATES.values()]
    
    @classmethod
    def get_templates_by_category(cls, category: str) -> List[Dict]:
        """Get templates by category"""
        if not cls.TEMPLATES:
            cls.initialize_templates()
        return [
            template.to_dict()
            for template in cls.TEMPLATES.values()
            if template.category.value == category
        ]


# Initialize templates on module import
StrategyTemplateService.initialize_templates()

# Global service instance
template_service = StrategyTemplateService()
