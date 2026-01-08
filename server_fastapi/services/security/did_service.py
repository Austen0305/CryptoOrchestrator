"""
Decentralized Identity (DID) Service
W3C DID standard implementation for self-sovereign identity
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# DID library availability
try:
    # Using didkit or similar DID library
    # For now, we'll create a foundation that can be extended
    DID_AVAILABLE = False  # Set to True when library is installed
except ImportError:
    DID_AVAILABLE = False
    logger.warning(
        "DID library not available. Install with: pip install didkit or similar"
    )


@dataclass
class DIDDocument:
    """DID Document (W3C standard)"""

    did: str  # Decentralized Identifier
    context: list[str] = field(default_factory=lambda: ["https://www.w3.org/ns/did/v1"])
    id: str = ""  # Same as did
    verification_methods: list[dict[str, Any]] = field(default_factory=list)
    authentication: list[str] = field(default_factory=list)
    service_endpoints: list[dict[str, Any]] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.utcnow)
    updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DIDCredential:
    """Verifiable Credential"""

    credential_id: str
    did: str  # Issuer DID
    subject_did: str  # Subject DID
    credential_type: list[str]
    claims: dict[str, Any]
    proof: dict[str, Any]  # Cryptographic proof
    issued: datetime = field(default_factory=datetime.utcnow)
    expires: datetime | None = None


@dataclass
class DIDPresentation:
    """Verifiable Presentation"""

    presentation_id: str
    holder_did: str
    verifiable_credentials: list[DIDCredential]
    proof: dict[str, Any]
    created: datetime = field(default_factory=datetime.utcnow)


class DIDService:
    """
    Decentralized Identity (DID) service

    Features:
    - DID creation and management
    - DID Document management
    - Verifiable Credentials (VC)
    - Verifiable Presentations (VP)
    - DID resolution
    - Key management for DIDs

    Note: This is a foundation that can be extended with actual DID libraries
    like didkit, did-jwt, or other W3C DID implementations.
    """

    def __init__(self):
        self.did_documents: dict[str, DIDDocument] = {}
        self.credentials: dict[str, DIDCredential] = {}
        self.presentations: dict[str, DIDPresentation] = {}
        self.enabled = DID_AVAILABLE

    def create_did(
        self,
        method: str = "key",
        user_id: int | None = None,
    ) -> DIDDocument:
        """
        Create a new DID

        Args:
            method: DID method (e.g., "key", "web", "ethr")
            user_id: Optional user ID to associate

        Returns:
            DIDDocument

        Note: DID format: did:method:identifier
        - did:key:... (self-contained)
        - did:web:... (web-based)
        - did:ethr:... (Ethereum-based)
        """
        # Generate DID identifier
        identifier = hashlib.sha256(
            f"{method}:{user_id or ''}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:32]

        did = f"did:{method}:{identifier}"

        # Generate verification method (public key)
        verification_method = {
            "id": f"{did}#keys-1",
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": self._generate_public_key(did),
        }

        document = DIDDocument(
            did=did,
            id=did,
            verification_methods=[verification_method],
            authentication=[f"{did}#keys-1"],
        )

        self.did_documents[did] = document

        logger.info(f"Created DID: {did}")

        return document

    def resolve_did(self, did: str) -> DIDDocument | None:
        """
        Resolve a DID to its document

        Args:
            did: Decentralized Identifier

        Returns:
            DIDDocument if found
        """
        return self.did_documents.get(did)

    def issue_credential(
        self,
        issuer_did: str,
        subject_did: str,
        credential_type: list[str],
        claims: dict[str, Any],
        expires_days: int | None = None,
    ) -> DIDCredential:
        """
        Issue a verifiable credential

        Args:
            issuer_did: DID of issuer
            subject_did: DID of subject
            credential_type: List of credential types
            claims: Credential claims
            expires_days: Optional expiration in days

        Returns:
            DIDCredential
        """
        # Verify issuer exists
        if issuer_did not in self.did_documents:
            raise ValueError(f"Issuer DID {issuer_did} not found")

        credential_id = hashlib.sha256(
            f"{issuer_did}:{subject_did}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()

        # Generate proof (simplified - in production, use actual cryptographic proof)
        proof = self._generate_proof(issuer_did, credential_id, claims)

        credential = DIDCredential(
            credential_id=credential_id,
            did=issuer_did,
            subject_did=subject_did,
            credential_type=credential_type,
            claims=claims,
            proof=proof,
            expires=(
                datetime.utcnow() + timedelta(days=expires_days)
                if expires_days
                else None
            ),
        )

        self.credentials[credential_id] = credential

        logger.info(
            f"Issued credential {credential_id} from {issuer_did} to {subject_did}"
        )

        return credential

    def create_presentation(
        self,
        holder_did: str,
        credential_ids: list[str],
    ) -> DIDPresentation:
        """
        Create a verifiable presentation

        Args:
            holder_did: DID of holder
            credential_ids: List of credential IDs to include

        Returns:
            DIDPresentation
        """
        # Get credentials
        credentials = [
            self.credentials[cid] for cid in credential_ids if cid in self.credentials
        ]

        if not credentials:
            raise ValueError("No valid credentials found")

        presentation_id = hashlib.sha256(
            f"{holder_did}:{':'.join(credential_ids)}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()

        # Generate proof
        proof = self._generate_proof(
            holder_did, presentation_id, {"credentials": credential_ids}
        )

        presentation = DIDPresentation(
            presentation_id=presentation_id,
            holder_did=holder_did,
            verifiable_credentials=credentials,
            proof=proof,
        )

        self.presentations[presentation_id] = presentation

        logger.info(f"Created presentation {presentation_id} for {holder_did}")

        return presentation

    def verify_credential(self, credential_id: str) -> bool:
        """Verify a verifiable credential"""
        credential = self.credentials.get(credential_id)
        if not credential:
            return False

        # Check expiration
        if credential.expires and datetime.utcnow() > credential.expires:
            return False

        # Verify proof (simplified)
        return self._verify_proof(
            credential.did,
            credential_id,
            credential.claims,
            credential.proof,
        )

    def verify_presentation(self, presentation_id: str) -> bool:
        """Verify a verifiable presentation"""
        presentation = self.presentations.get(presentation_id)
        if not presentation:
            return False

        # Verify all credentials
        for cred in presentation.verifiable_credentials:
            if not self.verify_credential(cred.credential_id):
                return False

        # Verify presentation proof
        return self._verify_proof(
            presentation.holder_did,
            presentation_id,
            {
                "credentials": [
                    c.credential_id for c in presentation.verifiable_credentials
                ]
            },
            presentation.proof,
        )

    def _generate_public_key(self, did: str) -> str:
        """Generate public key for DID (simplified)"""
        key_data = f"{did}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _generate_proof(
        self,
        did: str,
        credential_id: str,
        claims: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate cryptographic proof (simplified)"""
        # In production, this would use actual cryptographic signatures
        proof_data = f"{did}:{credential_id}:{json.dumps(claims, sort_keys=True)}"
        signature = hashlib.sha256(proof_data.encode()).hexdigest()

        return {
            "type": "Ed25519Signature2020",
            "created": datetime.utcnow().isoformat(),
            "proofPurpose": "assertionMethod",
            "verificationMethod": f"{did}#keys-1",
            "proofValue": signature,
        }

    def _verify_proof(
        self,
        did: str,
        credential_id: str,
        claims: dict[str, Any],
        proof: dict[str, Any],
    ) -> bool:
        """Verify cryptographic proof (simplified)"""
        # In production, this would verify the signature
        expected = self._generate_proof(did, credential_id, claims)
        return proof.get("proofValue") == expected.get("proofValue")


# Global instance
did_service = DIDService()
