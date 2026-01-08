"""
Tests for Social Recovery System
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server_fastapi.models.institutional_wallet import InstitutionalWallet
from server_fastapi.models.social_recovery import (
    GuardianStatus,
    RecoveryRequestStatus,
    SocialRecoveryGuardian,
)
from server_fastapi.models.user import User
from server_fastapi.services.institutional.social_recovery import SocialRecoveryService

pytestmark = pytest.mark.asyncio


class TestSocialRecoveryGuardian:
    """Tests for SocialRecoveryGuardian model and service"""

    async def test_add_guardian(self, db_session: AsyncSession, test_user: User):
        """Test adding a guardian to a wallet"""
        # Create institutional wallet
        wallet = InstitutionalWallet(
            user_id=test_user.id,
            wallet_type="multisig",
            chain_id=1,
            required_signatures=2,
            total_signers=3,
            status="active",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db_session.refresh(wallet)

        # Add guardian
        service = SocialRecoveryService(db_session)
        guardian = await service.add_guardian(
            wallet_id=wallet.id,
            guardian_user_id=test_user.id,
            added_by=test_user.id,
            notes="Test guardian",
        )

        assert guardian.id is not None
        assert guardian.wallet_id == wallet.id
        assert guardian.status == GuardianStatus.PENDING.value

        # Verify in database
        stmt = select(SocialRecoveryGuardian).where(
            SocialRecoveryGuardian.id == guardian.id
        )
        result = await db.execute(stmt)
        db_guardian = result.scalar_one_or_none()
        assert db_guardian is not None
        assert db_guardian.status == GuardianStatus.PENDING.value

    async def test_remove_guardian(self, db_session: AsyncSession, test_user: User):
        """Test removing a guardian"""
        # Create wallet and guardian
        wallet = InstitutionalWallet(
            user_id=test_user.id,
            wallet_type="multisig",
            chain_id=1,
            status="active",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db.refresh(wallet)

        service = SocialRecoveryService(db_session)
        guardian = await service.add_guardian(
            wallet_id=wallet.id,
            guardian_user_id=test_user.id,
            added_by=test_user.id,
        )

        # Remove guardian
        success = await service.remove_guardian(
            wallet_id=wallet.id,
            guardian_id=guardian.id,
            removed_by=test_user.id,
        )

        assert success is True

        # Verify removed
        stmt = select(SocialRecoveryGuardian).where(
            SocialRecoveryGuardian.id == guardian.id
        )
        result = await db.execute(stmt)
        db_guardian = result.scalar_one_or_none()
        assert db_guardian is None

    async def test_get_guardians(self, db_session: AsyncSession, test_user: User):
        """Test getting guardians for a wallet"""
        wallet = InstitutionalWallet(
            user_id=test_user.id,
            wallet_type="multisig",
            chain_id=1,
            status="active",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db.refresh(wallet)

        service = SocialRecoveryService(db_session)

        # Add multiple guardians
        guardian1 = await service.add_guardian(
            wallet_id=wallet.id,
            guardian_user_id=test_user.id,
            added_by=test_user.id,
        )
        guardian1.status = GuardianStatus.ACTIVE.value
        await db_session.commit()

        # Get guardians
        guardians = await service.get_guardians(wallet.id)
        assert len(guardians) == 1
        assert guardians[0].id == guardian1.id


class TestRecoveryRequest:
    """Tests for RecoveryRequest model and service"""

    async def test_create_recovery_request(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating a recovery request"""
        # Create wallet
        wallet = InstitutionalWallet(
            user_id=test_user.id,
            wallet_type="multisig",
            chain_id=1,
            status="active",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db.refresh(wallet)

        # Add guardians
        service = SocialRecoveryService(db_session)
        for i in range(3):
            guardian = await service.add_guardian(
                wallet_id=wallet.id,
                guardian_user_id=test_user.id,
                added_by=test_user.id,
            )
            guardian.status = GuardianStatus.ACTIVE.value
        await db_session.commit()

        # Create recovery request
        recovery_request = await service.create_recovery_request(
            wallet_id=wallet.id,
            requester_id=test_user.id,
            reason="Lost access to wallet",
            required_approvals=2,
            time_lock_days=7,
        )

        assert recovery_request.id is not None
        assert recovery_request.wallet_id == wallet.id
        assert recovery_request.requester_id == test_user.id
        assert recovery_request.status == RecoveryRequestStatus.PENDING.value
        assert recovery_request.required_approvals == 2
        assert recovery_request.time_lock_days == 7
        assert recovery_request.unlock_time is not None

    async def test_approve_recovery(self, db_session: AsyncSession, test_user: User):
        """Test approving a recovery request"""
        # Setup wallet and guardians
        wallet = InstitutionalWallet(
            user_id=test_user.id,
            wallet_type="multisig",
            chain_id=1,
            status="active",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db.refresh(wallet)

        service = SocialRecoveryService(db_session)
        guardian = await service.add_guardian(
            wallet_id=wallet.id,
            guardian_user_id=test_user.id,
            added_by=test_user.id,
        )
        guardian.status = GuardianStatus.ACTIVE.value
        await db_session.commit()

        # Create recovery request
        recovery_request = await service.create_recovery_request(
            wallet_id=wallet.id,
            requester_id=test_user.id,
            reason="Test recovery",
            required_approvals=1,
        )

        # Approve recovery
        success = await service.approve_recovery(
            recovery_request_id=recovery_request.id,
            guardian_id=guardian.id,
            approver_id=test_user.id,
        )

        assert success is True

        # Verify approval
        updated_request = await service.get_recovery_request(recovery_request.id)
        assert updated_request.current_approvals == 1
        assert updated_request.status == RecoveryRequestStatus.APPROVED.value

    async def test_execute_recovery(self, db_session: AsyncSession, test_user: User):
        """Test executing a recovery after approvals"""
        # Setup wallet, guardians, and recovery request
        wallet = InstitutionalWallet(
            user_id=test_user.id,
            wallet_type="multisig",
            chain_id=1,
            status="active",
        )
        db_session.add(wallet)
        await db_session.commit()
        await db.refresh(wallet)

        service = SocialRecoveryService(db_session)
        guardian = await service.add_guardian(
            wallet_id=wallet.id,
            guardian_user_id=test_user.id,
            added_by=test_user.id,
        )
        guardian.status = GuardianStatus.ACTIVE.value
        await db_session.commit()

        recovery_request = await service.create_recovery_request(
            wallet_id=wallet.id,
            requester_id=test_user.id,
            reason="Test",
            required_approvals=1,
            time_lock_days=0,  # No time lock for testing
        )

        # Approve
        await service.approve_recovery(
            recovery_request_id=recovery_request.id,
            guardian_id=guardian.id,
            approver_id=test_user.id,
        )

        # Set unlock time to past for testing
        recovery_request.unlock_time = datetime.utcnow() - timedelta(days=1)
        await db_session.commit()

        # Execute recovery
        success = await service.execute_recovery(
            recovery_request_id=recovery_request.id,
            executor_id=test_user.id,
        )

        assert success is True

        # Verify execution
        updated_request = await service.get_recovery_request(recovery_request.id)
        assert updated_request.status == RecoveryRequestStatus.COMPLETED.value
        assert updated_request.completed_at is not None
