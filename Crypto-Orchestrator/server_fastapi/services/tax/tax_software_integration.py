"""
Tax Software Integration Service
Integration with TaxAct, TurboTax, and other tax software
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaxSoftware(str, Enum):
    """Supported tax software"""
    TAXACT = "taxact"
    TURBOTAX = "turbotax"
    HR_BLOCK = "hr_block"
    TAXSLY = "taxsly"
    FREETAXUSA = "freetaxusa"


@dataclass
class TaxSoftwareExport:
    """Tax software export"""
    export_id: str
    user_id: int
    tax_year: int
    software: TaxSoftware
    format: str  # "csv", "xml", "json", "iif"
    file_path: Optional[str] = None
    exported_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending", "completed", "failed"


@dataclass
class TaxSoftwareCredentials:
    """Tax software API credentials"""
    software: TaxSoftware
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class TaxSoftwareIntegrationService:
    """
    Tax software integration service
    
    Features:
    - TaxAct integration
    - TurboTax integration
    - H&R Block integration
    - Generic tax software export
    - API credential management
    - Automated tax data upload
    
    Note: This is a foundation that can be extended with actual tax software APIs.
    Most tax software providers have APIs for importing tax data.
    """
    
    def __init__(self):
        self.exports: Dict[str, TaxSoftwareExport] = {}
        self.credentials: Dict[int, Dict[TaxSoftware, TaxSoftwareCredentials]] = {}  # user_id -> software -> creds
        self.enabled = True
    
    def export_to_taxact(
        self,
        user_id: int,
        tax_year: int,
        tax_data: Dict[str, Any],
    ) -> TaxSoftwareExport:
        """
        Export tax data to TaxAct
        
        Args:
            user_id: User ID
            tax_year: Tax year
            tax_data: Tax data dictionary
        
        Returns:
            TaxSoftwareExport
        
        Note: TaxAct supports CSV and XML import formats.
        In production, this would:
        1. Format data according to TaxAct schema
        2. Generate CSV/XML file
        3. Upload via TaxAct API (if available)
        4. Or provide download link
        """
        export_id = f"taxact_{user_id}_{tax_year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Format data for TaxAct (simplified)
        formatted_data = self._format_for_taxact(tax_data)
        
        export = TaxSoftwareExport(
            export_id=export_id,
            user_id=user_id,
            tax_year=tax_year,
            software=TaxSoftware.TAXACT,
            format="csv",
            status="completed",
        )
        
        self.exports[export_id] = export
        
        logger.info(f"Exported tax data to TaxAct for user {user_id}, year {tax_year}")
        
        return export
    
    def export_to_turbotax(
        self,
        user_id: int,
        tax_year: int,
        tax_data: Dict[str, Any],
    ) -> TaxSoftwareExport:
        """
        Export tax data to TurboTax
        
        Args:
            user_id: User ID
            tax_year: Tax year
            tax_data: Tax data dictionary
        
        Returns:
            TaxSoftwareExport
        
        Note: TurboTax supports CSV and TXF (Tax Exchange Format) import.
        In production, this would:
        1. Format data according to TurboTax schema
        2. Generate CSV/TXF file
        3. Upload via TurboTax API (if available)
        4. Or provide download link
        """
        export_id = f"turbotax_{user_id}_{tax_year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Format data for TurboTax (simplified)
        formatted_data = self._format_for_turbotax(tax_data)
        
        export = TaxSoftwareExport(
            export_id=export_id,
            user_id=user_id,
            tax_year=tax_year,
            software=TaxSoftware.TURBOTAX,
            format="csv",
            status="completed",
        )
        
        self.exports[export_id] = export
        
        logger.info(f"Exported tax data to TurboTax for user {user_id}, year {tax_year}")
        
        return export
    
    def export_to_hr_block(
        self,
        user_id: int,
        tax_year: int,
        tax_data: Dict[str, Any],
    ) -> TaxSoftwareExport:
        """
        Export tax data to H&R Block
        
        Args:
            user_id: User ID
            tax_year: Tax year
            tax_data: Tax data dictionary
        
        Returns:
            TaxSoftwareExport
        """
        export_id = f"hrblock_{user_id}_{tax_year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        formatted_data = self._format_for_hr_block(tax_data)
        
        export = TaxSoftwareExport(
            export_id=export_id,
            user_id=user_id,
            tax_year=tax_year,
            software=TaxSoftware.HR_BLOCK,
            format="csv",
            status="completed",
        )
        
        self.exports[export_id] = export
        
        logger.info(f"Exported tax data to H&R Block for user {user_id}, year {tax_year}")
        
        return export
    
    def export_generic(
        self,
        user_id: int,
        tax_year: int,
        tax_data: Dict[str, Any],
        format: str = "csv",
    ) -> TaxSoftwareExport:
        """
        Export tax data in generic format
        
        Args:
            user_id: User ID
            tax_year: Tax year
            tax_data: Tax data dictionary
            format: Export format (csv, json, xml)
        
        Returns:
            TaxSoftwareExport
        """
        export_id = f"generic_{user_id}_{tax_year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        export = TaxSoftwareExport(
            export_id=export_id,
            user_id=user_id,
            tax_year=tax_year,
            software=TaxSoftware.TAXACT,  # Placeholder
            format=format,
            status="completed",
        )
        
        self.exports[export_id] = export
        
        logger.info(f"Exported tax data in {format} format for user {user_id}, year {tax_year}")
        
        return export
    
    def store_credentials(
        self,
        user_id: int,
        software: TaxSoftware,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        """Store tax software API credentials"""
        if user_id not in self.credentials:
            self.credentials[user_id] = {}
        
        creds = TaxSoftwareCredentials(
            software=software,
            api_key=api_key,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        
        self.credentials[user_id][software] = creds
        
        logger.info(f"Stored credentials for {software.value} for user {user_id}")
    
    def get_credentials(
        self,
        user_id: int,
        software: TaxSoftware,
    ) -> Optional[TaxSoftwareCredentials]:
        """Get tax software credentials"""
        return self.credentials.get(user_id, {}).get(software)
    
    def _format_for_taxact(self, tax_data: Dict[str, Any]) -> str:
        """Format tax data for TaxAct CSV format"""
        # In production, format according to TaxAct CSV schema
        # This is a placeholder
        return json.dumps(tax_data)
    
    def _format_for_turbotax(self, tax_data: Dict[str, Any]) -> str:
        """Format tax data for TurboTax CSV/TXF format"""
        # In production, format according to TurboTax schema
        # This is a placeholder
        return json.dumps(tax_data)
    
    def _format_for_hr_block(self, tax_data: Dict[str, Any]) -> str:
        """Format tax data for H&R Block CSV format"""
        # In production, format according to H&R Block schema
        # This is a placeholder
        return json.dumps(tax_data)
    
    def get_export(self, export_id: str) -> Optional[TaxSoftwareExport]:
        """Get export by ID"""
        return self.exports.get(export_id)
    
    def list_user_exports(
        self,
        user_id: int,
        tax_year: Optional[int] = None,
    ) -> List[TaxSoftwareExport]:
        """List exports for a user"""
        exports = [
            exp for exp in self.exports.values()
            if exp.user_id == user_id
        ]
        
        if tax_year:
            exports = [exp for exp in exports if exp.tax_year == tax_year]
        
        return sorted(exports, key=lambda e: e.exported_at, reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        total_exports = len(self.exports)
        by_software = {}
        
        for exp in self.exports.values():
            by_software[exp.software.value] = by_software.get(exp.software.value, 0) + 1
        
        return {
            "total_exports": total_exports,
            "exports_by_software": by_software,
            "users_with_credentials": len(self.credentials),
        }


# Global instance
tax_software_integration_service = TaxSoftwareIntegrationService()
