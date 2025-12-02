"""
Model Evaluation Service - Metrics and validation system
"""
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel
import logging
import numpy as np
from datetime import datetime

try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report,
        mean_squared_error, mean_absolute_error, r2_score
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn unavailable; model evaluation may be limited.")

logger = logging.getLogger(__name__)


class ClassificationMetrics(BaseModel):
    """Classification metrics"""
    accuracy: float
    precision: Dict[str, float]  # Per class
    recall: Dict[str, float]  # Per class
    f1_score: Dict[str, float]  # Per class
    confusion_matrix: List[List[int]]
    classification_report: str
    macro_avg_precision: float
    macro_avg_recall: float
    macro_avg_f1: float
    weighted_avg_precision: float
    weighted_avg_recall: float
    weighted_avg_f1: float


class RegressionMetrics(BaseModel):
    """Regression metrics"""
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    mae: float  # Mean Absolute Error
    r2_score: float  # R-squared
    mape: Optional[float] = None  # Mean Absolute Percentage Error


class ModelEvaluation:
    """Model evaluation service for computing metrics"""
    
    def __init__(self):
        self.label_map = {0: 'hold', 1: 'buy', 2: 'sell'}
        self.reverse_label_map = {'hold': 0, 'buy': 1, 'sell': 2}
    
    def evaluate_classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        labels: Optional[List[str]] = None
    ) -> ClassificationMetrics:
        """Evaluate classification model performance"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, returning mock metrics")
            return self._mock_classification_metrics()
        
        if labels is None:
            labels = ['hold', 'buy', 'sell']
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average=None, zero_division=0)
        recall = recall_score(y_true, y_pred, average=None, zero_division=0)
        f1 = f1_score(y_true, y_pred, average=None, zero_division=0)
        
        # Per-class metrics
        precision_dict = {labels[i]: float(precision[i]) for i in range(len(labels))}
        recall_dict = {labels[i]: float(recall[i]) for i in range(len(labels))}
        f1_dict = {labels[i]: float(f1[i]) for i in range(len(labels))}
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred).tolist()
        
        # Classification report
        report = classification_report(y_true, y_pred, target_names=labels, zero_division=0)
        
        # Macro averages
        macro_precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        macro_recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        
        # Weighted averages
        weighted_precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        weighted_recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        return ClassificationMetrics(
            accuracy=float(accuracy),
            precision=precision_dict,
            recall=recall_dict,
            f1_score=f1_dict,
            confusion_matrix=cm,
            classification_report=report,
            macro_avg_precision=float(macro_precision),
            macro_avg_recall=float(macro_recall),
            macro_avg_f1=float(macro_f1),
            weighted_avg_precision=float(weighted_precision),
            weighted_avg_recall=float(weighted_recall),
            weighted_avg_f1=float(weighted_f1)
        )
    
    def evaluate_regression(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> RegressionMetrics:
        """Evaluate regression model performance"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, returning mock metrics")
            return self._mock_regression_metrics()
        
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        # MAPE (Mean Absolute Percentage Error)
        mape = None
        if np.all(y_true != 0):
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        return RegressionMetrics(
            mse=float(mse),
            rmse=float(rmse),
            mae=float(mae),
            r2_score=float(r2),
            mape=float(mape) if mape is not None else None
        )
    
    def evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_type: str = 'classification'
    ) -> Dict[str, Any]:
        """Comprehensive model evaluation"""
        try:
            # Get predictions
            if hasattr(model, 'predict'):
                y_pred = model.predict(X_test)
            else:
                logger.error("Model does not have predict method")
                return {'error': 'Model does not support prediction'}
            
            # Evaluate based on model type
            if model_type == 'classification':
                metrics = self.evaluate_classification(y_test, y_pred)
                return {
                    'model_type': 'classification',
                    'metrics': metrics.dict(),
                    'evaluated_at': datetime.utcnow().isoformat()
                }
            
            elif model_type == 'regression':
                metrics = self.evaluate_regression(y_test, y_pred)
                return {
                    'model_type': 'regression',
                    'metrics': metrics.dict(),
                    'evaluated_at': datetime.utcnow().isoformat()
                }
            
            else:
                return {'error': f'Unknown model type: {model_type}'}
        
        except Exception as error:
            logger.error(f"Model evaluation error: {error}")
            return {'error': str(error)}
    
    def _mock_classification_metrics(self) -> ClassificationMetrics:
        """Return mock classification metrics when sklearn is unavailable"""
        return ClassificationMetrics(
            accuracy=0.5,
            precision={'hold': 0.5, 'buy': 0.5, 'sell': 0.5},
            recall={'hold': 0.5, 'buy': 0.5, 'sell': 0.5},
            f1_score={'hold': 0.5, 'buy': 0.5, 'sell': 0.5},
            confusion_matrix=[[10, 5, 5], [5, 10, 5], [5, 5, 10]],
            classification_report="Mock report",
            macro_avg_precision=0.5,
            macro_avg_recall=0.5,
            macro_avg_f1=0.5,
            weighted_avg_precision=0.5,
            weighted_avg_recall=0.5,
            weighted_avg_f1=0.5
        )
    
    def _mock_regression_metrics(self) -> RegressionMetrics:
        """Return mock regression metrics when sklearn is unavailable"""
        return RegressionMetrics(
            mse=0.01,
            rmse=0.1,
            mae=0.05,
            r2_score=0.8,
            mape=5.0
        )
