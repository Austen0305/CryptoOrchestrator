"""
Transformer Engine - Attention-based neural network for time-series prediction
"""
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging
import numpy as np
from datetime import datetime
import os

try:
    if os.getenv("DISABLE_TENSORFLOW", "0") == "1":
        raise ImportError("TensorFlow disabled by environment")
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers, callbacks
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow unavailable; Transformer engine will use mock model.")

logger = logging.getLogger(__name__)


class TransformerConfig(BaseModel):
    """Transformer model configuration"""
    sequence_length: int = 128  # Number of time steps to look back
    d_model: int = 256  # Model dimension
    num_heads: int = 8  # Number of attention heads
    num_layers: int = 6  # Number of transformer layers
    dff: int = 1024  # Feed-forward network dimension
    dropout: float = 0.1  # Dropout rate
    dense_units: int = 128  # Final dense layer units
    learning_rate: float = 0.0001
    epochs: int = 150
    batch_size: int = 32
    validation_split: float = 0.2
    early_stopping_patience: int = 15


class MarketData(BaseModel):
    """Market data point"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class TransformerEngine:
    """Transformer neural network engine for time-series prediction"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = TransformerConfig(**(config or {}))
        self.model: Optional[tf.keras.Model] = None
        self.is_training: bool = False
        self.feature_count: int = 5  # OHLCV
        self.scaler = None
        
        if TENSORFLOW_AVAILABLE:
            self.initialize_model()
        else:
            logger.warning("Transformer engine initialized with mock model")
            self._initialize_mock_model()
    
    def _initialize_mock_model(self):
        """Initialize mock model for testing when TensorFlow is unavailable"""
        class MockModel:
            def predict(self, data):
                batch_size = data.shape[0] if len(data.shape) > 1 else 1
                return np.full((batch_size, 3), 1/3.0)
            
            def fit(self, *args, **kwargs):
                return None
            
            def save(self, *args, **kwargs):
                pass
            
            def compile(self, *args, **kwargs):
                pass
        
        self.model = MockModel()
    
    def _transformer_encoder_layer(self, d_model: int, num_heads: int, dff: int, dropout: float, name: str):
        """Create a transformer encoder layer"""
        inputs = layers.Input(shape=(None, d_model))
        
        # Multi-head self-attention
        attention_output = layers.MultiHeadAttention(
            num_heads=num_heads,
            key_dim=d_model // num_heads,
            name=f"{name}_attention"
        )(inputs, inputs)
        attention_output = layers.Dropout(dropout)(attention_output)
        out1 = layers.LayerNormalization(epsilon=1e-6)(inputs + attention_output)
        
        # Feed-forward network
        ffn_output = layers.Dense(dff, activation='relu', name=f"{name}_ffn1")(out1)
        ffn_output = layers.Dense(d_model, name=f"{name}_ffn2")(ffn_output)
        ffn_output = layers.Dropout(dropout)(ffn_output)
        out2 = layers.LayerNormalization(epsilon=1e-6)(out1 + ffn_output)
        
        return models.Model(inputs, out2, name=name)
    
    def initialize_model(self) -> None:
        """Initialize the Transformer model"""
        if not TENSORFLOW_AVAILABLE:
            self._initialize_mock_model()
            return
        
        try:
            # Input layer
            inputs = layers.Input(shape=(self.config.sequence_length, self.feature_count))
            
            # Positional encoding (learned embeddings)
            x = layers.Dense(self.config.d_model)(inputs)
            
            # Add positional encoding
            positional_encoding = layers.Embedding(
                input_dim=self.config.sequence_length,
                output_dim=self.config.d_model
            )(tf.range(self.config.sequence_length))
            x = x + positional_encoding
            
            # Stack transformer encoder layers
            for i in range(self.config.num_layers):
                encoder_layer = self._transformer_encoder_layer(
                    self.config.d_model,
                    self.config.num_heads,
                    self.config.dff,
                    self.config.dropout,
                    f"encoder_layer_{i}"
                )
                x = encoder_layer(x)
            
            # Global average pooling
            x = layers.GlobalAveragePooling1D()(x)
            
            # Final dense layers
            x = layers.Dense(
                self.config.dense_units,
                activation='relu',
                kernel_initializer='he_normal'
            )(x)
            x = layers.Dropout(self.config.dropout)(x)
            
            x = layers.Dense(
                self.config.dense_units // 2,
                activation='relu',
                kernel_initializer='he_normal'
            )(x)
            x = layers.Dropout(self.config.dropout / 2)(x)
            
            # Output layer - 3 classes (buy, sell, hold)
            outputs = layers.Dense(3, activation='softmax')(x)
            
            # Create model
            model = models.Model(inputs, outputs)
            
            # Compile model
            model.compile(
                optimizer=optimizers.Adam(learning_rate=self.config.learning_rate),
                loss='categorical_crossentropy',
                metrics=['accuracy', 'sparse_categorical_accuracy']
            )
            
            self.model = model
            logger.info(f'Transformer model initialized: {self.config.num_layers} layers, '
                       f'd_model={self.config.d_model}, heads={self.config.num_heads}')
        
        except Exception as error:
            logger.error(f'Failed to initialize Transformer model: {error}')
            raise error
    
    def create_sequences(self, data: np.ndarray, labels: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Create sequences from time-series data"""
        X, y = [], []
        
        for i in range(len(data) - self.config.sequence_length):
            X.append(data[i:i + self.config.sequence_length])
            if labels is not None:
                y.append(labels[i + self.config.sequence_length])
        
        X = np.array(X)
        if labels is not None:
            y = np.array(y)
            return X, y
        return X, None
    
    def preprocess_data(self, market_data: List[MarketData]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Preprocess market data for Transformer input"""
        if not market_data:
            raise ValueError("Market data is empty")
        
        data_array = np.array([
            [d.open, d.high, d.low, d.close, d.volume]
            for d in market_data
        ])
        
        from sklearn.preprocessing import MinMaxScaler
        if self.scaler is None:
            self.scaler = MinMaxScaler()
            data_array = self.scaler.fit_transform(data_array)
        else:
            data_array = self.scaler.transform(data_array)
        
        X, _ = self.create_sequences(data_array)
        return X, None
    
    def predict(self, market_data: List[MarketData]) -> Dict[str, Any]:
        """Make prediction using Transformer model"""
        try:
            X, _ = self.preprocess_data(market_data)
            
            if len(X) == 0:
                return {
                    'action': 'hold',
                    'confidence': 0.33,
                    'probabilities': {'buy': 0.33, 'sell': 0.33, 'hold': 0.33}
                }
            
            predictions = self.model.predict(X[-1:], verbose=0)
            probs = predictions[0]
            
            actions = ['buy', 'sell', 'hold']
            action_idx = np.argmax(probs)
            action = actions[action_idx]
            confidence = float(probs[action_idx])
            
            return {
                'action': action,
                'confidence': confidence,
                'probabilities': {
                    'buy': float(probs[0]),
                    'sell': float(probs[1]),
                    'hold': float(probs[2])
                }
            }
        
        except Exception as error:
            logger.error(f'Transformer prediction error: {error}')
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
        """Train the Transformer model"""
        if not TENSORFLOW_AVAILABLE:
            logger.warning("TensorFlow not available, cannot train Transformer model")
            return {'status': 'skipped', 'reason': 'TensorFlow not available'}
        
        try:
            self.is_training = True
            
            callback_list = [
                callbacks.EarlyStopping(
                    monitor='val_loss' if X_val is not None else 'loss',
                    patience=self.config.early_stopping_patience,
                    restore_best_weights=True
                ),
                callbacks.ReduceLROnPlateau(
                    monitor='val_loss' if X_val is not None else 'loss',
                    factor=0.5,
                    patience=7,
                    min_lr=1e-7
                ),
                callbacks.ModelCheckpoint(
                    filepath='models/transformer_best.h5',
                    monitor='val_loss' if X_val is not None else 'loss',
                    save_best_only=True,
                    verbose=0
                )
            ]
            
            validation_data = (X_val, y_val) if X_val is not None else None
            
            history = self.model.fit(
                X_train,
                y_train,
                batch_size=self.config.batch_size,
                epochs=self.config.epochs,
                validation_data=validation_data,
                callbacks=callback_list,
                verbose=1
            )
            
            self.is_training = False
            
            return {
                'status': 'success',
                'history': {
                    'loss': history.history.get('loss', []),
                    'val_loss': history.history.get('val_loss', []),
                    'accuracy': history.history.get('accuracy', []),
                    'val_accuracy': history.history.get('val_accuracy', [])
                }
            }
        
        except Exception as error:
            self.is_training = False
            logger.error(f'Transformer training error: {error}')
            return {'status': 'error', 'error': str(error)}
    
    def save_model(self, filepath: str) -> bool:
        """Save the model to file"""
        try:
            if not TENSORFLOW_AVAILABLE:
                return False
            
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            self.model.save(filepath)
            logger.info(f'Transformer model saved to {filepath}')
            return True
        
        except Exception as error:
            logger.error(f'Failed to save Transformer model: {error}')
            return False
    
    def load_model(self, filepath: str) -> bool:
        """Load the model from file"""
        try:
            if not TENSORFLOW_AVAILABLE:
                return False
            
            if not os.path.exists(filepath):
                logger.warning(f'Transformer model file not found: {filepath}')
                return False
            
            self.model = models.load_model(filepath)
            logger.info(f'Transformer model loaded from {filepath}')
            return True
        
        except Exception as error:
            logger.error(f'Failed to load Transformer model: {error}')
            return False
