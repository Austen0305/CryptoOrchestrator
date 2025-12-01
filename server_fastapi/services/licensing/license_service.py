"""
License Service - License key generation and validation
"""
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from enum import Enum
import logging
import os
import hashlib
import hmac
import base64
import secrets
import json

logger = logging.getLogger(__name__)


class LicenseType(str, Enum):
    """License types"""
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseStatus(BaseModel):
    """License status"""
    valid: bool
    license_type: str
    expires_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    max_bots: int = 1
    features: List[str] = []
    message: Optional[str] = None


class LicenseKey(BaseModel):
    """License key information"""
    license_key: str
    license_type: str
    user_id: str
    expires_at: Optional[datetime] = None
    max_bots: int = 1
    features: List[str] = []
    created_at: datetime
    activated_at: Optional[datetime] = None
    machine_id: Optional[str] = None


class LicenseService:
    """Service for license key generation and validation"""
    
    # License configuration
    LICENSE_CONFIG = {
        LicenseType.TRIAL: {
            'duration_days': 14,
            'max_bots': 3,
            'features': ['paper_trading', 'basic_strategies']
        },
        LicenseType.BASIC: {
            'duration_days': None,  # No expiration
            'max_bots': 10,
            'features': ['paper_trading', 'live_trading', 'basic_strategies', 'basic_ml']
        },
        LicenseType.PRO: {
            'duration_days': None,
            'max_bots': 100,
            'features': ['paper_trading', 'live_trading', 'all_strategies', 'advanced_ml', 'api_access']
        },
        LicenseType.ENTERPRISE: {
            'duration_days': None,
            'max_bots': -1,  # Unlimited
            'features': ['paper_trading', 'live_trading', 'all_strategies', 'advanced_ml', 'api_access', 'priority_support', 'custom_integrations']
        }
    }
    
    def __init__(self, secret_key: Optional[str] = None):
        # Use secret key from environment or generate one
        self.secret_key = secret_key or os.getenv("LICENSE_SECRET_KEY", secrets.token_hex(32))
        logger.info("License service initialized")
    
    def generate_license_key(
        self,
        user_id: str,
        license_type: str,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Generate a license key"""
        try:
            # Get license configuration
            config = self.LICENSE_CONFIG.get(license_type, self.LICENSE_CONFIG[LicenseType.TRIAL])
            
            # Set expiration date
            if expires_at is None and config['duration_days']:
                expires_at = datetime.utcnow() + timedelta(days=config['duration_days'])
            
            # Create license data
            license_data = {
                'user_id': user_id,
                'license_type': license_type,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'created_at': datetime.utcnow().isoformat(),
                'max_bots': config['max_bots'],
                'features': config['features']
            }
            
            # Encode license data
            data_json = json.dumps(license_data, sort_keys=True)
            data_encoded = base64.b64encode(data_json.encode()).decode()
            
            # Create signature
            signature = hmac.new(
                self.secret_key.encode(),
                data_encoded.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Combine data and signature
            license_key = f"{data_encoded}.{signature}"
            
            # Format as readable license key (XXXX-XXXX-XXXX-...)
            # Group every 4 characters with hyphens for readability
            formatted_key = '-'.join([license_key[i:i+4] for i in range(0, len(license_key), 4)])
            
            logger.info(f"Generated license key for user {user_id}, type {license_type}")
            return formatted_key
        
        except Exception as e:
            logger.error(f"Failed to generate license key: {e}")
            raise
    
    def parse_license_key(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Parse and validate license key"""
        try:
            # Remove formatting
            clean_key = license_key.replace('-', '')
            
            # Split data and signature
            if '.' not in clean_key:
                return None
            
            data_encoded, signature = clean_key.rsplit('.', 1)
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                data_encoded.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid license key signature")
                return None
            
            # Decode license data
            data_json = base64.b64decode(data_encoded.encode()).decode()
            license_data = json.loads(data_json)
            
            return license_data
        
        except Exception as e:
            logger.error(f"Failed to parse license key: {e}")
            return None
    
    def validate_license_key(self, license_key: str, machine_id: Optional[str] = None) -> LicenseStatus:
        """Validate a license key"""
        try:
            # Parse license key
            license_data = self.parse_license_key(license_key)
            
            if not license_data:
                return LicenseStatus(
                    valid=False,
                    license_type='invalid',
                    message='Invalid license key format'
                )
            
            # Check expiration
            expires_at = None
            if license_data.get('expires_at'):
                expires_at = datetime.fromisoformat(license_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    return LicenseStatus(
                        valid=False,
                        license_type=license_data.get('license_type', 'expired'),
                        expires_at=expires_at,
                        message='License has expired'
                    )
            
            # Get license config
            license_type = license_data.get('license_type', LicenseType.TRIAL)
            config = self.LICENSE_CONFIG.get(license_type, self.LICENSE_CONFIG[LicenseType.TRIAL])
            
            return LicenseStatus(
                valid=True,
                license_type=license_type,
                expires_at=expires_at,
                activated_at=datetime.fromisoformat(license_data.get('activated_at', datetime.utcnow().isoformat())) if license_data.get('activated_at') else None,
                max_bots=license_data.get('max_bots', config['max_bots']),
                features=license_data.get('features', config['features']),
                message='License is valid'
            )
        
        except Exception as e:
            logger.error(f"License validation error: {e}")
            return LicenseStatus(
                valid=False,
                license_type='error',
                message=f'Validation error: {str(e)}'
            )
    
    def get_machine_id(self) -> str:
        """Generate a machine ID for license binding"""
        import platform
        import socket
        
        try:
            # Get machine identifiers
            hostname = socket.gethostname()
            
            # Get MAC address (simplified approach)
            try:
                ip = socket.gethostbyname(hostname)
                mac_bytes = ip.encode()[-6:] if len(ip.encode()) >= 6 else b'00' * 6
            except:
                mac_bytes = b'00' * 6
            
            mac_address = ':'.join(['{:02x}'.format(mac_bytes[i]) for i in range(min(6, len(mac_bytes)))])
            
            # Create unique machine ID
            machine_string = f"{platform.system()}_{hostname}_{mac_address}"
            machine_id = hashlib.sha256(machine_string.encode()).hexdigest()[:16]
            
            return machine_id
        except Exception as e:
            logger.error(f"Failed to generate machine ID: {e}")
            return secrets.token_hex(8)
    
    def bind_license_to_machine(self, license_key: str, machine_id: str) -> bool:
        """Bind license to a specific machine"""
        # In production, this would update the license in the database
        # For now, just validate that the license can be parsed
        license_data = self.parse_license_key(license_key)
        return license_data is not None


# Global service instance
license_service = LicenseService()
