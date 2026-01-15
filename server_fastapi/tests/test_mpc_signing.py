"""
Tests for MPC Signing Service (Free version)
"""

import pytest

from server_fastapi.services.mpc_signing_service import (
    LocalThresholdSigner,
    MPCProvider,
    MPCSigningService,
    SignatureStatus,
    get_mpc_signing_service,
)


class TestLocalThresholdSigner:
    """Tests for the free local signer"""

    @pytest.fixture
    def signer(self):
        return LocalThresholdSigner(threshold=2, total_parties=3)

    @pytest.mark.asyncio
    async def test_initialize(self, signer):
        """Test initialization"""
        await signer.initialize()
        assert signer._initialized is True

    @pytest.mark.asyncio
    async def test_sign_transaction(self, signer):
        """Test signing produces valid response"""
        await signer.initialize()

        digest = b"0" * 32
        response = await signer.sign_transaction(
            digest=digest,
            key_id="test_key",
            chain_id=1,
        )

        assert response.status == SignatureStatus.COMPLETED
        assert response.signature is not None
        assert response.signature.startswith("0x") or response.signature.startswith("0")
        assert response.r is not None
        assert response.s is not None
        assert response.v in (0, 1, 27, 28)
        assert response.latency_ms > 0
        assert response.provider == MPCProvider.LOCAL_THRESHOLD

    @pytest.mark.asyncio
    async def test_create_wallet(self, signer):
        """Test wallet creation returns proper structure"""
        await signer.initialize()

        wallet = await signer.create_wallet(
            wallet_name="test_wallet",
            threshold=2,
            total_parties=3,
        )

        assert wallet["wallet_id"].startswith("local_")
        assert wallet["name"] == "test_wallet"
        assert wallet["threshold"] == 2
        assert wallet["total_parties"] == 3
        assert wallet["provider"] == MPCProvider.LOCAL_THRESHOLD.value

    @pytest.mark.asyncio
    async def test_health_check(self, signer):
        """Test health check response"""
        await signer.initialize()

        health = await signer.health_check()

        assert health["provider"] == MPCProvider.LOCAL_THRESHOLD.value
        assert health["status"] == "healthy"
        assert health["is_free"] is True


class TestMPCSigningService:
    """Tests for the unified MPC service"""

    @pytest.fixture
    def service(self):
        return MPCSigningService()

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization"""
        await service.initialize()
        assert service._initialized is True

    @pytest.mark.asyncio
    async def test_sign_transaction(self, service):
        """Test signing through unified service"""
        await service.initialize()

        digest = bytes.fromhex("a" * 64)  # 32 bytes
        response = await service.sign_transaction(
            digest=digest,
            key_id="test_key",
            chain_id=1,
        )

        assert response.status == SignatureStatus.COMPLETED
        assert response.signature is not None

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, service):
        """Test that metrics are updated after signing"""
        await service.initialize()

        initial_count = service._metrics["total_signatures"]

        digest = b"0" * 32
        await service.sign_transaction(digest, "key", 1)

        assert service._metrics["total_signatures"] == initial_count + 1
        assert service._metrics["avg_latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test health check includes provider info"""
        await service.initialize()

        health = await service.health_check()

        assert health["service"] == "mpc_signing"
        assert health["initialized"] is True
        assert health["is_free"] is True
        assert "metrics" in health


class TestGetMPCSigningService:
    """Test singleton factory"""

    @pytest.mark.asyncio
    async def test_returns_same_instance(self):
        """Test singleton pattern"""
        # Reset singleton
        import server_fastapi.services.mpc_signing_service as module

        module._mpc_signing_service = None

        service1 = await get_mpc_signing_service()
        service2 = await get_mpc_signing_service()

        assert service1 is service2
