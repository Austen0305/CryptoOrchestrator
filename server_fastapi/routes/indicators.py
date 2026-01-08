"""
Indicator Marketplace Routes
API endpoints for custom indicator marketplace functionality.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached
from ..services.indicator_service import IndicatorService
from ..services.volume_profile_service import VolumeProfileService
from ..utils.route_helpers import _get_user_id

try:
    from ..rate_limit_config import get_rate_limit, limiter
except ImportError:
    limiter = None
    get_rate_limit = lambda x: x

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateIndicatorRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1)
    language: str = Field(
        default="python", description="python, pine_script, javascript, custom_dsl"
    )
    description: str | None = None
    category: str | None = None
    tags: str | None = None
    price: float = Field(default=0.0, ge=0.0)
    is_free: bool = Field(default=True)
    parameters: dict[str, Any] | None = None


class CreateVersionRequest(BaseModel):
    code: str = Field(..., min_length=1)
    version_name: str | None = None
    changelog: str | None = None
    parameters: dict[str, Any] | None = None
    is_breaking: bool = Field(default=False)


class RateIndicatorRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = None


class ExecuteIndicatorRequest(BaseModel):
    market_data: list[dict[str, Any]] = Field(..., description="OHLCV market data")
    parameters: dict[str, Any] | None = None


class VolumeProfileRequest(BaseModel):
    market_data: list[dict[str, Any]] = Field(..., description="OHLCV market data")
    bins: int | None = Field(
        default=24, ge=10, le=100, description="Number of price bins"
    )


@router.post("/create")
async def create_indicator(
    request: CreateIndicatorRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new indicator"""
    try:
        user_id = _get_user_id(current_user)
        service = IndicatorService(db)

        result = await service.create_indicator(
            developer_id=user_id,
            name=request.name,
            code=request.code,
            language=request.language,
            description=request.description,
            category=request.category,
            tags=request.tags,
            price=request.price,
            is_free=request.is_free,
            parameters=request.parameters,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating indicator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create indicator")


@router.post("/{indicator_id}/publish")
async def publish_indicator(
    indicator_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Publish an indicator (submit for approval)"""
    try:
        user_id = _get_user_id(current_user)
        service = IndicatorService(db)

        result = await service.publish_indicator(indicator_id, user_id)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing indicator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to publish indicator")


@router.post("/{indicator_id}/version")
async def create_indicator_version(
    indicator_id: int,
    request: CreateVersionRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new version of an indicator"""
    try:
        user_id = _get_user_id(current_user)
        service = IndicatorService(db)

        result = await service.create_version(
            indicator_id=indicator_id,
            developer_id=user_id,
            code=request.code,
            version_name=request.version_name,
            changelog=request.changelog,
            parameters=request.parameters,
            is_breaking=request.is_breaking,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating indicator version: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to create indicator version"
        )


@router.get("/marketplace")
@cached(ttl=300, prefix="indicator_marketplace")  # 5 min cache
async def get_marketplace_indicators(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "download_count",
        description="Sort field: download_count, purchase_count, rating, price, created_at",
    ),
    category: str | None = Query(None, description="Filter by category"),
    is_free: bool | None = Query(None, description="Filter by free/paid"),
    min_rating: float | None = Query(
        None, ge=0, le=5, description="Minimum average rating"
    ),
    search: str | None = Query(None, description="Search in name, description, tags"),
):
    """Get list of indicators for marketplace"""
    try:
        service = IndicatorService(db)

        result = await service.get_marketplace_indicators(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            category=category,
            is_free=is_free,
            min_rating=min_rating,
            search_query=search,
        )

        return result
    except Exception as e:
        logger.error(f"Error getting marketplace indicators: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get marketplace indicators"
        )


@router.get("/{indicator_id}")
@cached(ttl=120, prefix="indicator_detail")
async def get_indicator_detail(
    indicator_id: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get detailed information about an indicator"""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from ..models.indicator import Indicator, IndicatorVersion

        result = await db.execute(
            select(Indicator)
            .where(Indicator.id == indicator_id)
            .options(selectinload(Indicator.developer))
        )
        indicator = result.scalar_one_or_none()

        if not indicator:
            raise HTTPException(status_code=404, detail="Indicator not found")

        # Get latest version
        version_result = await db.execute(
            select(IndicatorVersion)
            .where(IndicatorVersion.indicator_id == indicator_id)
            .where(IndicatorVersion.is_active == True)
            .order_by(IndicatorVersion.version.desc())
            .limit(1)
        )
        latest_version = version_result.scalar_one_or_none()

        developer = indicator.developer

        return {
            "id": indicator.id,
            "name": indicator.name,
            "description": indicator.description,
            "category": indicator.category,
            "tags": indicator.tags.split(",") if indicator.tags else [],
            "price": indicator.price,
            "is_free": indicator.is_free,
            "language": indicator.language,
            "parameters": indicator.parameters,
            "download_count": indicator.download_count,
            "purchase_count": indicator.purchase_count,
            "average_rating": indicator.average_rating,
            "total_ratings": indicator.total_ratings,
            "status": indicator.status,
            "developer": {
                "id": developer.id if developer else None,
                "username": developer.username or developer.email
                if developer
                else None,
            },
            "current_version": indicator.current_version,
            "latest_version": {
                "id": latest_version.id if latest_version else None,
                "version": latest_version.version if latest_version else None,
                "version_name": latest_version.version_name if latest_version else None,
            },
            "documentation": indicator.documentation,
            "usage_examples": indicator.usage_examples,
            "created_at": indicator.created_at.isoformat()
            if indicator.created_at
            else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting indicator detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get indicator detail")


@router.post("/{indicator_id}/purchase")
async def purchase_indicator(
    indicator_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    version_id: int | None = Query(None, description="Optional specific version ID"),
):
    """Purchase an indicator"""
    try:
        user_id = _get_user_id(current_user)
        service = IndicatorService(db)

        result = await service.purchase_indicator(
            indicator_id=indicator_id, user_id=user_id, version_id=version_id
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error purchasing indicator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to purchase indicator")


@router.post("/{indicator_id}/rate")
async def rate_indicator(
    indicator_id: int,
    request: RateIndicatorRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Rate an indicator (1-5 stars)"""
    try:
        user_id = _get_user_id(current_user)
        service = IndicatorService(db)

        result = await service.rate_indicator(
            indicator_id=indicator_id,
            user_id=user_id,
            rating=request.rating,
            comment=request.comment,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rating indicator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rate indicator")


@router.post("/{indicator_id}/execute")
async def execute_indicator(
    indicator_id: int,
    request: ExecuteIndicatorRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Execute an indicator on market data"""
    try:
        user_id = _get_user_id(current_user)
        service = IndicatorService(db)

        result = await service.execute_indicator(
            indicator_id=indicator_id,
            user_id=user_id,
            market_data=request.market_data,
            parameters=request.parameters,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing indicator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to execute indicator")


@router.post("/volume-profile")
async def calculate_volume_profile(
    request: VolumeProfileRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Calculate volume profile and market profile"""
    try:
        service = VolumeProfileService()

        volume_profile = service.calculate_volume_profile(
            market_data=request.market_data,
            bins=request.bins,
        )

        market_profile = service.calculate_market_profile(
            market_data=request.market_data,
        )

        poc_data = service.calculate_poc_and_value_areas(
            market_data=request.market_data,
        )

        return {
            "volume_profile": volume_profile,
            "market_profile": market_profile,
            "poc": poc_data["poc"],
            "vah": poc_data["vah"],
            "val": poc_data["val"],
        }
    except Exception as e:
        logger.error(f"Error calculating volume profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to calculate volume profile"
        )
