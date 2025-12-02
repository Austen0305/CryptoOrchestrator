"""
Withdrawal Address Whitelist Service
Manages withdrawal address whitelists for enhanced security
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...models.base import User
from ...database import get_db_context

logger = logging.getLogger(__name__)


class WithdrawalWhitelistService:
    """Service for managing withdrawal address whitelists"""
    
    def __init__(self):
        self.cooldown_hours = 24  # 24 hour cooldown after adding address
    
    async def add_withdrawal_address(
        self,
        user_id: int,
        address: str,
        currency: str,
        label: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Add withdrawal address to user's whitelist
        
        Args:
            user_id: User ID
            address: Withdrawal address (crypto address, bank account, etc.)
            currency: Currency code (BTC, ETH, USD, etc.)
            label: Optional label for the address
            db: Database session
        
        Returns:
            Dict with operation result
        """
        try:
            # Validate address format (basic check)
            if not address or len(address) < 10:
                return {
                    "success": False,
                    "error": "Invalid address format"
                }
            
            if db is None:
                async with get_db_context() as session:
                    return await self._add_address_internal(user_id, address, currency, label, session)
            else:
                return await self._add_address_internal(user_id, address, currency, label, db)
        except Exception as e:
            logger.error(f"Error adding withdrawal address: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _add_address_internal(
        self,
        user_id: int,
        address: str,
        currency: str,
        label: Optional[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Internal address addition logic"""
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Get existing whitelist from user preferences
        from ..repositories.preferences_repository import preferences_repository
        
        prefs = await preferences_repository.get_by_user_id(db, user_id)
        
        import json
        if prefs and prefs.data_json:
            try:
                data = json.loads(prefs.data_json)
            except:
                data = {}
        else:
            data = {}
        
        # Initialize withdrawal whitelist if not exists
        if "withdrawal_whitelist" not in data:
            data["withdrawal_whitelist"] = []
        
        # Check if address already whitelisted
        existing = next(
            (addr for addr in data["withdrawal_whitelist"]
             if addr["address"] == address and addr["currency"] == currency),
            None
        )
        
        if existing:
            return {
                "success": False,
                "error": "Address already whitelisted for this currency"
            }
        
        # Add address to whitelist (with cooldown period)
        cooldown_until = datetime.utcnow() + timedelta(hours=self.cooldown_hours)
        
        data["withdrawal_whitelist"].append({
            "address": address,
            "currency": currency,
            "label": label or f"{currency} Address",
            "added_at": datetime.utcnow().isoformat(),
            "cooldown_until": cooldown_until.isoformat(),
            "active": False  # Not active until cooldown expires
        })
        
        # Update preferences
        await preferences_repository.upsert_for_user(
            db,
            user_id,
            data_json=json.dumps(data)
        )
        
        await db.commit()
        
        logger.info(
            f"✅ Withdrawal address {address} ({currency}) added to whitelist for user {user_id}. "
            f"Cooldown until {cooldown_until.isoformat()}"
        )
        
        return {
            "success": True,
            "address": address,
            "currency": currency,
            "label": label,
            "cooldown_until": cooldown_until.isoformat(),
            "message": f"Address added. Will be active after {self.cooldown_hours} hour cooldown period."
        }
    
    async def remove_withdrawal_address(
        self,
        user_id: int,
        address: str,
        currency: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Remove withdrawal address from user's whitelist"""
        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._remove_address_internal(user_id, address, currency, session)
            else:
                return await self._remove_address_internal(user_id, address, currency, db)
        except Exception as e:
            logger.error(f"Error removing withdrawal address: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _remove_address_internal(
        self,
        user_id: int,
        address: str,
        currency: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Internal address removal logic"""
        from ..repositories.preferences_repository import preferences_repository
        
        prefs = await preferences_repository.get_by_user_id(db, user_id)
        
        if not prefs or not prefs.data_json:
            return {
                "success": False,
                "error": "No whitelist found"
            }
        
        import json
        try:
            data = json.loads(prefs.data_json)
        except:
            return {
                "success": False,
                "error": "Invalid preferences data"
            }
        
        if "withdrawal_whitelist" not in data:
            return {
                "success": False,
                "error": "No whitelist found"
            }
        
        # Remove address from whitelist
        original_count = len(data["withdrawal_whitelist"])
        data["withdrawal_whitelist"] = [
            addr for addr in data["withdrawal_whitelist"]
            if not (addr["address"] == address and addr["currency"] == currency)
        ]
        
        if len(data["withdrawal_whitelist"]) == original_count:
            return {
                "success": False,
                "error": "Address not found in whitelist"
            }
        
        # Update preferences
        await preferences_repository.upsert_for_user(
            db,
            user_id,
            data_json=json.dumps(data)
        )
        
        await db.commit()
        
        logger.info(f"✅ Withdrawal address {address} ({currency}) removed from whitelist for user {user_id}")
        
        return {
            "success": True,
            "address": address,
            "currency": currency,
            "message": "Address removed from whitelist"
        }
    
    async def get_whitelist(
        self,
        user_id: int,
        currency: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Get user's withdrawal address whitelist"""
        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._get_whitelist_internal(user_id, currency, session)
            else:
                return await self._get_whitelist_internal(user_id, currency, db)
        except Exception as e:
            logger.error(f"Error getting withdrawal whitelist: {e}", exc_info=True)
            return []
    
    async def _get_whitelist_internal(
        self,
        user_id: int,
        currency: Optional[str],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Internal whitelist retrieval"""
        from ..repositories.preferences_repository import preferences_repository
        
        prefs = await preferences_repository.get_by_user_id(db, user_id)
        
        if not prefs or not prefs.data_json:
            return []
        
        import json
        try:
            data = json.loads(prefs.data_json)
            whitelist = data.get("withdrawal_whitelist", [])
            
            # Filter by currency if specified
            if currency:
                whitelist = [addr for addr in whitelist if addr["currency"] == currency]
            
            # Check cooldown status
            now = datetime.utcnow()
            for addr in whitelist:
                cooldown_until = datetime.fromisoformat(addr.get("cooldown_until", "1970-01-01"))
                addr["active"] = now >= cooldown_until
                addr["cooldown_expires_at"] = addr.get("cooldown_until")
            
            return whitelist
        except Exception as e:
            logger.error(f"Error parsing withdrawal whitelist: {e}")
            return []
    
    async def is_address_whitelisted(
        self,
        user_id: int,
        address: str,
        currency: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Check if withdrawal address is whitelisted and active"""
        try:
            whitelist = await self.get_whitelist(user_id, currency, db)
            
            for addr in whitelist:
                if addr["address"] == address and addr["currency"] == currency:
                    # Check if cooldown has expired
                    cooldown_until = datetime.fromisoformat(addr.get("cooldown_until", "1970-01-01"))
                    return datetime.utcnow() >= cooldown_until
            
            return False
        except Exception as e:
            logger.error(f"Error checking withdrawal whitelist: {e}")
            return False


# Global instance
withdrawal_whitelist_service = WithdrawalWhitelistService()

