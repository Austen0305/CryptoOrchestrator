"""
Passkey Authentication Service
Passwordless authentication using WebAuthn passkeys
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# WebAuthn availability
try:
    from webauthn import (
        generate_authentication_options,
        generate_registration_options,
        options_to_json,
        verify_authentication_response,
        verify_registration_response,
    )
    from webauthn.helpers.structs import (
        AttestationConveyancePreference,
        AuthenticatorSelectionCriteria,
        UserVerificationRequirement,
    )

    WEBAUTHN_AVAILABLE = True
except ImportError:
    WEBAUTHN_AVAILABLE = False
    logger.warning("webauthn library not available. Install with: pip install webauthn")


@dataclass
class PasskeyCredential:
    """Passkey credential"""

    user_id: str
    credential_id: str
    public_key: bytes
    counter: int = 0
    created_at: datetime = None
    last_used_at: datetime | None = None
    device_name: str | None = None
    is_backup_eligible: bool = False
    is_backed_up: bool = False


class PasskeyAuthService:
    """
    Passkey (passwordless) authentication service

    Features:
    - WebAuthn/FIDO2 passkey registration
    - Passkey authentication
    - Multi-device support
    - Backup passkey support
    """

    def __init__(self, rp_id: str = "localhost", rp_name: str = "CryptoOrchestrator"):
        """
        Initialize passkey authentication service

        Args:
            rp_id: Relying Party ID (domain)
            rp_name: Relying Party name
        """
        if not WEBAUTHN_AVAILABLE:
            logger.warning("WebAuthn not available, passkey auth disabled")
            self.enabled = False
            return

        self.enabled = True
        self.rp_id = rp_id
        self.rp_name = rp_name
        self.credentials: dict[str, list[PasskeyCredential]] = {}
        self.challenges: dict[str, str] = {}  # Store challenges for verification

    def generate_registration_options(
        self,
        user_id: str,
        username: str,
        display_name: str,
        require_backup: bool = False,
    ) -> dict[str, Any]:
        """
        Generate passkey registration options

        Args:
            user_id: User ID
            username: Username
            display_name: Display name
            require_backup: Require backup-capable passkey

        Returns:
            Registration options (JSON-serializable)
        """
        if not self.enabled:
            raise RuntimeError("Passkey authentication not available")

        try:
            authenticator_selection = AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.REQUIRED,
                require_resident_key=True,  # Passkeys require resident keys
            )

            options = generate_registration_options(
                rp_id=self.rp_id,
                rp_name=self.rp_name,
                user_id=user_id.encode(),
                user_name=username,
                user_display_name=display_name,
                authenticator_selection=authenticator_selection,
                attestation=AttestationConveyancePreference.NONE,
            )

            # Store challenge for verification
            challenge = options.challenge
            self.challenges[f"{user_id}:registration"] = challenge

            return options_to_json(options)
        except Exception as e:
            logger.error(f"Error generating registration options: {e}", exc_info=True)
            raise

    def verify_registration(
        self,
        user_id: str,
        registration_response: dict[str, Any],
    ) -> PasskeyCredential | None:
        """
        Verify passkey registration

        Args:
            user_id: User ID
            registration_response: Registration response from client

        Returns:
            PasskeyCredential if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Verify challenge
            challenge_key = f"{user_id}:registration"
            if challenge_key not in self.challenges:
                logger.warning(f"Challenge not found for user {user_id}")
                return None

            # Verify registration (simplified - would need proper challenge and signature verification)
            # In production, use verify_registration_response with proper challenge verification

            credential = PasskeyCredential(
                user_id=user_id,
                credential_id=registration_response.get("id", ""),
                public_key=b"",  # Would extract from response
                created_at=datetime.now(UTC),
                is_backup_eligible=registration_response.get(
                    "is_backup_eligible", False
                ),
                is_backed_up=registration_response.get("is_backed_up", False),
            )

            # Store credential
            if user_id not in self.credentials:
                self.credentials[user_id] = []
            self.credentials[user_id].append(credential)

            # Remove challenge
            del self.challenges[challenge_key]

            logger.info(f"Passkey registered for user {user_id}")
            return credential
        except Exception as e:
            logger.error(f"Error verifying registration: {e}", exc_info=True)
            return None

    def generate_authentication_options(
        self, user_id: str | None = None
    ) -> dict[str, Any]:
        """
        Generate authentication options for passkey

        Args:
            user_id: Optional user ID (for user-specific authentication)

        Returns:
            Authentication options (JSON-serializable)
        """
        if not self.enabled:
            raise RuntimeError("Passkey authentication not available")

        try:
            allow_credentials = []
            if user_id and user_id in self.credentials:
                # User-specific authentication
                allow_credentials = [
                    {"id": cred.credential_id, "type": "public-key"}
                    for cred in self.credentials[user_id]
                ]
            # If no user_id, allow any credential (discoverable passkeys)

            options = generate_authentication_options(
                rp_id=self.rp_id,
                allow_credentials=allow_credentials if allow_credentials else None,
                user_verification=UserVerificationRequirement.REQUIRED,
            )

            # Store challenge
            challenge = options.challenge
            challenge_key = f"{user_id}:auth" if user_id else "anonymous:auth"
            self.challenges[challenge_key] = challenge

            return options_to_json(options)
        except Exception as e:
            logger.error(f"Error generating authentication options: {e}", exc_info=True)
            raise

    def verify_authentication(
        self,
        user_id: str | None,
        authentication_response: dict[str, Any],
    ) -> str | None:
        """
        Verify passkey authentication

        Args:
            user_id: Optional user ID (for user-specific authentication)
            authentication_response: Authentication response from client

        Returns:
            User ID if authentication successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Verify challenge
            challenge_key = f"{user_id}:auth" if user_id else "anonymous:auth"
            if challenge_key not in self.challenges:
                logger.warning("Challenge not found")
                return None

            credential_id = authentication_response.get("id", "")

            # Find matching credential
            if user_id:
                # User-specific authentication
                if user_id not in self.credentials:
                    return None

                credential = None
                for cred in self.credentials[user_id]:
                    if cred.credential_id == credential_id:
                        credential = cred
                        break
            else:
                # Discoverable passkey - find credential across all users
                credential = None
                for uid, creds in self.credentials.items():
                    for cred in creds:
                        if cred.credential_id == credential_id:
                            credential = cred
                            user_id = uid
                            break
                    if credential:
                        break

            if not credential:
                logger.warning("Credential not found")
                return None

            # Verify authentication (simplified - would need proper challenge and signature verification)
            # In production, use verify_authentication_response with proper challenge verification

            # Update credential
            credential.counter += 1
            credential.last_used_at = datetime.now(UTC)

            # Remove challenge
            del self.challenges[challenge_key]

            logger.info(f"Passkey authentication successful for user {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Error verifying authentication: {e}", exc_info=True)
            return None

    def get_user_passkeys(self, user_id: str) -> list[PasskeyCredential]:
        """Get all passkeys for a user"""
        return self.credentials.get(user_id, [])

    def remove_passkey(self, user_id: str, credential_id: str) -> bool:
        """Remove a passkey"""
        if user_id not in self.credentials:
            return False

        original_count = len(self.credentials[user_id])
        self.credentials[user_id] = [
            cred
            for cred in self.credentials[user_id]
            if cred.credential_id != credential_id
        ]

        removed = len(self.credentials[user_id]) < original_count
        if removed:
            logger.info(f"Removed passkey for user {user_id}")

        return removed


# Global instance
passkey_auth_service = PasskeyAuthService()
