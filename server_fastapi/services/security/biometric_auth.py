"""
Biometric Authentication Service
Fingerprint and face ID authentication
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import secrets

logger = logging.getLogger(__name__)

# Biometric library availability
try:
    # Using WebAuthn for biometric authentication
    # Biometrics are handled through WebAuthn's authenticator API
    BIOMETRIC_AVAILABLE = True  # WebAuthn supports biometrics
except ImportError:
    BIOMETRIC_AVAILABLE = False
    logger.warning("Biometric authentication requires WebAuthn support")


@dataclass
class BiometricCredential:
    """Biometric authentication credential"""
    credential_id: str
    user_id: int
    biometric_type: str  # "fingerprint", "face_id", "voice"
    device_id: str
    public_key: bytes
    created_at: datetime
    last_used: Optional[datetime] = None
    enabled: bool = True


@dataclass
class BiometricChallenge:
    """Biometric authentication challenge"""
    challenge_id: str
    user_id: int
    challenge_data: bytes
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


class BiometricAuthService:
    """
    Biometric authentication service
    
    Features:
    - Fingerprint authentication
    - Face ID authentication
    - Voice recognition (optional)
    - Device-based biometric storage
    - Challenge-response authentication
    
    Note: Biometric authentication uses WebAuthn's authenticator API,
    which supports platform authenticators (Touch ID, Face ID, Windows Hello).
    """
    
    def __init__(self):
        self.credentials: Dict[str, BiometricCredential] = {}
        self.challenges: Dict[str, BiometricChallenge] = {}
        self.enabled = BIOMETRIC_AVAILABLE
    
    def register_biometric(
        self,
        user_id: int,
        biometric_type: str,
        device_id: str,
        public_key: bytes,
        credential_id: Optional[str] = None,
    ) -> BiometricCredential:
        """
        Register biometric credential
        
        Args:
            user_id: User ID
            biometric_type: Type of biometric ("fingerprint", "face_id", "voice")
            device_id: Device identifier
            public_key: Public key from WebAuthn authenticator
            credential_id: Optional credential ID
        
        Returns:
            BiometricCredential
        
        Note: In production, this integrates with WebAuthn's platform authenticators:
        - iOS: Face ID / Touch ID
        - Android: Fingerprint / Face unlock
        - Windows: Windows Hello
        - macOS: Touch ID
        """
        if not self.enabled:
            raise RuntimeError("Biometric authentication not available")
        
        if biometric_type not in ["fingerprint", "face_id", "voice"]:
            raise ValueError(f"Invalid biometric type: {biometric_type}")
        
        cred_id = credential_id or hashlib.sha256(
            f"{user_id}:{device_id}:{biometric_type}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        credential = BiometricCredential(
            credential_id=cred_id,
            user_id=user_id,
            biometric_type=biometric_type,
            device_id=device_id,
            public_key=public_key,
            created_at=datetime.utcnow(),
        )
        
        self.credentials[cred_id] = credential
        
        logger.info(
            f"Registered {biometric_type} credential for user {user_id} "
            f"on device {device_id}"
        )
        
        return credential
    
    def create_challenge(
        self,
        user_id: int,
        credential_id: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> BiometricChallenge:
        """
        Create authentication challenge
        
        Args:
            user_id: User ID
            credential_id: Optional specific credential ID
            timeout_seconds: Challenge timeout
        
        Returns:
            BiometricChallenge
        """
        challenge_data = secrets.token_bytes(32)
        challenge_id = hashlib.sha256(
            f"{user_id}:{challenge_data.hex()}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        challenge = BiometricChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            challenge_data=challenge_data,
            expires_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
        )
        
        self.challenges[challenge_id] = challenge
        
        logger.debug(f"Created biometric challenge {challenge_id} for user {user_id}")
        
        return challenge
    
    def verify_biometric(
        self,
        challenge_id: str,
        credential_id: str,
        signature: bytes,
        authenticator_data: bytes,
    ) -> bool:
        """
        Verify biometric authentication
        
        Args:
            challenge_id: Challenge ID
            credential_id: Credential ID
            signature: Signature from biometric authenticator
            authenticator_data: Authenticator data from WebAuthn
        
        Returns:
            True if verification successful
        """
        # Get challenge
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return False
        
        # Check expiration
        if datetime.utcnow() > challenge.expires_at:
            logger.warning(f"Challenge {challenge_id} expired")
            return False
        
        # Get credential
        credential = self.credentials.get(credential_id)
        if not credential or not credential.enabled:
            return False
        
        # Verify signature (simplified - in production, use WebAuthn verification)
        # This would verify:
        # 1. Signature is valid for challenge + authenticator_data
        # 2. Authenticator data includes user verification
        # 3. Challenge matches
        is_valid = self._verify_signature(
            challenge.challenge_data,
            authenticator_data,
            signature,
            credential.public_key,
        )
        
        if is_valid:
            credential.last_used = datetime.utcnow()
            # Remove used challenge
            del self.challenges[challenge_id]
            logger.info(f"Biometric authentication successful for credential {credential_id}")
        else:
            logger.warning(f"Biometric authentication failed for credential {credential_id}")
        
        return is_valid
    
    def get_user_credentials(self, user_id: int) -> List[BiometricCredential]:
        """Get all biometric credentials for a user"""
        return [
            cred for cred in self.credentials.values()
            if cred.user_id == user_id and cred.enabled
        ]
    
    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a biometric credential"""
        if credential_id in self.credentials:
            self.credentials[credential_id].enabled = False
            logger.info(f"Revoked biometric credential {credential_id}")
            return True
        return False
    
    def _verify_signature(
        self,
        challenge: bytes,
        authenticator_data: bytes,
        signature: bytes,
        public_key: bytes,
    ) -> bool:
        """Verify biometric signature (simplified)"""
        # In production, this would use WebAuthn's signature verification
        # which verifies the signature against the public key using
        # the challenge and authenticator data
        # This is a placeholder
        expected = hashlib.sha256(
            challenge + authenticator_data + public_key
        ).digest()
        return len(signature) > 0  # Placeholder verification


# Global instance
biometric_auth_service = BiometricAuthService()
