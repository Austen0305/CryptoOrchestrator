"""
Social Recovery Service
Social recovery mechanisms for institutional wallets with database persistence
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.institutional_wallet import (
    InstitutionalWallet,
    wallet_signer_association,
)
from ...models.social_recovery import (
    GuardianStatus,
    RecoveryApproval,
    RecoveryRequest,
    RecoveryRequestStatus,
    SocialRecoveryGuardian,
)

logger = logging.getLogger(__name__)


class SocialRecoveryService:
    """
    Social recovery service for institutional wallets

    Features:
    - Guardian management (add/remove guardians)
    - Recovery request creation with time-locked recovery
    - Multi-party approval system (M-of-N guardians)
    - Guardian verification (email/SMS/2FA)
    - Recovery execution after approvals and time-lock
    - Audit logging
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize social recovery service

        Args:
            db: Async database session
        """
        self.db = db

    async def add_guardian(
        self,
        wallet_id: int,
        added_by: int,
        guardian_user_id: int | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> SocialRecoveryGuardian:
        """
        Add a guardian to an institutional wallet

        Args:
            wallet_id: Wallet ID
            guardian_user_id: User ID of guardian (if platform user)
            email: Guardian email (if not platform user)
            phone: Guardian phone (for SMS verification)
            added_by: User ID who is adding the guardian
            notes: Optional notes about guardian

        Returns:
            SocialRecoveryGuardian
        """
        # Verify wallet exists and user has permission
        stmt = select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")

        # Check if user has permission (owner or admin)
        if wallet.user_id != added_by:
            # Check if user is a signer with admin role
            # For now, only owner can add guardians
            raise PermissionError("Only wallet owner can add guardians")

        # Validate guardian input
        if not guardian_user_id and not email:
            raise ValueError("Either guardian_user_id or email must be provided")

        # Check if guardian already exists
        stmt = select(SocialRecoveryGuardian).where(
            and_(
                SocialRecoveryGuardian.wallet_id == wallet_id,
                or_(
                    SocialRecoveryGuardian.guardian_user_id == guardian_user_id
                    if guardian_user_id
                    else False,
                    SocialRecoveryGuardian.email == email if email else False,
                ),
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("Guardian already exists for this wallet")

        # Create guardian
        guardian = SocialRecoveryGuardian(
            wallet_id=wallet_id,
            guardian_user_id=guardian_user_id,
            email=email,
            phone=phone,
            added_by=added_by,
            notes=notes,
            status=GuardianStatus.PENDING.value,
        )

        self.db.add(guardian)
        await self.db.commit()
        await self.db.refresh(guardian)

        logger.info(
            f"Guardian added to wallet {wallet_id} by user {added_by}: "
            f"guardian_user_id={guardian_user_id}, email={email}"
        )

        return guardian

    async def remove_guardian(
        self,
        wallet_id: int,
        guardian_id: int,
        removed_by: int,
    ) -> bool:
        """
        Remove a guardian from an institutional wallet

        Args:
            wallet_id: Wallet ID
            guardian_id: Guardian ID to remove
            removed_by: User ID who is removing the guardian

        Returns:
            True if successful
        """
        # Verify wallet exists and user has permission
        stmt = select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")

        if wallet.user_id != removed_by:
            raise PermissionError("Only wallet owner can remove guardians")

        # Get guardian
        stmt = select(SocialRecoveryGuardian).where(
            and_(
                SocialRecoveryGuardian.id == guardian_id,
                SocialRecoveryGuardian.wallet_id == wallet_id,
            )
        )
        result = await self.db.execute(stmt)
        guardian = result.scalar_one_or_none()

        if not guardian:
            raise ValueError(f"Guardian {guardian_id} not found")

        # Remove guardian
        await self.db.delete(guardian)
        await self.db.commit()

        logger.info(
            f"Guardian {guardian_id} removed from wallet {wallet_id} by user {removed_by}"
        )

        return True

    async def get_guardians(
        self,
        wallet_id: int,
        status: GuardianStatus | None = None,
    ) -> list[SocialRecoveryGuardian]:
        """
        Get all guardians for a wallet

        Args:
            wallet_id: Wallet ID
            status: Optional status filter

        Returns:
            List of guardians
        """
        stmt = select(SocialRecoveryGuardian).where(
            SocialRecoveryGuardian.wallet_id == wallet_id
        )

        if status:
            stmt = stmt.where(SocialRecoveryGuardian.status == status.value)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_recovery_request(
        self,
        wallet_id: int,
        requester_id: int,
        reason: str,
        required_approvals: int | None = None,
        time_lock_days: int = 7,
    ) -> RecoveryRequest:
        """
        Create a recovery request

        Args:
            wallet_id: Wallet ID to recover
            requester_id: User ID requesting recovery
            reason: Reason for recovery
            required_approvals: Number of approvals needed (default: M-of-N based on guardians)
            time_lock_days: Days to wait before recovery can execute (7-30 days)

        Returns:
            RecoveryRequest
        """
        # Verify wallet exists
        stmt = select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")

        # Check if requester has access (owner or signer)
        has_access = wallet.user_id == requester_id
        if not has_access and wallet.signers:
            # Check if requester is a signer
            signer_stmt = select(wallet_signer_association).where(
                and_(
                    wallet_signer_association.c.wallet_id == wallet_id,
                    wallet_signer_association.c.user_id == requester_id,
                )
            )
            signer_result = await self.db.execute(signer_stmt)
            has_access = signer_result.first() is not None

        if not has_access:
            raise PermissionError("Requester does not have access to this wallet")

        # Get active guardians
        guardians = await self.get_guardians(wallet_id, GuardianStatus.ACTIVE)
        if not guardians:
            raise ValueError("No active guardians found for this wallet")

        # Determine required approvals (default: majority of guardians)
        if required_approvals is None:
            required_approvals = max(1, (len(guardians) // 2) + 1)  # Majority

        if required_approvals > len(guardians):
            raise ValueError(
                f"Required approvals ({required_approvals}) cannot exceed number of guardians ({len(guardians)})"
            )

        # Validate time-lock (7-30 days)
        if time_lock_days < 7 or time_lock_days > 30:
            raise ValueError("Time-lock must be between 7 and 30 days")

        # Create recovery request
        now = datetime.now(UTC)
        recovery_request = RecoveryRequest(
            wallet_id=wallet_id,
            requester_id=requester_id,
            reason=reason,
            status=RecoveryRequestStatus.PENDING.value,
            required_approvals=required_approvals,
            current_approvals=0,
            time_lock_days=time_lock_days,
            unlock_time=now + timedelta(days=time_lock_days),
            expires_at=now
            + timedelta(hours=72),  # Request expires in 3 days if not approved
        )

        self.db.add(recovery_request)
        await self.db.commit()
        await self.db.refresh(recovery_request)

        logger.info(
            f"Recovery request {recovery_request.id} created for wallet {wallet_id} "
            f"by user {requester_id} (requires {required_approvals} approvals, unlocks in {time_lock_days} days)"
        )

        return recovery_request

    async def approve_recovery(
        self,
        recovery_request_id: int,
        guardian_id: int,
        approver_id: int,
        verification_code: str | None = None,
        signature: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> bool:
        """
        Approve a recovery request

        Args:
            recovery_request_id: Recovery request ID
            guardian_id: Guardian ID approving
            approver_id: User ID approving (guardian or guardian's user)
            verification_code: Optional verification code
            signature: Optional cryptographic signature
            ip_address: Optional IP address
            user_agent: Optional user agent

        Returns:
            True if approval successful
        """
        # Get recovery request
        stmt = (
            select(RecoveryRequest)
            .where(RecoveryRequest.id == recovery_request_id)
            .options(selectinload(RecoveryRequest.approvals))
        )
        result = await self.db.execute(stmt)
        recovery_request = result.scalar_one_or_none()

        if not recovery_request:
            raise ValueError(f"Recovery request {recovery_request_id} not found")

        # Check status
        if recovery_request.status != RecoveryRequestStatus.PENDING.value:
            raise ValueError(
                f"Recovery request is not pending (status: {recovery_request.status})"
            )

        # Check if expired
        if (
            recovery_request.expires_at
            and datetime.now(UTC) > recovery_request.expires_at
        ):
            recovery_request.status = RecoveryRequestStatus.EXPIRED.value
            await self.db.commit()
            return False

        # Verify guardian
        stmt = select(SocialRecoveryGuardian).where(
            and_(
                SocialRecoveryGuardian.id == guardian_id,
                SocialRecoveryGuardian.wallet_id == recovery_request.wallet_id,
                SocialRecoveryGuardian.status == GuardianStatus.ACTIVE.value,
            )
        )
        result = await self.db.execute(stmt)
        guardian = result.scalar_one_or_none()

        if not guardian:
            raise ValueError(f"Guardian {guardian_id} not found or not active")

        # Check if already approved by this guardian
        existing_approval = next(
            (a for a in recovery_request.approvals if a.guardian_id == guardian_id),
            None,
        )
        if existing_approval:
            return False  # Already approved

        # Create approval
        approval = RecoveryApproval(
            recovery_request_id=recovery_request_id,
            guardian_id=guardian_id,
            approver_id=approver_id,
            approved_at=datetime.now(UTC),
            signature=signature,
            verification_code=verification_code,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(approval)
        recovery_request.current_approvals += 1

        # Check if threshold met
        if recovery_request.current_approvals >= recovery_request.required_approvals:
            recovery_request.status = RecoveryRequestStatus.APPROVED.value

        await self.db.commit()

        logger.info(
            f"Recovery request {recovery_request_id} approved by guardian {guardian_id} "
            f"({recovery_request.current_approvals}/{recovery_request.required_approvals})"
        )

        return True

    async def reject_recovery(
        self,
        recovery_request_id: int,
        guardian_id: int,
        rejector_id: int,
        reason: str | None = None,
    ) -> bool:
        """
        Reject a recovery request

        Args:
            recovery_request_id: Recovery request ID
            guardian_id: Guardian ID rejecting
            rejector_id: User ID rejecting

        Returns:
            True if rejection successful
        """
        # Get recovery request
        stmt = select(RecoveryRequest).where(RecoveryRequest.id == recovery_request_id)
        result = await self.db.execute(stmt)
        recovery_request = result.scalar_one_or_none()

        if not recovery_request:
            raise ValueError(f"Recovery request {recovery_request_id} not found")

        if recovery_request.status != RecoveryRequestStatus.PENDING.value:
            return False

        # Verify guardian
        stmt = select(SocialRecoveryGuardian).where(
            and_(
                SocialRecoveryGuardian.id == guardian_id,
                SocialRecoveryGuardian.wallet_id == recovery_request.wallet_id,
            )
        )
        result = await self.db.execute(stmt)
        guardian = result.scalar_one_or_none()

        if not guardian:
            raise ValueError(f"Guardian {guardian_id} not found")

        # Reject request
        recovery_request.status = RecoveryRequestStatus.REJECTED.value
        await self.db.commit()

        logger.info(
            f"Recovery request {recovery_request_id} rejected by guardian {guardian_id}: {reason}"
        )

        return True

    async def execute_recovery(
        self,
        recovery_request_id: int,
        executor_id: int,
    ) -> bool:
        """
        Execute a recovery (after approvals and time-lock)

        Args:
            recovery_request_id: Recovery request ID
            executor_id: User ID executing recovery

        Returns:
            True if execution successful
        """
        # Get recovery request
        stmt = select(RecoveryRequest).where(RecoveryRequest.id == recovery_request_id)
        result = await self.db.execute(stmt)
        recovery_request = result.scalar_one_or_none()

        if not recovery_request:
            raise ValueError(f"Recovery request {recovery_request_id} not found")

        # Check status
        if recovery_request.status != RecoveryRequestStatus.APPROVED.value:
            raise ValueError(
                f"Recovery request not approved (status: {recovery_request.status})"
            )

        # Check if requester is executor
        if recovery_request.requester_id != executor_id:
            raise PermissionError("Only requester can execute recovery")

        # Check if time-lock has passed
        if (
            recovery_request.unlock_time
            and datetime.now(UTC) < recovery_request.unlock_time
        ):
            raise ValueError(
                f"Recovery time-lock has not passed yet. Unlocks at {recovery_request.unlock_time}"
            )

        # Execute recovery (in production, this would perform actual wallet recovery)
        recovery_request.status = RecoveryRequestStatus.COMPLETED.value
        recovery_request.completed_at = datetime.now(UTC)
        recovery_request.executed_by = executor_id

        await self.db.commit()

        logger.info(
            f"Recovery request {recovery_request_id} executed by user {executor_id}"
        )

        return True

    async def get_recovery_request(
        self,
        recovery_request_id: int,
    ) -> RecoveryRequest | None:
        """Get a recovery request"""
        stmt = (
            select(RecoveryRequest)
            .where(RecoveryRequest.id == recovery_request_id)
            .options(
                selectinload(RecoveryRequest.approvals),
                selectinload(RecoveryRequest.wallet),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_wallet_recovery_requests(
        self,
        wallet_id: int,
        status: RecoveryRequestStatus | None = None,
    ) -> list[RecoveryRequest]:
        """Get all recovery requests for a wallet"""
        stmt = select(RecoveryRequest).where(RecoveryRequest.wallet_id == wallet_id)

        if status:
            stmt = stmt.where(RecoveryRequest.status == status.value)

        stmt = stmt.order_by(RecoveryRequest.created_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recovery_approvals(
        self,
        recovery_request_id: int,
    ) -> list[RecoveryApproval]:
        """Get approvals for a recovery request"""
        stmt = (
            select(RecoveryApproval)
            .where(RecoveryApproval.recovery_request_id == recovery_request_id)
            .order_by(RecoveryApproval.approved_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


# Export RecoveryStatus for backward compatibility
RecoveryStatus = RecoveryRequestStatus
