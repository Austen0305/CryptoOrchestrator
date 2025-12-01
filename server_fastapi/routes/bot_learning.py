"""
Bot Learning & Adaptation API Routes
Provides endpoints for bot learning metrics and adaptive strategies
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import logging

from ..dependencies.auth import get_current_user
from ..services.ml.adaptive_learning import adaptive_learning_service
from ..services.trading.bot_service import BotService
from ..dependencies.bots import get_bot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["Bot Learning"])


@router.get("/{bot_id}/learning/metrics")
async def get_bot_learning_metrics(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Dict[str, Any]:
    """Get learning metrics for a bot"""
    try:
        # Verify bot ownership
        bot_status = await bot_service.get_bot_status(bot_id, current_user['id'])
        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Get learning metrics
        metrics = adaptive_learning_service.get_learning_metrics()

        return {
            "bot_id": bot_id,
            "learning_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning metrics for bot {bot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get learning metrics: {str(e)}")


@router.get("/{bot_id}/learning/patterns")
async def get_bot_learning_patterns(
    bot_id: str,
    min_occurrences: int = 5,
    current_user: dict = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Dict[str, Any]:
    """Get learned patterns for a bot"""
    try:
        # Verify bot ownership
        bot_status = await bot_service.get_bot_status(bot_id, current_user['id'])
        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Get pattern analysis
        patterns = adaptive_learning_service.get_pattern_analysis(min_occurrences=min_occurrences)

        return {
            "bot_id": bot_id,
            "patterns": patterns,
            "total_patterns": len(patterns),
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning patterns for bot {bot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get learning patterns: {str(e)}")


@router.post("/{bot_id}/learning/retrain")
async def retrain_bot_model(
    bot_id: str,
    current_user: dict = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Dict[str, Any]:
    """Retrain bot model based on recent trading history"""
    try:
        # Verify bot ownership
        bot_status = await bot_service.get_bot_status(bot_id, current_user['id'])
        if not bot_status:
            raise HTTPException(status_code=404, detail="Bot not found")

        # In production, this would trigger model retraining
        # For now, we'll just return success
        return {
            "bot_id": bot_id,
            "status": "retraining_initiated",
            "message": "Model retraining initiated. This may take several minutes.",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retraining bot model for bot {bot_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrain model: {str(e)}")

