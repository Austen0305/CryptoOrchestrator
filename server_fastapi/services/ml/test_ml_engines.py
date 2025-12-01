"""
Test script for ML engines - Verify all models work correctly
"""
import sys
import os
from datetime import datetime
from typing import List
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from server_fastapi.services.ml.lstm_engine import LSTMEngine, MarketData
from server_fastapi.services.ml.gru_engine import GRUEngine
from server_fastapi.services.ml.transformer_engine import TransformerEngine
from server_fastapi.services.ml.xgboost_engine import XGBoostEngine
from server_fastapi.services.ml.ml_pipeline import MLPipeline
from server_fastapi.services.ml.model_evaluation import ModelEvaluation
from server_fastapi.services.ml.model_persistence import ModelPersistence


def generate_mock_data(n_samples: int = 200) -> List[MarketData]:
    """Generate mock market data for testing"""
    base_price = 50000.0
    data = []
    
    for i in range(n_samples):
        timestamp = int(datetime.now().timestamp()) + i * 3600
        price_change = np.random.normal(0, 0.02)  # 2% volatility
        price = base_price * (1 + price_change)
        base_price = price
        
        data.append(MarketData(
            timestamp=timestamp,
            open=price * (1 + np.random.normal(0, 0.001)),
            high=price * (1 + abs(np.random.normal(0, 0.002))),
            low=price * (1 - abs(np.random.normal(0, 0.002))),
            close=price,
            volume=np.random.uniform(1000000, 10000000)
        ))
    
    return data


def test_lstm_engine():
    """Test LSTM engine"""
    print("\n=== Testing LSTM Engine ===")
    try:
        engine = LSTMEngine()
        test_data = generate_mock_data(200)
        
        # Test prediction
        result = engine.predict(test_data)
        print(f"✅ LSTM Prediction: {result['action']} (confidence: {result['confidence']:.2f})")
        return True
    except Exception as e:
        print(f"❌ LSTM Engine Error: {e}")
        return False


def test_gru_engine():
    """Test GRU engine"""
    print("\n=== Testing GRU Engine ===")
    try:
        engine = GRUEngine()
        test_data = generate_mock_data(200)
        
        # Test prediction
        result = engine.predict(test_data)
        print(f"✅ GRU Prediction: {result['action']} (confidence: {result['confidence']:.2f})")
        return True
    except Exception as e:
        print(f"❌ GRU Engine Error: {e}")
        return False


def test_transformer_engine():
    """Test Transformer engine"""
    print("\n=== Testing Transformer Engine ===")
    try:
        engine = TransformerEngine()
        test_data = generate_mock_data(200)
        
        # Test prediction
        result = engine.predict(test_data)
        print(f"✅ Transformer Prediction: {result['action']} (confidence: {result['confidence']:.2f})")
        return True
    except Exception as e:
        print(f"❌ Transformer Engine Error: {e}")
        return False


def test_xgboost_engine():
    """Test XGBoost engine"""
    print("\n=== Testing XGBoost Engine ===")
    try:
        engine = XGBoostEngine()
        test_data = generate_mock_data(200)
        
        # Test prediction
        result = engine.predict(test_data)
        print(f"✅ XGBoost Prediction: {result['action']} (confidence: {result['confidence']:.2f})")
        return True
    except Exception as e:
        print(f"❌ XGBoost Engine Error: {e}")
        return False


def test_ml_pipeline():
    """Test ML Pipeline"""
    print("\n=== Testing ML Pipeline ===")
    try:
        pipeline = MLPipeline()
        test_data = generate_mock_data(300)
        
        # Process data
        processed = pipeline.process_data(test_data, create_labels=True)
        
        print(f"✅ Pipeline Processed Data:")
        print(f"   - X_train shape: {processed['X_train'].shape}")
        print(f"   - X_val shape: {processed['X_val'].shape}")
        print(f"   - X_test shape: {processed['X_test'].shape}")
        print(f"   - Features: {len(processed['feature_names'])}")
        return True
    except Exception as e:
        print(f"❌ ML Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_evaluation():
    """Test Model Evaluation"""
    print("\n=== Testing Model Evaluation ===")
    try:
        evaluator = ModelEvaluation()
        
        # Mock predictions
        y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        y_pred = np.array([0, 1, 2, 0, 1, 2, 0, 1, 1, 0])  # One wrong prediction
        
        metrics = evaluator.evaluate_classification(y_true, y_pred)
        
        print(f"✅ Evaluation Metrics:")
        print(f"   - Accuracy: {metrics.accuracy:.2f}")
        print(f"   - Macro F1: {metrics.macro_avg_f1:.2f}")
        return True
    except Exception as e:
        print(f"❌ Model Evaluation Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_persistence():
    """Test Model Persistence"""
    print("\n=== Testing Model Persistence ===")
    try:
        persistence = ModelPersistence(base_dir="test_models")
        
        # Test listing (should work even with empty directory)
        models = persistence.list_models()
        print(f"✅ Model Persistence initialized")
        print(f"   - Models directory: test_models")
        return True
    except Exception as e:
        print(f"❌ Model Persistence Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("ML Engines Test Suite")
    print("=" * 50)
    
    results = {
        "LSTM": test_lstm_engine(),
        "GRU": test_gru_engine(),
        "Transformer": test_transformer_engine(),
        "XGBoost": test_xgboost_engine(),
        "ML Pipeline": test_ml_pipeline(),
        "Model Evaluation": test_model_evaluation(),
        "Model Persistence": test_model_persistence(),
    }
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
