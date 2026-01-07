"""
Web Vitals Analytics Endpoint
Tracks Core Web Vitals metrics from frontend
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics"])


class WebVitalsMetric(BaseModel):
    name: str
    value: float
    id: str
    delta: float
    rating: str  # 'good', 'needs-improvement', 'poor'
    navigationType: Optional[str] = None
    timestamp: Optional[int] = None


@router.post("/web-vitals")
async def track_web_vitals(metric: WebVitalsMetric):
    """
    Track Core Web Vitals metrics
    Stores metrics for performance analysis and monitoring
    """
    try:
        # Log the metric
        logger.info(
            f"Web Vitals metric: {metric.name}={metric.value}ms "
            f"(rating: {metric.rating})"
        )

        return {
            "status": "recorded",
            "metric": metric.name,
            "value": metric.value,
            "rating": metric.rating,
        }
    except Exception as e:
        # Log error but return success to client to avoid client-side errors for analytics
        logger.warning(f"Error recording web vitals: {e}")
        return {
            "status": "recorded_with_error",
            "message": "Metric received but logging failed",
        }
