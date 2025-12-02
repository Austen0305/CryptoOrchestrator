"""
Base repository pattern implementation for database operations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict
from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
# NOTE: get_db_session imported for completeness; repository methods expect an AsyncSession passed explicitly.
try:
    from ..database import get_db_session  # type: ignore
except Exception:  # pragma: no cover
    get_db_session = None  # Optional for tests without DB

T = TypeVar('T')  # Model type
ID = TypeVar('ID')  # ID type

class BaseRepository(Generic[T, ID], ABC):
    """
    Abstract base repository providing common CRUD operations.
    """

    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, id: ID) -> Optional[T]:
        """Get a single record by ID."""
        pass

    @abstractmethod
    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination."""
        pass

    @abstractmethod
    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> T:
        """Create a new record."""
        pass

    @abstractmethod
    async def update(self, session: AsyncSession, id: ID, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record."""
        pass

    @abstractmethod
    async def delete(self, session: AsyncSession, id: ID) -> bool:
        """Delete a record by ID."""
        pass

class SQLAlchemyRepository(BaseRepository[T, int]):
    """
    SQLAlchemy implementation of the base repository pattern.
    Provides async CRUD operations for SQLAlchemy models.
    """

    async def get_by_id(self, session: AsyncSession, id: int, load_options: Optional[List] = None) -> Optional[T]:
        """
        Get a single record by ID.
        Optionally load related entities.
        """
        query = select(self.model_class).where(
            self.model_class.id == id,
            ~self.model_class.is_deleted  # Exclude soft-deleted records
        )

        if load_options:
            for option in load_options:
                query = query.options(option)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100,
                     filters: Optional[Dict[str, Any]] = None,
                     load_options: Optional[List] = None) -> List[T]:
        """
        Get all records with optional filtering and pagination.
        """
        query = select(self.model_class).where(~self.model_class.is_deleted)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)

        if load_options:
            for option in load_options:
                query = query.options(option)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> T:
        """
        Create a new record.
        """
        # Remove any fields that shouldn't be set during creation
        # Preserve provided string primary key values (e.g., Bot.id) while filtering
        primary_key_is_string = False
        if hasattr(self.model_class, 'id'):
            try:
                col_type = getattr(self.model_class, 'id').property.columns[0].type  # type: ignore[attr-defined]
                from sqlalchemy import String
                primary_key_is_string = isinstance(col_type, String)
            except Exception:
                primary_key_is_string = False

        create_data = {}
        for k, v in data.items():
            if k in ['created_at', 'updated_at']:
                continue
            if k == 'id' and not primary_key_is_string:
                # Skip autoincrement integer ids
                continue
            create_data[k] = v

        # Field aliasing to support legacy/external naming
        # Example: tests use 'hashed_password' while model uses 'password_hash'
        if 'hashed_password' in create_data and hasattr(self.model_class, 'password_hash'):
            create_data['password_hash'] = create_data.pop('hashed_password')

        # JSON serialization for any mapped Text columns that caller passed as dict/list
        # Heuristic: if model has attribute and incoming value is dict/list but column expects string/text
        from sqlalchemy import String, Text
        for key, value in list(create_data.items()):
            if isinstance(value, (dict, list)) and hasattr(self.model_class, key):
                col = getattr(self.model_class, key)
                try:
                    # Column may be InstrumentedAttribute; access property .property.columns[0].type
                    col_type = col.property.columns[0].type  # type: ignore[attr-defined]
                    if isinstance(col_type, (String, Text)):
                        import json
                        create_data[key] = json.dumps(value)
                except Exception:
                    pass  # Non-critical; fallback to original value

        stmt = insert(self.model_class).values(**create_data).returning(self.model_class)
        result = await session.execute(stmt)
        await session.commit()

        created_obj = result.scalar_one()
        await session.refresh(created_obj)
        return created_obj

    async def update(self, session: AsyncSession, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update an existing record.
        """
        # Remove fields that shouldn't be updated directly
        update_data: Dict[str, Any] = {k: v for k, v in data.items() if k not in ['created_at']}

        # Allow explicit update of string PK only if necessary (rare). Avoid changing integer PK.
        if 'id' in update_data:
            try:
                col_type = getattr(self.model_class, 'id').property.columns[0].type  # type: ignore[attr-defined]
                from sqlalchemy import Integer
                if isinstance(col_type, Integer):
                    update_data.pop('id', None)
            except Exception:
                update_data.pop('id', None)

        # Apply same aliasing for updates
        if 'hashed_password' in update_data and hasattr(self.model_class, 'password_hash'):
            update_data['password_hash'] = update_data.pop('hashed_password')

        # JSON serialization similar to create
        from sqlalchemy import String, Text
        for key, value in list(update_data.items()):
            if isinstance(value, (dict, list)) and hasattr(self.model_class, key):
                col = getattr(self.model_class, key)
                try:
                    col_type = col.property.columns[0].type  # type: ignore[attr-defined]
                    if isinstance(col_type, (String, Text)):
                        import json
                        update_data[key] = json.dumps(value)
                except Exception:
                    pass

        # Do not force 'updated_at' here; let SQLAlchemy onupdate/default handle it if configured

        stmt = update(self.model_class).where(
            self.model_class.id == id,
            ~self.model_class.is_deleted
        ).values(**update_data).returning(self.model_class)

        result = await session.execute(stmt)
        await session.commit()

        updated_obj = result.scalar_one_or_none()
        if updated_obj:
            await session.refresh(updated_obj)
        return updated_obj

    async def delete(self, session: AsyncSession, id: int) -> bool:
        """
        Soft delete a record by ID.
        """
        stmt = update(self.model_class).where(
            self.model_class.id == id,
            ~self.model_class.is_deleted
        ).values(is_deleted=True, deleted_at=None)  # Set deleted_at to current time

        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    async def hard_delete(self, session: AsyncSession, id: int) -> bool:
        """
        Permanently delete a record by ID.
        Use with caution!
        """
        stmt = delete(self.model_class).where(self.model_class.id == id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    async def exists(self, session: AsyncSession, id: int) -> bool:
        """
        Check if a record exists by ID.
        """
        query = select(self.model_class.id).where(
            self.model_class.id == id,
            ~self.model_class.is_deleted
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    async def count(self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters.
        """
        query = select(self.model_class.id).where(~self.model_class.is_deleted)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)

        result = await session.execute(query)
        return len(result.scalars().all())

# Repository factory for dependency injection
class RepositoryFactory:
    """
    Factory class for creating repository instances.
    """

    _repositories: Dict[type, BaseRepository] = {}

    @classmethod
    def get_repository(cls, model_class: type[T]) -> BaseRepository[T, int]:
        """
        Get or create a repository instance for the given model class.
        """
        if model_class not in cls._repositories:
            cls._repositories[model_class] = SQLAlchemyRepository(model_class)
        return cls._repositories[model_class]