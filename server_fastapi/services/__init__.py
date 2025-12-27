# Services package
import os
import logging

logger = logging.getLogger(__name__)

# Lazy import ML services to prevent blocking startup with heavy dependencies
# Only import when actually needed, not at module level
_ml_imports_loaded = False
_ml_imports = {}


def _lazy_load_ml_imports():
    """Lazy load ML imports to prevent startup blocking"""
    global _ml_imports_loaded, _ml_imports

    if _ml_imports_loaded:
        return _ml_imports

    # Check if ML features are disabled
    if os.getenv("DISABLE_ML_FEATURES", "false").lower() == "true":
        logger.info("ML features disabled via DISABLE_ML_FEATURES environment variable")
        _ml_imports_loaded = True
        _ml_imports = {
            "EnhancedMLEngine": None,
            "enhanced_ml_engine": None,
            "TechnicalIndicators": None,
            "MLPrediction": None,
            "MarketData": None,
            "EnsembleEngine": None,
            "ensemble_engine": None,
            "EnsemblePrediction": None,
            "NeuralNetworkEngine": None,
            "neural_network_engine": None,
            "NeuralNetworkConfig": None,
        }
        return _ml_imports

    try:
        # Set environment variables to disable CUDA before importing
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

        from .ml.enhanced_ml_engine import (
            EnhancedMLEngine,
            enhanced_ml_engine,
            TechnicalIndicators,
            MLPrediction,
            MarketData,
        )
        from .ml.ensemble_engine import (
            EnsembleEngine,
            ensemble_engine,
            EnsemblePrediction,
        )
        from .ml.neural_network_engine import (
            NeuralNetworkEngine,
            neural_network_engine,
            NeuralNetworkConfig,
        )

        _ml_imports = {
            "EnhancedMLEngine": EnhancedMLEngine,
            "enhanced_ml_engine": enhanced_ml_engine,
            "TechnicalIndicators": TechnicalIndicators,
            "MLPrediction": MLPrediction,
            "MarketData": MarketData,
            "EnsembleEngine": EnsembleEngine,
            "ensemble_engine": ensemble_engine,
            "EnsemblePrediction": EnsemblePrediction,
            "NeuralNetworkEngine": NeuralNetworkEngine,
            "neural_network_engine": neural_network_engine,
            "NeuralNetworkConfig": NeuralNetworkConfig,
        }
        logger.info("ML services loaded successfully")
    except (ImportError, RuntimeError, Exception) as e:
        logger.warning(
            f"Failed to load ML services: {e}. ML features will be disabled."
        )
        _ml_imports = {
            "EnhancedMLEngine": None,
            "enhanced_ml_engine": None,
            "TechnicalIndicators": None,
            "MLPrediction": None,
            "MarketData": None,
            "EnsembleEngine": None,
            "ensemble_engine": None,
            "EnsemblePrediction": None,
            "NeuralNetworkEngine": None,
            "neural_network_engine": None,
            "NeuralNetworkConfig": None,
        }

    _ml_imports_loaded = True
    return _ml_imports


# Lazy property accessors
def __getattr__(name):
    """Lazy import ML services when accessed"""
    if name in [
        "EnhancedMLEngine",
        "enhanced_ml_engine",
        "TechnicalIndicators",
        "MLPrediction",
        "MarketData",
        "EnsembleEngine",
        "ensemble_engine",
        "EnsemblePrediction",
        "NeuralNetworkEngine",
        "neural_network_engine",
        "NeuralNetworkConfig",
    ]:
        imports = _lazy_load_ml_imports()
        return imports.get(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Always import integration service (lightweight)
from .integration_service import IntegrationService, integration_service

__all__ = [
    "EnhancedMLEngine",
    "enhanced_ml_engine",
    "TechnicalIndicators",
    "MLPrediction",
    "MarketData",
    "EnsembleEngine",
    "ensemble_engine",
    "EnsemblePrediction",
    "NeuralNetworkEngine",
    "neural_network_engine",
    "NeuralNetworkConfig",
    "IntegrationService",
    "integration_service",
]
