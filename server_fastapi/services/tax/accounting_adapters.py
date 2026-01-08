"""
Accounting System OAuth Adapters
OAuth 2.0 integration adapters for QuickBooks Online and Xero
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None  # Optional dependency
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class AccountingSystem(str, Enum):
    """Supported accounting systems"""

    QUICKBOOKS = "quickbooks"
    XERO = "xero"


@dataclass
class OAuthCredentials:
    """OAuth 2.0 credentials"""

    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    token_type: str = "Bearer"
    realm_id: str | None = None  # QuickBooks realm ID
    tenant_id: str | None = None  # Xero tenant ID


@dataclass
class AccountingConnection:
    """Accounting system connection"""

    user_id: int
    system: AccountingSystem
    credentials: OAuthCredentials
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_sync_at: datetime | None = None
    sync_frequency: str = "daily"  # "daily", "weekly", "monthly"
    enabled: bool = True


class QuickBooksAdapter:
    """
    QuickBooks Online API adapter with OAuth 2.0

    Features:
    - OAuth 2.0 authentication
    - Transaction export
    - Journal entry creation
    - Chart of accounts mapping
    - Customer/vendor creation
    - Automated sync
    """

    def _check_httpx(self):
        """Check if httpx is available"""
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for OAuth operations. Install with: pip install httpx"
            )

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        environment: str = "sandbox",  # "sandbox" or "production"
    ):
        """
        Initialize QuickBooks adapter

        Args:
            client_id: QuickBooks OAuth client ID
            client_secret: QuickBooks OAuth client secret
            redirect_uri: OAuth redirect URI
            environment: API environment (sandbox or production)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.environment = environment

        if environment == "sandbox":
            self.base_url = "https://sandbox-quickbooks.api.intuit.com"
            self.auth_url = "https://appcenter.intuit.com/connect/oauth2"
        else:
            self.base_url = "https://quickbooks.api.intuit.com"
            self.auth_url = "https://appcenter.intuit.com/connect/oauth2"

    def get_authorization_url(self, state: str) -> str:
        """
        Get OAuth authorization URL

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"

    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
    ) -> OAuthCredentials:
        """
        Exchange authorization code for access token

        Args:
            authorization_code: Authorization code from OAuth callback

        Returns:
            OAuthCredentials
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            data = response.json()

            return OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_at=datetime.utcnow()
                + timedelta(seconds=data.get("expires_in", 3600)),
                token_type=data.get("token_type", "Bearer"),
                realm_id=data.get("realmId"),  # QuickBooks realm ID
            )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> OAuthCredentials:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token

        Returns:
            OAuthCredentials
        """
        self._check_httpx()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            data = response.json()

            return OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
                expires_at=datetime.utcnow()
                + timedelta(seconds=data.get("expires_in", 3600)),
                token_type=data.get("token_type", "Bearer"),
            )

    async def create_journal_entry(
        self,
        credentials: OAuthCredentials,
        transactions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create journal entry in QuickBooks

        Args:
            credentials: OAuth credentials
            transactions: List of transaction dictionaries

        Returns:
            Created journal entry response
        """
        self._check_httpx()

        # Build QuickBooks journal entry format
        journal_entry = {"Line": []}

        for tx in transactions:
            journal_entry["Line"].append(
                {
                    "DetailType": "JournalEntryLineDetail",
                    "Amount": tx.get("amount", 0.0),
                    "JournalEntryLineDetail": {
                        "PostingType": "Debit" if tx.get("amount", 0) > 0 else "Credit",
                        "AccountRef": {
                            "value": tx.get("account_code", "12000"),  # Account code
                        },
                    },
                    "Description": tx.get("description", "Crypto Transaction"),
                }
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v3/company/{credentials.realm_id}/journalentry",
                json=journal_entry,
                headers={
                    "Authorization": f"{credentials.token_type} {credentials.access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_accounts(
        self,
        credentials: OAuthCredentials,
    ) -> list[dict[str, Any]]:
        """
        Get chart of accounts from QuickBooks

        Args:
            credentials: OAuth credentials

        Returns:
            List of accounts
        """
        self._check_httpx()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v3/company/{credentials.realm_id}/accounts",
                headers={
                    "Authorization": f"{credentials.token_type} {credentials.access_token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("QueryResponse", {}).get("Account", [])


class XeroAdapter:
    """
    Xero API adapter with OAuth 2.0

    Features:
    - OAuth 2.0 authentication
    - Transaction export
    - Bank transaction import
    - Invoice creation
    - Contact management
    - Automated sync
    """

    def _check_httpx(self):
        """Check if httpx is available"""
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for OAuth operations. Install with: pip install httpx"
            )

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ):
        """
        Initialize Xero adapter

        Args:
            client_id: Xero OAuth client ID
            client_secret: Xero OAuth client secret
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = "https://api.xero.com"
        self.auth_url = "https://login.xero.com/identity/connect/authorize"
        self.token_url = "https://identity.xero.com/connect/token"

    def get_authorization_url(self, state: str) -> str:
        """
        Get OAuth authorization URL

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "accounting.transactions accounting.contacts",
            "state": state,
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"

    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
    ) -> OAuthCredentials:
        """
        Exchange authorization code for access token

        Args:
            authorization_code: Authorization code from OAuth callback

        Returns:
            OAuthCredentials
        """
        self._check_httpx()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.redirect_uri,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            data = response.json()

            # Xero returns tenant_id in the response
            tenant_id = None
            if "id_token" in data:
                # Extract tenant_id from id_token (simplified)
                # In production, decode JWT to get tenant_id
                pass

            return OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                expires_at=datetime.utcnow()
                + timedelta(seconds=data.get("expires_in", 3600)),
                token_type=data.get("token_type", "Bearer"),
                tenant_id=tenant_id,
            )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> OAuthCredentials:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token

        Returns:
            OAuthCredentials
        """
        self._check_httpx()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            data = response.json()

            return OAuthCredentials(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", refresh_token),
                expires_at=datetime.utcnow()
                + timedelta(seconds=data.get("expires_in", 3600)),
                token_type=data.get("token_type", "Bearer"),
            )

    async def create_bank_transaction(
        self,
        credentials: OAuthCredentials,
        transactions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Create bank transaction in Xero

        Args:
            credentials: OAuth credentials
            transactions: List of transaction dictionaries

        Returns:
            Created transaction response
        """
        self._check_httpx()

        # Build Xero bank transaction format
        bank_transactions = []

        for tx in transactions:
            bank_transactions.append(
                {
                    "Type": "SPEND" if tx.get("amount", 0) < 0 else "RECEIVE",
                    "Contact": {
                        "Name": "Crypto Trading",
                    },
                    "LineItems": [
                        {
                            "Description": tx.get("description", "Crypto Transaction"),
                            "Quantity": 1,
                            "UnitAmount": abs(tx.get("amount", 0.0)),
                            "AccountCode": tx.get("account_code", "200"),
                        }
                    ],
                    "Date": tx.get("date", datetime.utcnow().isoformat()),
                    "Reference": tx.get("reference", ""),
                }
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api.xro/2.0/BankTransactions",
                json={"BankTransactions": bank_transactions},
                headers={
                    "Authorization": f"{credentials.token_type} {credentials.access_token}",
                    "Xero-tenant-id": credentials.tenant_id or "",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_accounts(
        self,
        credentials: OAuthCredentials,
    ) -> list[dict[str, Any]]:
        """
        Get chart of accounts from Xero

        Args:
            credentials: OAuth credentials

        Returns:
            List of accounts
        """
        self._check_httpx()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api.xro/2.0/Accounts",
                headers={
                    "Authorization": f"{credentials.token_type} {credentials.access_token}",
                    "Xero-tenant-id": credentials.tenant_id or "",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("Accounts", [])
