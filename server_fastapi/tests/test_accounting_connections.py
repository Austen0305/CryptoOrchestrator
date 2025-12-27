"""
Tests for Accounting Connection System
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from server_fastapi.models.accounting_connection import (
    AccountingConnection,
    AccountingSyncLog,
    AccountingSystem,
    ConnectionStatus,
    SyncFrequency,
)
from server_fastapi.models.user import User
from server_fastapi.services.tax.accounting_connection_service import AccountingConnectionService


pytestmark = pytest.mark.asyncio


class TestAccountingConnection:
    """Tests for AccountingConnection model and service"""

    async def test_get_authorization_url(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting OAuth authorization URL"""
        service = AccountingConnectionService(db_session)
        
        # Mock adapter (will fail if credentials not set, but tests structure)
        try:
            auth_url = await service.get_authorization_url(
                user_id=test_user.id,
                system=AccountingSystem.QUICKBOOKS,
            )
            assert auth_url is not None
            assert "quickbooks" in auth_url.lower() or "intuit" in auth_url.lower()
        except ValueError:
            # Expected if adapter not configured
            pytest.skip("Accounting adapter not configured (missing env vars)")

    async def test_connection_storage(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test storing and retrieving connections"""
        service = AccountingConnectionService(db_session)
        
        # Create connection manually (simulating OAuth completion)
        connection = AccountingConnection(
            user_id=test_user.id,
            system=AccountingSystem.QUICKBOOKS.value,
            status=ConnectionStatus.CONNECTED.value,
            access_token=service._encrypt_token("test_token"),
            refresh_token=service._encrypt_token("test_refresh"),
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            realm_id="test_realm",
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)
        
        # Retrieve connection
        retrieved = await service.get_connection(
            test_user.id,
            AccountingSystem.QUICKBOOKS,
        )
        
        assert retrieved is not None
        assert retrieved.id == connection.id
        assert retrieved.status == ConnectionStatus.CONNECTED.value
        
        # Verify token decryption
        credentials = await service.get_credentials(retrieved)
        assert credentials is not None
        assert credentials.access_token == "test_token"

    async def test_token_refresh(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test token refresh"""
        service = AccountingConnectionService(db_session)
        
        # Create connection with expired token
        connection = AccountingConnection(
            user_id=test_user.id,
            system=AccountingSystem.QUICKBOOKS.value,
            status=ConnectionStatus.CONNECTED.value,
            access_token=service._encrypt_token("old_token"),
            refresh_token=service._encrypt_token("refresh_token"),
            token_expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)
        
        # Try to refresh (will fail without adapter, but tests structure)
        try:
            refreshed = await service.refresh_token_if_needed(connection)
            # If adapter configured, token should be refreshed
            if refreshed:
                assert connection.token_expires_at > datetime.utcnow()
        except (ValueError, ImportError):
            # Expected if adapter not configured
            pytest.skip("Accounting adapter not configured")

    async def test_sync_logging(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test sync log creation"""
        # Create connection
        connection = AccountingConnection(
            user_id=test_user.id,
            system=AccountingSystem.QUICKBOOKS.value,
            status=ConnectionStatus.CONNECTED.value,
            access_token="encrypted_token",
        )
        db_session.add(connection)
        await db_session.commit()
        await db_session.refresh(connection)
        
        service = AccountingConnectionService(db_session)
        
        # Log sync
        sync_log = await service.log_sync(
            connection_id=connection.id,
            sync_type="manual",
            status="success",
            transactions_synced=10,
            transactions_failed=0,
        )
        
        assert sync_log.id is not None
        assert sync_log.connection_id == connection.id
        assert sync_log.status == "success"
        assert sync_log.transactions_synced == 10
        
        # Verify connection updated
        await db_session.refresh(connection)
        assert connection.last_sync_at is not None
