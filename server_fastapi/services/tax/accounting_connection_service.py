"""
Accounting Connection Service
Manages OAuth connections to QuickBooks and Xero
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import os
import base64

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    Fernet = None
    CRYPTOGRAPHY_AVAILABLE = False
    logger.warning("cryptography not available - token encryption disabled")

from ...models.accounting_connection import (
    AccountingConnection,
    AccountingSyncLog,
    AccountingSystem,
    ConnectionStatus,
    SyncFrequency,
)
from .accounting_adapters import QuickBooksAdapter, XeroAdapter, OAuthCredentials

logger = logging.getLogger(__name__)


class AccountingConnectionService:
    """
    Service for managing accounting system connections
    
    Features:
    - OAuth flow management
    - Token storage and encryption
    - Token refresh
    - Connection status tracking
    - Sync scheduling
    - Account mapping
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize accounting connection service
        
        Args:
            db: Async database session
        """
        self.db = db
        self._encryption_key = self._get_encryption_key()
        self._cipher = Fernet(self._encryption_key) if self._encryption_key else None
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key from environment"""
        if not CRYPTOGRAPHY_AVAILABLE:
            return None
        key = os.getenv("ACCOUNTING_ENCRYPTION_KEY")
        if key:
            return key.encode()
        # Generate a key if not set (for development only)
        # In production, this should be set via environment variable
        logger.warning("ACCOUNTING_ENCRYPTION_KEY not set, using development key")
        return Fernet.generate_key()
    
    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for storage"""
        if not self._cipher:
            return token  # No encryption if cipher not available
        return self._cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage"""
        if not self._cipher:
            return encrypted_token  # No decryption if cipher not available
        return self._cipher.decrypt(encrypted_token.encode()).decode()
    
    async def get_authorization_url(
        self,
        user_id: int,
        system: AccountingSystem,
        state: Optional[str] = None,
    ) -> str:
        """
        Get OAuth authorization URL
        
        Args:
            user_id: User ID
            system: Accounting system
            state: Optional state parameter
        
        Returns:
            Authorization URL
        """
        # Get adapter
        adapter = self._get_adapter(system)
        if not adapter:
            raise ValueError(f"Adapter not configured for {system}")
        
        # Generate state if not provided
        if not state:
            state = f"{user_id}_{system.value}_{datetime.utcnow().timestamp()}"
        
        # Store state in connection (pending status)
        connection = await self.get_connection(user_id, system)
        if not connection:
            connection = AccountingConnection(
                user_id=user_id,
                system=system.value,
                status=ConnectionStatus.PENDING.value,
                access_token="",  # Temporary
                metadata={"oauth_state": state},
            )
            self.db.add(connection)
        else:
            connection.status = ConnectionStatus.PENDING.value
            if not connection.metadata:
                connection.metadata = {}
            connection.metadata["oauth_state"] = state
        
        await self.db.commit()
        
        return adapter.get_authorization_url(state)
    
    async def complete_oauth_flow(
        self,
        user_id: int,
        system: AccountingSystem,
        authorization_code: str,
        state: Optional[str] = None,
    ) -> AccountingConnection:
        """
        Complete OAuth flow and store credentials
        
        Args:
            user_id: User ID
            system: Accounting system
            authorization_code: Authorization code from callback
            state: State parameter from callback
        
        Returns:
            AccountingConnection
        """
        # Get adapter
        adapter = self._get_adapter(system)
        if not adapter:
            raise ValueError(f"Adapter not configured for {system}")
        
        # Exchange code for tokens
        credentials = await adapter.exchange_code_for_tokens(authorization_code)
        
        # Get or create connection
        connection = await self.get_connection(user_id, system)
        if not connection:
            connection = AccountingConnection(
                user_id=user_id,
                system=system.value,
                status=ConnectionStatus.CONNECTED.value,
                access_token=self._encrypt_token(credentials.access_token),
                refresh_token=self._encrypt_token(credentials.refresh_token) if credentials.refresh_token else None,
                token_expires_at=credentials.expires_at,
                realm_id=credentials.realm_id,
                tenant_id=credentials.tenant_id,
                connected_at=datetime.utcnow(),
            )
            self.db.add(connection)
        else:
            # Update existing connection
            connection.status = ConnectionStatus.CONNECTED.value
            connection.access_token = self._encrypt_token(credentials.access_token)
            if credentials.refresh_token:
                connection.refresh_token = self._encrypt_token(credentials.refresh_token)
            connection.token_expires_at = credentials.expires_at
            connection.realm_id = credentials.realm_id
            connection.tenant_id = credentials.tenant_id
            connection.error_message = None
        
        await self.db.commit()
        await self.db.refresh(connection)
        
        logger.info(f"OAuth flow completed for user {user_id}, system {system.value}")
        
        return connection
    
    async def get_connection(
        self,
        user_id: int,
        system: AccountingSystem,
    ) -> Optional[AccountingConnection]:
        """Get accounting connection for user"""
        stmt = select(AccountingConnection).where(
            and_(
                AccountingConnection.user_id == user_id,
                AccountingConnection.system == system.value,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_connections(
        self,
        user_id: int,
    ) -> List[AccountingConnection]:
        """Get all accounting connections for user"""
        stmt = select(AccountingConnection).where(
            AccountingConnection.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def refresh_token_if_needed(
        self,
        connection: AccountingConnection,
    ) -> bool:
        """
        Refresh access token if expired
        
        Args:
            connection: Accounting connection
        
        Returns:
            True if token was refreshed
        """
        # Check if token is expired or expiring soon (within 5 minutes)
        if connection.token_expires_at:
            time_until_expiry = (connection.token_expires_at - datetime.utcnow()).total_seconds()
            if time_until_expiry > 300:  # More than 5 minutes left
                return False  # Token still valid
        
        if not connection.refresh_token:
            logger.warning(f"No refresh token for connection {connection.id}")
            return False
        
        # Get adapter
        system = AccountingSystem(connection.system)
        adapter = self._get_adapter(system)
        if not adapter:
            logger.error(f"Adapter not configured for {system}")
            return False
        
        try:
            # Refresh token
            decrypted_refresh_token = self._decrypt_token(connection.refresh_token)
            credentials = await adapter.refresh_access_token(decrypted_refresh_token)
            
            # Update connection
            connection.access_token = self._encrypt_token(credentials.access_token)
            if credentials.refresh_token:
                connection.refresh_token = self._encrypt_token(credentials.refresh_token)
            connection.token_expires_at = credentials.expires_at
            connection.status = ConnectionStatus.CONNECTED.value
            connection.error_message = None
            
            await self.db.commit()
            
            logger.info(f"Token refreshed for connection {connection.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh token for connection {connection.id}: {e}")
            connection.status = ConnectionStatus.EXPIRED.value
            connection.error_message = str(e)
            await self.db.commit()
            return False
    
    async def get_credentials(
        self,
        connection: AccountingConnection,
    ) -> Optional[OAuthCredentials]:
        """
        Get decrypted OAuth credentials
        
        Args:
            connection: Accounting connection
        
        Returns:
            OAuthCredentials or None
        """
        # Refresh token if needed
        await self.refresh_token_if_needed(connection)
        
        if connection.status != ConnectionStatus.CONNECTED.value:
            return None
        
        return OAuthCredentials(
            access_token=self._decrypt_token(connection.access_token),
            refresh_token=self._decrypt_token(connection.refresh_token) if connection.refresh_token else None,
            expires_at=connection.token_expires_at,
            token_type="Bearer",
            realm_id=connection.realm_id,
            tenant_id=connection.tenant_id,
        )
    
    async def disconnect(
        self,
        user_id: int,
        system: AccountingSystem,
    ) -> bool:
        """
        Disconnect accounting system
        
        Args:
            user_id: User ID
            system: Accounting system
        
        Returns:
            True if successful
        """
        connection = await self.get_connection(user_id, system)
        if not connection:
            return False
        
        connection.status = ConnectionStatus.DISCONNECTED.value
        connection.access_token = ""  # Clear token
        connection.refresh_token = None
        connection.enabled = False
        
        await self.db.commit()
        
        logger.info(f"Disconnected {system.value} for user {user_id}")
        return True
    
    async def update_sync_config(
        self,
        user_id: int,
        system: AccountingSystem,
        sync_frequency: SyncFrequency,
        account_mappings: Optional[Dict[str, str]] = None,
    ) -> AccountingConnection:
        """
        Update sync configuration
        
        Args:
            user_id: User ID
            system: Accounting system
            sync_frequency: Sync frequency
            account_mappings: Account code mappings
        
        Returns:
            Updated connection
        """
        connection = await self.get_connection(user_id, system)
        if not connection:
            raise ValueError(f"No connection found for {system.value}")
        
        connection.sync_frequency = sync_frequency.value
        
        if account_mappings:
            connection.account_mappings = account_mappings
        
        # Calculate next sync time
        if sync_frequency != SyncFrequency.MANUAL:
            connection.next_sync_at = self._calculate_next_sync_time(sync_frequency)
        
        await self.db.commit()
        await self.db.refresh(connection)
        
        return connection
    
    def _calculate_next_sync_time(self, frequency: SyncFrequency) -> datetime:
        """Calculate next sync time based on frequency"""
        now = datetime.utcnow()
        if frequency == SyncFrequency.DAILY:
            return now + timedelta(days=1)
        elif frequency == SyncFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        elif frequency == SyncFrequency.MONTHLY:
            return now + timedelta(days=30)
        return now
    
    async def log_sync(
        self,
        connection_id: int,
        sync_type: str,
        status: str,
        transactions_synced: int = 0,
        transactions_failed: int = 0,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
    ) -> AccountingSyncLog:
        """
        Log sync operation
        
        Args:
            connection_id: Connection ID
            sync_type: Type of sync
            status: Sync status
            transactions_synced: Number of transactions synced
            transactions_failed: Number of transactions failed
            error_message: Error message if failed
            started_at: Sync start time
        
        Returns:
            AccountingSyncLog
        """
        if not started_at:
            started_at = datetime.utcnow()
        
        sync_log = AccountingSyncLog(
            connection_id=connection_id,
            sync_type=sync_type,
            status=status,
            transactions_synced=transactions_synced,
            transactions_failed=transactions_failed,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            duration_seconds=(datetime.utcnow() - started_at).total_seconds(),
            error_message=error_message,
        )
        
        self.db.add(sync_log)
        await self.db.commit()
        await self.db.refresh(sync_log)
        
        # Update connection last_sync_at
        stmt = select(AccountingConnection).where(AccountingConnection.id == connection_id)
        result = await self.db.execute(stmt)
        connection = result.scalar_one_or_none()
        if connection:
            connection.last_sync_at = datetime.utcnow()
            if connection.sync_frequency != SyncFrequency.MANUAL.value:
                connection.next_sync_at = self._calculate_next_sync_time(
                    SyncFrequency(connection.sync_frequency)
                )
            await self.db.commit()
        
        return sync_log
    
    def _get_adapter(self, system: AccountingSystem) -> Optional[Any]:
        """Get adapter for accounting system"""
        if system == AccountingSystem.QUICKBOOKS:
            client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
            client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
            redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")
            if client_id and client_secret and redirect_uri:
                return QuickBooksAdapter(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                )
        elif system == AccountingSystem.XERO:
            client_id = os.getenv("XERO_CLIENT_ID")
            client_secret = os.getenv("XERO_CLIENT_SECRET")
            redirect_uri = os.getenv("XERO_REDIRECT_URI")
            if client_id and client_secret and redirect_uri:
                return XeroAdapter(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                )
        return None
