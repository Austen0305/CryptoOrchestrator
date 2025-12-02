"""
IP Whitelisting Service
Manages IP whitelists for enhanced security
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from ipaddress import ip_address, IPv4Address, IPv6Address

from ...models.base import User
from ...database import get_db_context

logger = logging.getLogger(__name__)


class IPWhitelistService:
    """Service for managing IP whitelists"""
    
    async def add_ip_to_whitelist(
        self,
        user_id: int,
        ip_address_str: str,
        label: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Add IP address to user's whitelist
        
        Args:
            user_id: User ID
            ip_address_str: IP address to whitelist
            label: Optional label for the IP
            db: Database session
        
        Returns:
            Dict with operation result
        """
        try:
            # Validate IP address
            try:
                ip = ip_address(ip_address_str)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid IP address: {ip_address_str}"
                }
            
            if db is None:
                async with get_db_context() as session:
                    return await self._add_ip_internal(user_id, ip_address_str, label, session)
            else:
                return await self._add_ip_internal(user_id, ip_address_str, label, db)
        except Exception as e:
            logger.error(f"Error adding IP to whitelist: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _add_ip_internal(
        self,
        user_id: int,
        ip_address_str: str,
        label: Optional[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Internal IP addition logic"""
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Get existing whitelist from user preferences or create new
        # For now, store in user preferences JSON
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
        
        # Initialize IP whitelist if not exists
        if "ip_whitelist" not in data:
            data["ip_whitelist"] = []
        
        # Check if IP already whitelisted
        if ip_address_str in [ip["address"] for ip in data["ip_whitelist"]]:
            return {
                "success": False,
                "error": "IP address already whitelisted"
            }
        
        # Add IP to whitelist
        data["ip_whitelist"].append({
            "address": ip_address_str,
            "label": label or f"IP {ip_address_str}",
            "added_at": datetime.utcnow().isoformat()
        })
        
        # Update preferences
        await preferences_repository.upsert_for_user(
            db,
            user_id,
            data_json=json.dumps(data)
        )
        
        await db.commit()
        
        logger.info(f"✅ IP {ip_address_str} added to whitelist for user {user_id}")
        
        return {
            "success": True,
            "ip_address": ip_address_str,
            "label": label,
            "message": "IP address added to whitelist"
        }
    
    async def remove_ip_from_whitelist(
        self,
        user_id: int,
        ip_address_str: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Remove IP address from user's whitelist"""
        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._remove_ip_internal(user_id, ip_address_str, session)
            else:
                return await self._remove_ip_internal(user_id, ip_address_str, db)
        except Exception as e:
            logger.error(f"Error removing IP from whitelist: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _remove_ip_internal(
        self,
        user_id: int,
        ip_address_str: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Internal IP removal logic"""
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
        
        if "ip_whitelist" not in data:
            return {
                "success": False,
                "error": "No whitelist found"
            }
        
        # Remove IP from whitelist
        original_count = len(data["ip_whitelist"])
        data["ip_whitelist"] = [
            ip for ip in data["ip_whitelist"]
            if ip["address"] != ip_address_str
        ]
        
        if len(data["ip_whitelist"]) == original_count:
            return {
                "success": False,
                "error": "IP address not found in whitelist"
            }
        
        # Update preferences
        await preferences_repository.upsert_for_user(
            db,
            user_id,
            data_json=json.dumps(data)
        )
        
        await db.commit()
        
        logger.info(f"✅ IP {ip_address_str} removed from whitelist for user {user_id}")
        
        return {
            "success": True,
            "ip_address": ip_address_str,
            "message": "IP address removed from whitelist"
        }
    
    async def get_whitelist(
        self,
        user_id: int,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Get user's IP whitelist"""
        try:
            if db is None:
                async with get_db_context() as session:
                    return await self._get_whitelist_internal(user_id, session)
            else:
                return await self._get_whitelist_internal(user_id, db)
        except Exception as e:
            logger.error(f"Error getting whitelist: {e}", exc_info=True)
            return []
    
    async def _get_whitelist_internal(
        self,
        user_id: int,
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
            return data.get("ip_whitelist", [])
        except:
            return []
    
    async def is_ip_whitelisted(
        self,
        user_id: int,
        ip_address_str: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """Check if IP address is whitelisted for user"""
        try:
            whitelist = await self.get_whitelist(user_id, db)
            return ip_address_str in [ip["address"] for ip in whitelist]
        except Exception as e:
            logger.error(f"Error checking IP whitelist: {e}")
            return False


# Global instance
ip_whitelist_service = IPWhitelistService()

