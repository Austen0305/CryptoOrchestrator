"""
ML Model Training API Routes
Train and manage machine learning models
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from server_fastapi.services.ml.lstm_training_service import get_lstm_service

logger = logging.getLogger(__name__)
router = APIRouter()


class TrainModelRequest(BaseModel):
    """Model training request"""

    symbol: str = Field(..., description="Trading pair (e.g., 'BTC/USDT')")
    price_data: List[Dict[str, Any]] = Field(..., description="Historical price data")
    epochs: int = Field(50, ge=1, le=200, description="Number of training epochs")
    batch_size: int = Field(32, ge=8, le=128, description="Batch size")
    validation_split: float = Field(
        0.2, ge=0.1, le=0.3, description="Validation split ratio"
    )


class PredictionRequest(BaseModel):
    """Prediction request"""

    recent_data: List[List[float]] = Field(
        ..., description="Recent price data for prediction"
    )


@router.post("/train", summary="Train LSTM Model")
async def train_model(request: TrainModelRequest):
    """
    Train LSTM model for price prediction

    Features:
    - 20+ technical indicators
    - LSTM architecture (2 layers, 128/64 units)
    - Early stopping
    - Model checkpointing

    Returns training metrics and model path
    """
    service = get_lstm_service()

    if not service.ml_available:
        raise HTTPException(
            status_code=503,
            detail="ML libraries not available. Install tensorflow and scikit-learn.",
        )

    try:
        # Prepare data
        X, y = service.prepare_data(
            price_data=request.price_data, symbol=request.symbol
        )

        # Split data
        split_idx = int(len(X) * (1 - request.validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Train model
        results = service.train_model(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            epochs=request.epochs,
            batch_size=request.batch_size,
            model_path=f'models/lstm_{request.symbol.replace("/", "_")}.h5',
        )

        return results

    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", summary="Make Prediction")
async def predict(request: PredictionRequest):
    """
    Make price prediction with trained model

    Requires:
    - Trained model
    - Recent data (60 time steps with features)
    """
    service = get_lstm_service()

    if not service.ml_available:
        raise HTTPException(status_code=503, detail="ML libraries not available")

    try:
        import numpy as np

        recent_data = np.array(request.recent_data)

        result = service.predict(recent_data)

        if not result["success"]:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Prediction failed")
            )

        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="Get ML Service Status")
async def get_status():
    """
    Get ML service status

    Returns:
    - ML libraries availability
    - Model training status
    - Configuration details
    """
    service = get_lstm_service()
    return service.get_status()


@router.get("/health", summary="ML Service Health Check")
async def health_check():
    """Health check for ML service"""
    service = get_lstm_service()
    status = service.get_status()

    return {
        "status": "healthy" if status["ml_available"] else "degraded",
        "ml_available": status["ml_available"],
        "message": (
            "ML service operational"
            if status["ml_available"]
            else "ML libraries not installed"
        ),
    }
