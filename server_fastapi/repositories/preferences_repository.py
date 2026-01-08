from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.preferences import UserPreferencesModel
from .base import SQLAlchemyRepository


class PreferencesRepository(SQLAlchemyRepository[UserPreferencesModel]):
    def __init__(self):
        super().__init__(UserPreferencesModel)

    async def get_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> UserPreferencesModel | None:
        result = await session.execute(
            select(UserPreferencesModel).where(UserPreferencesModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_for_user(
        self, session: AsyncSession, user_id: int, **kwargs
    ) -> UserPreferencesModel:
        prefs = await self.get_by_user_id(session, user_id)
        if prefs is None:
            prefs = UserPreferencesModel(user_id=user_id, **kwargs)
            session.add(prefs)
            await session.commit()
            await session.refresh(prefs)
            return prefs
        # update existing
        await session.execute(
            update(UserPreferencesModel)
            .where(UserPreferencesModel.id == prefs.id)
            .values(**kwargs)
        )
        await session.commit()
        await session.refresh(prefs)
        return prefs


preferences_repository = PreferencesRepository()
