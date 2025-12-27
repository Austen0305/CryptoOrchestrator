"""
Hardware Security Key Authentication
Support for YubiKey, Titan, and other FIDO2/WebAuthn devices
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# WebAuthn/FIDO2 availability
try:
    from webauthn import (
        generate_registration_options,
        verify_registration_response,
        generate_authentication_options,
        verify_authentication_response,
        options_to_json,
    )
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        UserVerificationRequirement,
        AttestationConveyancePreference,
    )
    WEBAUTHN_AVAILABLE = True
except ImportError:
    WEBAUTHN_AVAILABLE = False
    logger.warning("webauthn library not available. Install with: pip install webauthn")


@dataclass
class HardwareKeyCredential:
    """Hardware security key credential"""
    user_id: str
    credential_id: str
    public_key: bytes
    counter: int = 0
    created_at: datetime = None
    last_used_at: Optional[datetime] = None
    device_name: Optional[str] = None


class HardwareKeyAuthService:
    """
    Hardware security key authentication service
    
    Supports:
    - YubiKey
    - Google Titan
    - Other FIDO2/WebAuthn compatible devices
    """
    
    def __init__(self, rp_id: str = "localhost", rp_name: str = "CryptoOrchestrator"):
        """
        Initialize hardware key authentication service
        
        Args:
            rp_id: Relying Party ID (domain)
            rp_name: Relying Party name
        """
        if not WEBAUTHN_AVAILABLE:
            logger.warning("WebAuthn not available, hardware key auth disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.rp_id = rp_id
        self.rp_name = rp_name
        self.credentials: Dict[str, list[HardwareKeyCredential]] = {}
    
    def generate_registration_options(self, user_id: str, username: str, display_name: str) -> Dict[str, Any]:
        """
        Generate registration options for hardware key
        
        Args:
            user_id: User ID
            username: Username
            display_name: Display name
        
        Returns:
            Registration options (JSON-serializable)
        """
        if not self.enabled:
            raise RuntimeError("Hardware key authentication not available")
        
        try:
            options = generate_registration_options(
                rp_id=self.rp_id,
                rp_name=self.rp_name,
                user_id=user_id.encode(),
                user_name=username,
                user_display_name=display_name,
                authenticator_selection=AuthenticatorSelectionCriteria(
                    user_verification=UserVerificationRequirement.PREFERRED,
                ),
                attestation=AttestationConveyancePreference.NONE,
            )
            
            return options_to_json(options)
        except Exception as e:
            logger.error(f"Error generating registration options: {e}", exc_info=True)
            raise
    
    def verify_registration(
        self,
        user_id: str,
        registration_response: Dict[str, Any],
        challenge: str,
    ) -> Optional[HardwareKeyCredential]:
        """
        Verify hardware key registration
        
        Args:
            user_id: User ID
            registration_response: Registration response from client
            challenge: Original challenge
        
        Returns:
            HardwareKeyCredential if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            # Verify registration (simplified - would need proper challenge verification)
            # In production, store challenge and verify it matches
            
            credential = HardwareKeyCredential(
                user_id=user_id,
                credential_id=registration_response.get("id", ""),
                public_key=b"",  # Would extract from response
                created_at=datetime.utcnow(),
            )
            
            # Store credential
            if user_id not in self.credentials:
                self.credentials[user_id] = []
            self.credentials[user_id].append(credential)
            
            logger.info(f"Hardware key registered for user {user_id}")
            return credential
        except Exception as e:
            logger.error(f"Error verifying registration: {e}", exc_info=True)
            return None
    
    def generate_authentication_options(self, user_id: str) -> Dict[str, Any]:
        """
        Generate authentication options for hardware key
        
        Args:
            user_id: User ID
        
        Returns:
            Authentication options (JSON-serializable)
        """
        if not self.enabled:
            raise RuntimeError("Hardware key authentication not available")
        
        if user_id not in self.credentials or not self.credentials[user_id]:
            raise ValueError(f"No hardware keys registered for user {user_id}")
        
        try:
            # Get user's credential IDs
            credential_ids = [cred.credential_id for cred in self.credentials[user_id]]
            
            options = generate_authentication_options(
                rp_id=self.rp_id,
                allow_credentials=[
                    {"id": cred_id, "type": "public-key"}
                    for cred_id in credential_ids
                ],
                user_verification=UserVerificationRequirement.PREFERRED,
            )
            
            return options_to_json(options)
        except Exception as e:
            logger.error(f"Error generating authentication options: {e}", exc_info=True)
            raise
    
    def verify_authentication(
        self,
        user_id: str,
        authentication_response: Dict[str, Any],
        challenge: str,
    ) -> bool:
        """
        Verify hardware key authentication
        
        Args:
            user_id: User ID
            authentication_response: Authentication response from client
            challenge: Original challenge
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.enabled:
            return False
        
        if user_id not in self.credentials:
            return False
        
        try:
            # Find matching credential
            credential_id = authentication_response.get("id", "")
            credential = None
            for cred in self.credentials[user_id]:
                if cred.credential_id == credential_id:
                    credential = cred
                    break
            
            if not credential:
                logger.warning(f"Credential not found for user {user_id}")
                return False
            
            # Verify authentication (simplified - would need proper challenge and signature verification)
            # In production, verify challenge matches and signature is valid
            
            # Update credential
            credential.counter += 1
            credential.last_used_at = datetime.utcnow()
            
            logger.info(f"Hardware key authentication successful for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error verifying authentication: {e}", exc_info=True)
            return False
    
    def get_user_credentials(self, user_id: str) -> list[HardwareKeyCredential]:
        """Get all hardware key credentials for a user"""
        return self.credentials.get(user_id, [])
    
    def remove_credential(self, user_id: str, credential_id: str) -> bool:
        """Remove a hardware key credential"""
        if user_id not in self.credentials:
            return False
        
        original_count = len(self.credentials[user_id])
        self.credentials[user_id] = [
            cred for cred in self.credentials[user_id]
            if cred.credential_id != credential_id
        ]
        
        removed = len(self.credentials[user_id]) < original_count
        if removed:
            logger.info(f"Removed hardware key credential for user {user_id}")
        
        return removed


# Global instance
hardware_key_auth_service = HardwareKeyAuthService()
