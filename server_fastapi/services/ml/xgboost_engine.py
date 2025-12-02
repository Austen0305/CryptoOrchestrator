"""
XGBoost Engine - Gradient boosting for time-series prediction
"""
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
import numpy as np
from datetime import datetime
import os
import pickle

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost unavailable; XGBoost engine will use mock model.")

try:
    from sklearn.preprocessing import MinMaxScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn unavailable; XGBoost engine preprocessing may fail.")

logger = logging.getLogger(__name__)


class XGBoostConfig(BaseModel):
    """XGBoost model configuration"""
    max_depth: int = 6  # Maximum tree depth
    n_estimators: int = 100  # Number of boosting rounds
    learning_rate: float = 0.1
    subsample: float = 0.8  # Fraction of samples used for training
    colsample_bytree: float = 0.8  # Fraction of features used per tree
    min_child_weight: int = 1
    gamma: float = 0  # Minimum loss reduction required
    reg_alpha: float = 0  # L1 regularization
    reg_lambda: float = 1  # L2 regularization
    objective: str = "multi:softprob"  # Multi-class classification
    num_class: int = 3  # Number of classes (buy, sell, hold)
    eval_metric: str = "mlogloss"
    early_stopping_rounds: int = 10
    random_state: int = 42


class MarketData(BaseModel):
    """Market data point"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class XGBoostEngine:
    """XGBoost gradient boosting engine for time-series prediction"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = XGBoostConfig(**(config or {}))
        self.model: Optional[xgb.XGBClassifier] = None
        self.is_training: bool = False
        self.scaler = None
        self.label_encoder = None
        
        if XGBOOST_AVAILABLE:
            self.initialize_model()
        else:
            logger.warning("XGBoost engine initialized with mock model")
            self._initialize_mock_model()
    
    def _initialize_mock_model(self):
        """Initialize mock model for testing when XGBoost is unavailable"""
        class MockModel:
            def predict_proba(self, data):
                batch_size = data.shape[0] if len(data.shape) > 1 else 1
                return np.full((batch_size, 3), 1/3.0)
            
            def fit(self, *args, **kwargs):
                return None
            
        self.model = MockModel()
    
    def initialize_model(self) -> None:
        """Initialize the XGBoost model"""
        if not XGBOOST_AVAILABLE:
            self._initialize_mock_model()
            return
        
        try:
            self.model = xgb.XGBClassifier(
                max_depth=self.config.max_depth,
                n_estimators=self.config.n_estimators,
                learning_rate=self.config.learning_rate,
                subsample=self.config.subsample,
                colsample_bytree=self.config.colsample_bytree,
                min_child_weight=self.config.min_child_weight,
                gamma=self.config.gamma,
                reg_alpha=self.config.reg_alpha,
                reg_lambda=self.config.reg_lambda,
                objective=self.config.objective,
                num_class=self.config.num_class,
                eval_metric=self.config.eval_metric,
                random_state=self.config.random_state,
                tree_method='hist',  # Faster training
                verbosity=0  # Suppress warnings
            )
            
            if SKLEARN_AVAILABLE:
                self.scaler = MinMaxScaler()
                self.label_encoder = LabelEncoder()
            
            logger.info(f'XGBoost model initialized: max_depth={self.config.max_depth}, '
                       f'n_estimators={self.config.n_estimators}')
        
        except Exception as error:
            logger.error(f'Failed to initialize XGBoost model: {error}')
            raise error
    
    def create_features(self, market_data: List[MarketData], lookback: int = 60) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create feature vectors from market data with technical indicators"""
        if len(market_data) < lookback:
            return np.array([]), None
        
        features = []
        labels = []
        
        for i in range(lookback, len(market_data)):
            # Extract sequence
            sequence = market_data[i - lookback:i + 1]
            
            # Price features
            prices = [d.close for d in sequence]
            volumes = [d.volume for d in sequence]
            
            feature_vector = []
            
            # Basic OHLCV features
            current = sequence[-1]
            feature_vector.extend([
                current.open,
                current.high,
                current.low,
                current.close,
                current.volume
            ])
            
            # Technical indicators
            # Moving averages
            ma_5 = np.mean(prices[-5:]) if len(prices) >= 5 else prices[-1]
            ma_10 = np.mean(prices[-10:]) if len(prices) >= 10 else prices[-1]
            ma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else prices[-1]
            feature_vector.extend([ma_5, ma_10, ma_20])
            
            # Price changes
            price_change_1 = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
            price_change_5 = (prices[-1] - prices[-6]) / prices[-6] if len(prices) >= 6 else 0
            price_change_20 = (prices[-1] - prices[-21]) / prices[-21] if len(prices) >= 21 else 0
            feature_vector.extend([price_change_1, price_change_5, price_change_20])
            
            # Volatility
            if len(prices) >= 20:
                volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) if np.mean(prices[-20:]) != 0 else 0
            else:
                volatility = 0
            feature_vector.append(volatility)
            
            # Volume features
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
            volume_ratio = current.volume / avg_volume if avg_volume != 0 else 1
            feature_vector.append(volume_ratio)
            
            # RSI (simplified)
            if len(prices) >= 14:
                gains = [max(0, prices[j] - prices[j-1]) for j in range(len(prices)-13, len(prices))]
                losses = [max(0, prices[j-1] - prices[j]) for j in range(len(prices)-13, len(prices))]
                avg_gain = np.mean(gains) if gains else 0
                avg_loss = np.mean(losses) if losses else 0
                rs = avg_gain / avg_loss if avg_loss != 0 else 1
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50
            feature_vector.append(rsi)
            
            features.append(feature_vector)
        
        features = np.array(features)
        
        return features, None  # Labels created separately
    
    def preprocess_data(self, market_data: List[MarketData], labels: Optional[List[str]] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Preprocess market data for XGBoost input"""
        if not market_data:
            raise ValueError("Market data is empty")
        
        # Create features
        X, _ = self.create_features(market_data)
        
        if len(X) == 0:
            return np.array([]), None
        
        # Normalize features
        if SKLEARN_AVAILABLE and self.scaler is not None:
            if not hasattr(self.scaler, 'mean_'):  # Not fitted yet
                X = self.scaler.fit_transform(X)
            else:
                X = self.scaler.transform(X)
        
        # Encode labels if provided
        y = None
        if labels and SKLEARN_AVAILABLE and self.label_encoder is not None:
            y = self.label_encoder.fit_transform(labels)
        
        return X, y
    
    def predict(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Make prediction using XGBoost model"""
        try:
            X, _ = self.preprocess_data(market_data)
            
            if len(X) == 0:
                return {
                    'action': 'hold',
                    'confidence': 0.33,
                    'probabilities': {'buy': 0.33, 'sell': 0.33, 'hold': 0.33}
                }
            
            # Get prediction probabilities
            probs = self.model.predict_proba(X[-1:])[0]
            
            # Map to actions
            actions = ['buy', 'sell', 'hold']
            if self.label_encoder and hasattr(self.label_encoder, 'classes_'):
                # Map encoded labels back to actions
                action_idx = np.argmax(probs)
                action = self.label_encoder.inverse_transform([action_idx])[0]
            else:
                action_idx = np.argmax(probs)
                action = actions[action_idx] if action_idx < len(actions) else 'hold'
            
            confidence = float(probs[action_idx])
            
            # Ensure we have 3 probabilities
            prob_dict = {}
            if len(probs) >= 3:
                prob_dict = {
                    'buy': float(probs[0]),
                    'sell': float(probs[1]),
                    'hold': float(probs[2])
                }
            else:
                # Fallback
                prob_dict = {'buy': 0.33, 'sell': 0.33, 'hold': 0.33}
            
            return {
                'action': action,
                'confidence': confidence,
                'probabilities': prob_dict
            }
        
        except Exception as error:
            logger.error(f'XGBoost prediction error: {error}')
            return {
                'action': 'hold',
                'confidence': 0.33,
                'probabilities': {'buy': 0.33, 'sell': 0.33, 'hold': 0.33}
            }
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Train the XGBoost model"""
        if not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available, cannot train model")
            return {'status': 'skipped', 'reason': 'XGBoost not available'}
        
        try:
            self.is_training = True
            
            # Prepare training data
            eval_set = [(X_train, y_train)]
            if X_val is not None and y_val is not None:
                eval_set.append((X_val, y_val))
            
            # Train model
            self.model.fit(
                X_train,
                y_train,
                eval_set=eval_set,
                eval_metric=self.config.eval_metric,
                early_stopping_rounds=self.config.early_stopping_rounds if X_val is not None else None,
                verbose=False
            )
            
            self.is_training = False
            
            # Get evaluation results
            results = self.model.evals_result()
            
            return {
                'status': 'success',
                'history': {
                    'train_loss': results.get('validation_0', {}).get('mlogloss', []),
                    'val_loss': results.get('validation_1', {}).get('mlogloss', []) if X_val is not None else []
                }
            }
        
        except Exception as error:
            self.is_training = False
            logger.error(f'XGBoost training error: {error}')
            return {'status': 'error', 'error': str(error)}
    
    def save_model(self, filepath: str) -> bool:
        """Save the model to file"""
        try:
            if not XGBOOST_AVAILABLE or self.model is None:
                return False
            
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            
            # Save model
            self.model.save_model(filepath)
            
            # Save scaler and label encoder
            scaler_path = filepath.replace('.model', '_scaler.pkl')
            if self.scaler:
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scaler, f)
            
            encoder_path = filepath.replace('.model', '_encoder.pkl')
            if self.label_encoder:
                with open(encoder_path, 'wb') as f:
                    pickle.dump(self.label_encoder, f)
            
            logger.info(f'XGBoost model saved to {filepath}')
            return True
        
        except Exception as error:
            logger.error(f'Failed to save XGBoost model: {error}')
            return False
    
    def load_model(self, filepath: str) -> bool:
        """Load the model from file"""
        try:
            if not XGBOOST_AVAILABLE:
                return False
            
            if not os.path.exists(filepath):
                logger.warning(f'XGBoost model file not found: {filepath}')
                return False
            
            # Load model
            self.model = xgb.XGBClassifier()
            self.model.load_model(filepath)
            
            # Load scaler and label encoder
            scaler_path = filepath.replace('.model', '_scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            encoder_path = filepath.replace('.model', '_encoder.pkl')
            if os.path.exists(encoder_path):
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
            
            logger.info(f'XGBoost model loaded from {filepath}')
            return True
        
        except Exception as error:
            logger.error(f'Failed to load XGBoost model: {error}')
            return False
