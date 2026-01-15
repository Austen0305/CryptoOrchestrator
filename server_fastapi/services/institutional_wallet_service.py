"""
Institutional Wallet Service
Manages multi-signature wallets, team access, and institutional custody features
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, delete, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.institutional_wallet import (
    InstitutionalWallet,
    PendingTransaction,
    SignerRole,
    WalletAccessLog,
    WalletStatus,
    WalletType,
    wallet_signer_association,
)
from ..models.user import User

logger = logging.getLogger(__name__)


class InstitutionalWalletService:
    """Service for managing institutional wallets with multi-signature support"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_institutional_wallet(
        self,
        user_id: int,
        wallet_type: str,
        chain_id: int,
        multisig_type: str | None = None,
        required_signatures: int = 1,
        total_signers: int = 1,
        signer_user_ids: list[int] | None = None,
        label: str | None = None,
        description: str | None = None,
        unlock_time: datetime | None = None,
        config: dict | None = None,
    ) -> InstitutionalWallet:
        """
        Create a new institutional wallet

        Args:
            user_id: Primary owner user ID
            wallet_type: Type of wallet (multisig, timelock, treasury, custodial)
            chain_id: Blockchain ID
            multisig_type: Multi-signature type (2_of_3, 3_of_5, custom)
            required_signatures: M in M-of-N (minimum signatures required)
            total_signers: N in M-of-N (total number of signers)
            signer_user_ids: List of user IDs to add as signers
            label: User-friendly label
            description: Wallet description
            unlock_time: When time-locked wallet unlocks
            config: Additional configuration

        Returns:
            Created InstitutionalWallet instance
        """
        try:
            # Validate multisig configuration
            if wallet_type == WalletType.MULTISIG.value:
                if not multisig_type:
                    raise ValueError(
                        "multisig_type required for multi-signature wallets"
                    )
                if required_signatures < 1 or total_signers < required_signatures:
                    raise ValueError(
                        f"Invalid signature configuration: {required_signatures} of {total_signers}"
                    )

            # Create wallet
            wallet = InstitutionalWallet(
                user_id=user_id,
                wallet_type=wallet_type,
                chain_id=chain_id,
                multisig_type=multisig_type,
                required_signatures=required_signatures,
                total_signers=total_signers,
                label=label,
                description=description,
                unlock_time=unlock_time,
                config=config or {},
                status=WalletStatus.PENDING.value,
            )

            self.db.add(wallet)
            await self.db.flush()  # Get wallet ID

            # Add signers
            if signer_user_ids:
                await self.add_signers(wallet.id, signer_user_ids, user_id)
            else:
                # Add owner as signer by default
                await self.add_signer(
                    wallet.id, user_id, SignerRole.OWNER.value, user_id
                )

            # Log access
            await self.log_access(
                wallet.id,
                user_id,
                "create",
                "wallet",
                wallet.id,
                success=True,
            )

            await self.db.commit()
            await self.db.refresh(wallet)

            logger.info(
                f"Created institutional wallet {wallet.id} for user {user_id}",
                extra={
                    "wallet_id": wallet.id,
                    "user_id": user_id,
                    "wallet_type": wallet_type,
                },
            )

            return wallet

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating institutional wallet: {e}", exc_info=True)
            raise

    async def add_signer(
        self,
        wallet_id: int,
        signer_user_id: int,
        role: str = SignerRole.SIGNER.value,
        added_by_user_id: int = None,
    ) -> bool:
        """
        Add a signer to an institutional wallet

        Args:
            wallet_id: Wallet ID
            signer_user_id: User ID to add as signer
            role: Signer role (owner, signer, viewer, admin)
            added_by_user_id: User ID who is adding the signer

        Returns:
            True if successful
        """
        try:
            # Get wallet
            result = await self.db.execute(
                select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found")

            # Check permissions (owner or admin can add signers)
            if added_by_user_id and added_by_user_id != wallet.user_id:
                # Check if user is admin
                # For now, only owner can add signers
                raise PermissionError("Only wallet owner can add signers")

            # Get signer user
            result = await self.db.execute(
                select(User).where(User.id == signer_user_id)
            )
            signer = result.scalar_one_or_none()

            if not signer:
                raise ValueError(f"User {signer_user_id} not found")

            # Check if already a signer (query the association table)
            from sqlalchemy import text

            existing_result = await self.db.execute(
                text(
                    "SELECT 1 FROM wallet_signer_associations WHERE wallet_id = :wallet_id AND user_id = :user_id"
                ),
                {"wallet_id": wallet_id, "user_id": signer_user_id},
            )
            if existing_result.scalar_one_or_none():
                logger.warning(
                    f"User {signer_user_id} already a signer of wallet {wallet_id}"
                )
                return False

            # Add signer association
            stmt = insert(wallet_signer_association).values(
                wallet_id=wallet_id,
                user_id=signer_user_id,
                role=role,
            )
            await self.db.execute(stmt)

            # Update total signers count
            wallet.total_signers += 1

            # Log access
            await self.log_access(
                wallet_id,
                added_by_user_id or wallet.user_id,
                "add_signer",
                "signer",
                signer_user_id,
                success=True,
            )

            await self.db.commit()

            logger.info(
                f"Added signer {signer_user_id} to wallet {wallet_id}",
                extra={"wallet_id": wallet_id, "signer_user_id": signer_user_id},
            )

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error adding signer: {e}", exc_info=True)
            raise

    async def add_signers(
        self,
        wallet_id: int,
        signer_user_ids: list[int],
        added_by_user_id: int,
        role: str = SignerRole.SIGNER.value,
    ) -> int:
        """
        Add multiple signers to a wallet

        Returns:
            Number of signers added
        """
        added_count = 0
        for signer_id in signer_user_ids:
            try:
                await self.add_signer(wallet_id, signer_id, role, added_by_user_id)
                added_count += 1
            except Exception as e:
                logger.warning(f"Failed to add signer {signer_id}: {e}")
                continue

        return added_count

    async def remove_signer(
        self,
        wallet_id: int,
        signer_user_id: int,
        removed_by_user_id: int,
    ) -> bool:
        """
        Remove a signer from a wallet

        Returns:
            True if successful
        """
        try:
            # Get wallet
            result = await self.db.execute(
                select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found")

            # Check permissions
            if removed_by_user_id != wallet.user_id:
                raise PermissionError("Only wallet owner can remove signers")

            # Don't allow removing the owner
            if signer_user_id == wallet.user_id:
                raise ValueError("Cannot remove wallet owner")

            # Remove signer association
            stmt = delete(wallet_signer_association).where(
                and_(
                    wallet_signer_association.c.wallet_id == wallet_id,
                    wallet_signer_association.c.user_id == signer_user_id,
                )
            )
            await self.db.execute(stmt)

            # Update total signers count
            wallet.total_signers = max(1, wallet.total_signers - 1)

            # Log access
            await self.log_access(
                wallet_id,
                removed_by_user_id,
                "remove_signer",
                "signer",
                signer_user_id,
                success=True,
            )

            await self.db.commit()

            logger.info(
                f"Removed signer {signer_user_id} from wallet {wallet_id}",
                extra={"wallet_id": wallet_id, "signer_user_id": signer_user_id},
            )

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing signer: {e}", exc_info=True)
            raise

    async def create_pending_transaction(
        self,
        wallet_id: int,
        transaction_type: str,
        transaction_data: dict,
        created_by_user_id: int,
        description: str | None = None,
        expires_in_hours: int = 24,
    ) -> PendingTransaction:
        """
        Create a pending transaction requiring signatures

        Args:
            wallet_id: Wallet ID
            transaction_type: Type of transaction
            transaction_data: Full transaction data
            created_by_user_id: User creating the transaction
            description: Transaction description
            expires_in_hours: Hours until transaction expires

        Returns:
            Created PendingTransaction
        """
        try:
            # Get wallet
            result = await self.db.execute(
                select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found")

            # Check permissions
            if not await self.has_permission(wallet_id, created_by_user_id, "sign"):
                raise PermissionError(
                    "User does not have permission to create transactions"
                )

            # Create pending transaction
            pending_tx = PendingTransaction(
                wallet_id=wallet_id,
                transaction_type=transaction_type,
                to_address=transaction_data.get("to"),
                amount=transaction_data.get("value"),
                currency=transaction_data.get("currency", "ETH"),
                chain_id=transaction_data.get("chain_id", wallet.chain_id),
                transaction_data=transaction_data,
                required_signatures=wallet.required_signatures,
                description=description,
                expires_at=datetime.now(UTC) + timedelta(hours=expires_in_hours),
                status="pending",
            )

            self.db.add(pending_tx)
            await self.db.commit()
            await self.db.refresh(pending_tx)

            # Log access
            await self.log_access(
                wallet_id,
                created_by_user_id,
                "create_transaction",
                "transaction",
                pending_tx.id,
                success=True,
            )

            logger.info(
                f"Created pending transaction {pending_tx.id} for wallet {wallet_id}",
                extra={"wallet_id": wallet_id, "transaction_id": pending_tx.id},
            )

            return pending_tx

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating pending transaction: {e}", exc_info=True)
            raise

    async def sign_transaction(
        self,
        transaction_id: int,
        user_id: int,
        signature_data: dict,
    ) -> bool:
        """
        Sign a pending transaction

        Args:
            transaction_id: Pending transaction ID
            user_id: User signing the transaction
            signature_data: Signature data (signature, message hash, etc.)

        Returns:
            True if transaction is now fully signed and ready to execute
        """
        try:
            # Get transaction
            result = await self.db.execute(
                select(PendingTransaction)
                .where(PendingTransaction.id == transaction_id)
                .options(selectinload(PendingTransaction.wallet))
            )
            pending_tx = result.scalar_one_or_none()

            if not pending_tx:
                raise ValueError(f"Transaction {transaction_id} not found")

            # Check if expired
            if pending_tx.expires_at and pending_tx.expires_at < datetime.now(UTC):
                pending_tx.status = "expired"
                await self.db.commit()
                raise ValueError("Transaction has expired")

            # Check permissions
            if not await self.has_permission(pending_tx.wallet_id, user_id, "sign"):
                raise PermissionError(
                    "User does not have permission to sign transactions"
                )

            # Check if already signed by this user
            if str(user_id) in pending_tx.signatures:
                logger.warning(
                    f"User {user_id} already signed transaction {transaction_id}"
                )
                return False

            # Add signature
            pending_tx.signatures[str(user_id)] = signature_data

            # Check if we have enough signatures
            signature_count = len(pending_tx.signatures)
            if signature_count >= pending_tx.required_signatures:
                pending_tx.status = "signed"
                logger.info(
                    f"Transaction {transaction_id} fully signed ({signature_count}/{pending_tx.required_signatures})"
                )
            else:
                logger.info(
                    f"Transaction {transaction_id} partially signed ({signature_count}/{pending_tx.required_signatures})"
                )

            # Log access
            await self.log_access(
                pending_tx.wallet_id,
                user_id,
                "sign_transaction",
                "transaction",
                transaction_id,
                success=True,
            )

            await self.db.commit()

            return pending_tx.status == "signed"

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error signing transaction: {e}", exc_info=True)
            raise

    async def has_permission(
        self,
        wallet_id: int,
        user_id: int,
        permission: str,
    ) -> bool:
        """
        Check if user has permission on a wallet

        Args:
            wallet_id: Wallet ID
            user_id: User ID
            permission: Permission to check ("view", "sign", "execute", "admin")

        Returns:
            True if user has permission
        """
        try:
            # Get wallet
            result = await self.db.execute(
                select(InstitutionalWallet).where(InstitutionalWallet.id == wallet_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                return False

            # Owner has all permissions
            if wallet.user_id == user_id:
                return True

            # Check signer role (query the association table)
            from sqlalchemy import text

            role_result = await self.db.execute(
                text(
                    "SELECT role FROM wallet_signer_associations WHERE wallet_id = :wallet_id AND user_id = :user_id"
                ),
                {"wallet_id": wallet_id, "user_id": user_id},
            )
            role_row = role_result.first()

            if not role_row:
                return False

            role = role_row[0]

            # Permission mapping
            if permission == "view":
                return role in [
                    SignerRole.OWNER.value,
                    SignerRole.SIGNER.value,
                    SignerRole.VIEWER.value,
                    SignerRole.ADMIN.value,
                ]
            elif permission == "sign":
                return role in [
                    SignerRole.OWNER.value,
                    SignerRole.SIGNER.value,
                    SignerRole.ADMIN.value,
                ]
            elif permission == "execute" or permission == "admin":
                return role in [SignerRole.OWNER.value, SignerRole.ADMIN.value]

            return False

        except Exception as e:
            logger.error(f"Error checking permissions: {e}", exc_info=True)
            return False

    async def get_wallet(
        self,
        wallet_id: int,
        user_id: int,
    ) -> InstitutionalWallet | None:
        """
        Get wallet with permission check

        Returns:
            Wallet if user has view permission, None otherwise
        """
        if not await self.has_permission(wallet_id, user_id, "view"):
            return None

        result = await self.db.execute(
            select(InstitutionalWallet)
            .where(InstitutionalWallet.id == wallet_id)
            .options(
                selectinload(InstitutionalWallet.signers),
                selectinload(InstitutionalWallet.transactions),
                selectinload(InstitutionalWallet.pending_transactions),
            )
        )
        return result.scalar_one_or_none()

    async def list_wallets(
        self,
        user_id: int,
        wallet_type: str | None = None,
        status: str | None = None,
    ) -> list[InstitutionalWallet]:
        """
        List wallets accessible by user

        Returns:
            List of wallets user has access to
        """
        # Get wallets where user is owner or signer
        from sqlalchemy import text

        # First get wallet IDs where user is a signer
        signer_result = await self.db.execute(
            text(
                "SELECT wallet_id FROM wallet_signer_associations WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        )
        signer_wallet_ids = [row[0] for row in signer_result.fetchall()]

        # Query wallets where user is owner or signer
        query = select(InstitutionalWallet).where(
            or_(
                InstitutionalWallet.user_id == user_id,
                InstitutionalWallet.id.in_(signer_wallet_ids)
                if signer_wallet_ids
                else False,
            )
        )

        if wallet_type:
            query = query.where(InstitutionalWallet.wallet_type == wallet_type)

        if status:
            query = query.where(InstitutionalWallet.status == status)

        result = await self.db.execute(
            query.options(
                selectinload(InstitutionalWallet.signers),
            )
        )
        return list(result.scalars().all())

    async def log_access(
        self,
        wallet_id: int,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        success: bool = True,
        error_message: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> WalletAccessLog:
        """
        Log wallet access for audit trail

        Returns:
            Created WalletAccessLog
        """
        log = WalletAccessLog(
            wallet_id=wallet_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )

        self.db.add(log)
        await self.db.flush()

        return log

    async def export_audit_logs(
        self,
        wallet_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: int | None = None,
    ) -> list[WalletAccessLog]:
        """
        Export audit logs for compliance

        Returns:
            List of access logs
        """
        query = select(WalletAccessLog).where(WalletAccessLog.wallet_id == wallet_id)

        if start_date:
            query = query.where(WalletAccessLog.created_at >= start_date)

        if end_date:
            query = query.where(WalletAccessLog.created_at <= end_date)

        if user_id:
            query = query.where(WalletAccessLog.user_id == user_id)

        query = query.order_by(WalletAccessLog.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
