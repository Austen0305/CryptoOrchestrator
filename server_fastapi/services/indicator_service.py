"""
Indicator Service
Manages custom indicators for the marketplace.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from ..models.indicator import (
        Indicator,
        IndicatorPurchase,
        IndicatorRating,
        IndicatorVersion,
    )

from ..models.indicator import (
    Indicator,
    IndicatorLanguage,
    IndicatorPurchase,
    IndicatorRating,
    IndicatorStatus,
    IndicatorVersion,
)
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class IndicatorService:
    """Service for indicator marketplace functionality"""

    def __init__(
        self,
        db: AsyncSession,
        user_repository: UserRepository | None = None,
    ):
        self.db = db
        self.user_repository = user_repository or UserRepository()

    async def create_indicator(
        self,
        developer_id: int,
        name: str,
        code: str,
        language: str = IndicatorLanguage.PYTHON.value,
        description: str | None = None,
        category: str | None = None,
        tags: str | None = None,
        price: float = 0.0,
        is_free: bool = True,
        parameters: dict | None = None,
    ) -> dict[str, any]:
        """
        Create a new indicator.

        Args:
            developer_id: User ID of the developer
            name: Indicator name
            code: Indicator code
            language: Programming language
            description: Optional description
            category: Optional category
            tags: Optional comma-separated tags
            price: Price in USD (0 for free)
            is_free: Whether indicator is free
            parameters: Default parameters dict

        Returns:
            Dict with indicator details
        """
        try:
            # Create indicator
            indicator = Indicator(
                developer_id=developer_id,
                name=name,
                code=code,
                language=language,
                description=description,
                category=category,
                tags=tags,
                price=price,
                is_free=is_free,
                parameters=parameters or {},
                status=IndicatorStatus.DRAFT.value,
                is_public=False,
            )

            self.db.add(indicator)
            await self.db.commit()
            await self.db.refresh(indicator)

            # Create initial version
            version = IndicatorVersion(
                indicator_id=indicator.id,
                version=1,
                version_name="1.0.0",
                code=code,
                parameters=parameters or {},
                is_active=True,
            )

            self.db.add(version)
            indicator.latest_version_id = version.id
            await self.db.commit()
            await self.db.refresh(version)
            await self.db.refresh(indicator)

            return {
                "id": indicator.id,
                "name": indicator.name,
                "status": indicator.status,
                "version": 1,
                "version_id": version.id,
            }
        except Exception as e:
            logger.error(f"Error creating indicator: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def publish_indicator(
        self, indicator_id: int, developer_id: int
    ) -> dict[str, any]:
        """
        Publish an indicator (submit for approval).

        Args:
            indicator_id: Indicator ID
            developer_id: Developer user ID (must own indicator)

        Returns:
            Dict with updated status
        """
        try:
            indicator = await self.db.get(Indicator, indicator_id)
            if not indicator:
                raise ValueError("Indicator not found")

            if indicator.developer_id != developer_id:
                raise ValueError("Not authorized to publish this indicator")

            indicator.status = IndicatorStatus.PENDING.value
            await self.db.commit()
            await self.db.refresh(indicator)

            return {
                "id": indicator.id,
                "status": indicator.status,
                "message": "Indicator submitted for approval",
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error publishing indicator: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def approve_indicator(self, indicator_id: int) -> dict[str, any]:
        """
        Approve an indicator (curator action).

        Args:
            indicator_id: Indicator ID to approve

        Returns:
            Dict with approval details
        """
        try:
            indicator = await self.db.get(Indicator, indicator_id)
            if not indicator:
                raise ValueError("Indicator not found")

            indicator.status = IndicatorStatus.APPROVED.value
            indicator.is_public = True

            await self.db.commit()
            await self.db.refresh(indicator)

            return {
                "id": indicator.id,
                "status": indicator.status,
                "is_public": indicator.is_public,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error approving indicator: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def create_version(
        self,
        indicator_id: int,
        developer_id: int,
        code: str,
        version_name: str | None = None,
        changelog: str | None = None,
        parameters: dict | None = None,
        is_breaking: bool = False,
    ) -> dict[str, any]:
        """
        Create a new version of an indicator.

        Args:
            indicator_id: Indicator ID
            developer_id: Developer user ID (must own indicator)
            code: New version code
            version_name: Version name (e.g., "2.0.0")
            changelog: Changelog for this version
            parameters: Updated parameters
            is_breaking: Whether this is a breaking change

        Returns:
            Dict with version details
        """
        try:
            indicator = await self.db.get(Indicator, indicator_id)
            if not indicator:
                raise ValueError("Indicator not found")

            if indicator.developer_id != developer_id:
                raise ValueError("Not authorized to create version for this indicator")

            # Get next version number
            new_version = indicator.current_version + 1

            # Create new version
            version = IndicatorVersion(
                indicator_id=indicator_id,
                version=new_version,
                version_name=version_name or f"{new_version}.0.0",
                changelog=changelog,
                code=code,
                parameters=parameters or indicator.parameters or {},
                is_active=True,
                is_breaking=is_breaking,
            )

            self.db.add(version)
            indicator.current_version = new_version
            indicator.latest_version_id = version.id

            await self.db.commit()
            await self.db.refresh(version)
            await self.db.refresh(indicator)

            return {
                "id": version.id,
                "indicator_id": indicator_id,
                "version": new_version,
                "version_name": version.version_name,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating indicator version: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def purchase_indicator(
        self, indicator_id: int, user_id: int, version_id: int | None = None
    ) -> dict[str, any]:
        """
        Purchase an indicator (70/30 revenue split).

        Args:
            indicator_id: Indicator ID to purchase
            user_id: User ID purchasing
            version_id: Optional specific version ID (defaults to latest)

        Returns:
            Dict with purchase details
        """
        try:
            indicator = await self.db.get(Indicator, indicator_id)
            if not indicator:
                raise ValueError("Indicator not found")

            if indicator.status != IndicatorStatus.APPROVED.value:
                raise ValueError("Indicator not available for purchase")

            if indicator.is_free:
                price = 0.0
            else:
                price = indicator.price

            # Check if already purchased
            existing_result = await self.db.execute(
                select(IndicatorPurchase).where(
                    and_(
                        IndicatorPurchase.indicator_id == indicator_id,
                        IndicatorPurchase.user_id == user_id,
                        IndicatorPurchase.status == "completed",
                    )
                )
            )
            existing_purchase = existing_result.scalar_one_or_none()

            if existing_purchase:
                raise ValueError("Indicator already purchased")

            # Get version to purchase
            if version_id:
                version = await self.db.get(IndicatorVersion, version_id)
                if not version or version.indicator_id != indicator_id:
                    raise ValueError("Invalid version")
            else:
                # Get latest version
                version_result = await self.db.execute(
                    select(IndicatorVersion)
                    .where(IndicatorVersion.indicator_id == indicator_id)
                    .where(IndicatorVersion.is_active == True)
                    .order_by(desc(IndicatorVersion.version))
                    .limit(1)
                )
                version = version_result.scalar_one_or_none()
                if not version:
                    raise ValueError("No active version found")

            # Calculate revenue split (70% developer, 30% platform)
            platform_fee = price * 0.30
            developer_payout = price * 0.70

            # Create purchase record
            purchase = IndicatorPurchase(
                indicator_id=indicator_id,
                user_id=user_id,
                price_paid=price,
                platform_fee=platform_fee,
                developer_payout=developer_payout,
                version_id=version.id,
                status="completed",
            )

            self.db.add(purchase)

            # Update indicator statistics
            indicator.purchase_count += 1
            indicator.total_revenue += price

            await self.db.commit()
            await self.db.refresh(purchase)
            await self.db.refresh(indicator)

            return {
                "id": purchase.id,
                "indicator_id": indicator_id,
                "version_id": version.id,
                "price_paid": price,
                "status": purchase.status,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error purchasing indicator: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def rate_indicator(
        self, indicator_id: int, user_id: int, rating: int, comment: str | None = None
    ) -> dict[str, any]:
        """
        Rate an indicator (1-5 stars).

        Args:
            indicator_id: Indicator ID
            user_id: User ID rating
            rating: Rating (1-5)
            comment: Optional comment

        Returns:
            Dict with rating details
        """
        try:
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")

            # Check if already rated
            existing_result = await self.db.execute(
                select(IndicatorRating).where(
                    and_(
                        IndicatorRating.indicator_id == indicator_id,
                        IndicatorRating.user_id == user_id,
                    )
                )
            )
            existing_rating = existing_result.scalar_one_or_none()

            if existing_rating:
                existing_rating.rating = rating
                if comment:
                    existing_rating.comment = comment
                rating_obj = existing_rating
            else:
                rating_obj = IndicatorRating(
                    indicator_id=indicator_id,
                    user_id=user_id,
                    rating=rating,
                    comment=comment,
                )
                self.db.add(rating_obj)

            await self.db.commit()
            await self.db.refresh(rating_obj)

            # Update average rating
            await self._update_average_rating(indicator_id)

            return {
                "id": rating_obj.id,
                "indicator_id": indicator_id,
                "rating": rating,
                "comment": comment,
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error rating indicator: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def _update_average_rating(self, indicator_id: int) -> None:
        """Update average rating for an indicator"""
        try:
            ratings_result = await self.db.execute(
                select(
                    func.avg(IndicatorRating.rating), func.count(IndicatorRating.id)
                ).where(IndicatorRating.indicator_id == indicator_id)
            )
            result = ratings_result.first()

            if result and result[0]:
                indicator = await self.db.get(Indicator, indicator_id)
                if indicator:
                    indicator.average_rating = round(float(result[0]), 2)
                    indicator.total_ratings = result[1] or 0
                    await self.db.commit()
        except Exception as e:
            logger.error(f"Error updating average rating: {e}", exc_info=True)

    async def get_marketplace_indicators(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "download_count",
        category: str | None = None,
        is_free: bool | None = None,
        min_rating: float | None = None,
        search_query: str | None = None,
    ) -> dict[str, any]:
        """
        Get list of indicators for marketplace (public, approved only).

        Args:
            skip: Pagination offset
            limit: Pagination limit
            sort_by: Sort field (download_count, purchase_count, rating, price, created_at)
            category: Filter by category
            is_free: Filter by free/paid
            min_rating: Minimum average rating filter
            search_query: Search in name, description, tags

        Returns:
            Dict with indicators list and pagination info
        """
        try:
            query = (
                select(Indicator)
                .where(
                    and_(
                        Indicator.status == IndicatorStatus.APPROVED.value,
                        Indicator.is_public == True,
                    )
                )
                .options(selectinload(Indicator.developer))
            )

            # Apply filters
            if category:
                query = query.where(Indicator.category == category)
            if is_free is not None:
                query = query.where(Indicator.is_free == is_free)
            if min_rating is not None:
                query = query.where(Indicator.average_rating >= min_rating)
            if search_query:
                search_term = f"%{search_query.lower()}%"
                query = query.where(
                    or_(
                        func.lower(Indicator.name).like(search_term),
                        func.lower(Indicator.description).like(search_term),
                        func.lower(Indicator.tags).like(search_term),
                    )
                )

            # Apply sorting
            if sort_by == "download_count":
                query = query.order_by(desc(Indicator.download_count))
            elif sort_by == "purchase_count":
                query = query.order_by(desc(Indicator.purchase_count))
            elif sort_by == "rating":
                query = query.order_by(desc(Indicator.average_rating))
            elif sort_by == "price":
                query = query.order_by(Indicator.price)
            elif sort_by == "created_at":
                query = query.order_by(desc(Indicator.created_at))
            else:
                query = query.order_by(desc(Indicator.download_count))

            # Get total count
            count_query = select(func.count(Indicator.id)).where(
                and_(
                    Indicator.status == IndicatorStatus.APPROVED.value,
                    Indicator.is_public == True,
                )
            )
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await self.db.execute(query)
            indicators = result.scalars().all()

            indicator_list = []
            for ind in indicators:
                developer = ind.developer
                indicator_list.append(
                    {
                        "id": ind.id,
                        "name": ind.name,
                        "description": ind.description,
                        "category": ind.category,
                        "tags": ind.tags.split(",") if ind.tags else [],
                        "price": ind.price,
                        "is_free": ind.is_free,
                        "language": ind.language,
                        "download_count": ind.download_count,
                        "purchase_count": ind.purchase_count,
                        "average_rating": ind.average_rating,
                        "total_ratings": ind.total_ratings,
                        "developer": {
                            "id": developer.id if developer else None,
                            "username": developer.username or developer.email
                            if developer
                            else None,
                        },
                        "created_at": (
                            ind.created_at.isoformat() if ind.created_at else None
                        ),
                    }
                )

            return {
                "indicators": indicator_list,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error getting marketplace indicators: {e}", exc_info=True)
            return {"indicators": [], "total": 0, "skip": skip, "limit": limit}

    async def execute_indicator(
        self,
        indicator_id: int,
        user_id: int,
        market_data: list[dict],
        parameters: dict | None = None,
    ) -> dict[str, any]:
        """
        Execute an indicator on market data with sandboxed execution.

        Args:
            indicator_id: Indicator ID
            user_id: User ID (must own or have purchased)
            market_data: Market data (OHLCV)
            parameters: Optional parameter overrides

        Returns:
            Dict with indicator results
        """
        try:
            # Verify user has access
            indicator = await self.db.get(Indicator, indicator_id)
            if not indicator:
                raise ValueError("Indicator not found")

            # Check if user owns or has purchased
            if indicator.developer_id != user_id:
                purchase_result = await self.db.execute(
                    select(IndicatorPurchase).where(
                        and_(
                            IndicatorPurchase.indicator_id == indicator_id,
                            IndicatorPurchase.user_id == user_id,
                            IndicatorPurchase.status == "completed",
                        )
                    )
                )
                purchase = purchase_result.scalar_one_or_none()
                if not purchase:
                    raise ValueError("Indicator not purchased or not owned")

            # Get active version
            version_result = await self.db.execute(
                select(IndicatorVersion)
                .where(IndicatorVersion.indicator_id == indicator_id)
                .where(IndicatorVersion.is_active == True)
                .order_by(desc(IndicatorVersion.version))
                .limit(1)
            )
            version = version_result.scalar_one_or_none()

            if not version:
                raise ValueError("No active version found")

            # Merge parameters
            final_parameters = (indicator.parameters or {}).copy()
            if parameters:
                final_parameters.update(parameters)

            # Execute indicator with sandboxed execution engine
            from ..services.indicator_execution_engine import (
                IndicatorExecutionEngine,
                IndicatorExecutionError,
            )

            engine = IndicatorExecutionEngine()

            try:
                result = engine.execute_indicator(
                    code=version.code,
                    market_data=market_data,
                    parameters=final_parameters,
                )

                # Update download count
                indicator.download_count += 1
                await self.db.commit()

                return {
                    "status": "success",
                    "indicator_id": indicator_id,
                    "version": version.version,
                    "values": result.get("values", []),
                    "signals": result.get("signals", []),
                    "output": result.get("output", {}),
                }
            except IndicatorExecutionError as e:
                logger.error(f"Indicator execution error: {e}", exc_info=True)
                raise ValueError(f"Indicator execution failed: {str(e)}")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error executing indicator: {e}", exc_info=True)
            raise
