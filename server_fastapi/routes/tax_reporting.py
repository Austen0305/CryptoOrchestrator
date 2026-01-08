"""
Tax Reporting API Routes
Endpoints for tax calculation, reporting, and export
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..dependencies.auth import get_current_user
from ..models.accounting_connection import AccountingSystem as AccountingSystemEnum
from ..services.form_8949_generator import Form8949Generator
from ..services.tax.accounting_connection_service import (
    AccountingConnectionService,
    SyncFrequency,
)
from ..services.tax.accounting_export import (
    AccountingSystem,
    accounting_export_service,
)
from ..services.tax.multi_jurisdiction import (
    Jurisdiction,
    multi_jurisdiction_tax_service,
)
from ..services.tax.tax_software_integration import (
    TaxSoftware,
    tax_software_integration_service,
)
from ..services.tax_calculation_service import (
    CostBasisMethod,
    tax_calculation_service,
)
from ..utils.route_helpers import _get_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tax", tags=["Tax Reporting"])


# Request/Response Models
class TaxSummaryResponse(BaseModel):
    symbol: str | None
    start_date: str | None
    end_date: str | None
    total_events: int
    short_term: dict[str, float]
    long_term: dict[str, float]
    total_proceeds: float
    total_cost_basis: float
    net_gain_loss: float
    wash_sales: dict[str, Any]


class TaxLossHarvestingResponse(BaseModel):
    symbol: str
    opportunities: list[dict[str, Any]]


class Form8949Response(BaseModel):
    tax_year: int
    user_id: int
    part_i: dict[str, Any]
    part_ii: dict[str, Any]
    summary: dict[str, Any]
    generated_at: str


@router.get("/summary", response_model=TaxSummaryResponse)
async def get_tax_summary(
    current_user: Annotated[dict, Depends(get_current_user)],
    symbol: str | None = Query(None, description="Filter by symbol"),
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
) -> TaxSummaryResponse:
    """
    Get tax summary for reporting

    Returns short-term and long-term capital gains/losses summary.
    """
    try:
        summary = tax_calculation_service.get_tax_summary(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        return TaxSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting tax summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get tax summary")


@router.get("/loss-harvesting/{symbol}", response_model=TaxLossHarvestingResponse)
async def get_tax_loss_harvesting_opportunities(
    symbol: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    current_price: float = Query(..., description="Current market price"),
    threshold_percent: float = Query(
        0.1, ge=0, le=1, description="Loss threshold (0.1 = 10%)"
    ),
) -> TaxLossHarvestingResponse:
    """
    Get tax-loss harvesting opportunities

    Identifies lots that are at a loss and could be sold to realize
    tax losses.
    """
    try:
        opportunities = tax_calculation_service.get_tax_loss_harvesting_opportunities(
            symbol=symbol,
            current_price=current_price,
            threshold_percent=threshold_percent,
        )

        # Convert dataclasses to dicts for JSON serialization
        opportunities_dict = []
        for opp in opportunities:
            opp_dict = {
                "purchase_date": opp["lot"].purchase_date.isoformat(),
                "purchase_price": opp["lot"].purchase_price,
                "quantity": opp["lot"].remaining_quantity,
                "current_price": opp["current_price"],
                "current_value": opp["current_value"],
                "cost_basis": opp["cost_basis"],
                "unrealized_loss": opp["unrealized_loss"],
                "loss_percent": opp["loss_percent"],
                "holding_period_days": opp["holding_period_days"],
            }
            opportunities_dict.append(opp_dict)

        return TaxLossHarvestingResponse(
            symbol=symbol,
            opportunities=opportunities_dict,
        )
    except Exception as e:
        logger.error(
            f"Error getting tax-loss harvesting opportunities: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to get tax-loss harvesting opportunities"
        )


@router.get("/form-8949", response_model=Form8949Response)
async def get_form_8949(
    current_user: Annotated[dict, Depends(get_current_user)],
    tax_year: int = Query(..., ge=2020, le=2100, description="Tax year"),
    method: str = Query("fifo", description="Cost basis method: fifo, lifo, average"),
) -> Form8949Response:
    """
    Generate IRS Form 8949

    Returns Form 8949 data structure for the specified tax year.
    """
    try:
        user_id = _get_user_id(current_user)

        generator = Form8949Generator(tax_calculation_service)
        form_data = generator.generate_form_8949(
            user_id=user_id,
            tax_year=tax_year,
            method=method,
        )

        return Form8949Response(**form_data)
    except Exception as e:
        logger.error(f"Error generating Form 8949: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate Form 8949")


@router.get("/form-8949/export")
async def export_form_8949(
    current_user: Annotated[dict, Depends(get_current_user)],
    tax_year: int = Query(..., ge=2020, le=2100, description="Tax year"),
    method: str = Query("fifo", description="Cost basis method"),
    format: str = Query("csv", description="Export format: csv, json"),
):
    """
    Export Form 8949 in various formats

    Supports CSV and JSON formats for import into tax software.
    """
    try:
        user_id = _get_user_id(current_user)

        generator = Form8949Generator(tax_calculation_service)
        form_data = generator.generate_form_8949(
            user_id=user_id,
            tax_year=tax_year,
            method=method,
        )

        if format == "csv":
            csv_content = generator.export_to_csv(form_data)
            from fastapi.responses import Response

            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=form8949_{tax_year}.csv"
                },
            )
        elif format == "json":
            json_data = generator.export_to_json(form_data)
            return json_data
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting Form 8949: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export Form 8949")


@router.get("/wash-sales")
async def get_wash_sales(
    current_user: Annotated[dict, Depends(get_current_user)],
    symbol: str | None = Query(None, description="Filter by symbol"),
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
) -> dict[str, Any]:
    """
    Get wash sale warnings and adjustments

    Identifies transactions that may qualify as wash sales and
    shows the adjustments that need to be made.
    """
    try:
        summary = tax_calculation_service.get_tax_summary(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        wash_sales_info = summary.get("wash_sales", {})

        return {
            "wash_sale_count": wash_sales_info.get("count", 0),
            "total_adjustment": wash_sales_info.get("total_adjustment", 0.0),
            "warning": "Wash sales disallow loss deductions. Adjustments have been applied to cost basis.",
        }
    except Exception as e:
        logger.error(f"Error getting wash sales: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get wash sales")


@router.post("/calculate")
async def calculate_tax_event(
    symbol: str,
    sale_date: datetime,
    sale_price: float,
    quantity: float,
    current_user: Annotated[dict, Depends(get_current_user)],
    method: str = Query("fifo", description="Cost basis method"),
    trade_id: int | None = None,
) -> dict[str, Any]:
    """
    Calculate tax for a sale event

    This endpoint allows manual calculation of tax events.
    In production, this would be called automatically when trades are executed.
    """
    try:
        cost_method = CostBasisMethod(method.lower())

        event = tax_calculation_service.calculate_sale(
            symbol=symbol,
            sale_date=sale_date,
            sale_price=sale_price,
            quantity=quantity,
            method=cost_method,
            trade_id=trade_id,
        )

        return {
            "sale_date": event.sale_date.isoformat(),
            "sale_price": event.sale_price,
            "quantity": event.quantity,
            "proceeds": event.proceeds,
            "cost_basis": event.cost_basis,
            "gain_loss": event.gain_loss,
            "holding_period_days": event.holding_period_days,
            "is_long_term": event.is_long_term,
            "is_wash_sale": event.is_wash_sale,
            "wash_sale_adjustment": event.wash_sale_adjustment,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating tax event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate tax event")


# Multi-Jurisdiction Endpoints
@router.get("/jurisdictions")
async def get_supported_jurisdictions(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, Any]:
    """
    Get list of supported tax jurisdictions

    Returns tax rules and settings for each supported country.
    """
    try:
        jurisdictions = multi_jurisdiction_tax_service.get_supported_jurisdictions()
        return {
            "jurisdictions": jurisdictions,
            "count": len(jurisdictions),
        }
    except Exception as e:
        logger.error(f"Error getting jurisdictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get jurisdictions")


@router.get("/jurisdictions/{jurisdiction_code}/tax-year")
async def get_tax_year(
    jurisdiction_code: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    date: datetime = Query(..., description="Date to calculate tax year for"),
) -> dict[str, Any]:
    """
    Calculate tax year for a given date and jurisdiction
    """
    try:
        jurisdiction = Jurisdiction(jurisdiction_code.upper())
        tax_year = multi_jurisdiction_tax_service.calculate_tax_year(date, jurisdiction)
        start_date, end_date = multi_jurisdiction_tax_service.get_tax_year_range(
            tax_year, jurisdiction
        )

        return {
            "jurisdiction": jurisdiction_code.upper(),
            "date": date.isoformat(),
            "tax_year": tax_year,
            "tax_year_start": start_date.isoformat(),
            "tax_year_end": end_date.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating tax year: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate tax year")


@router.post("/jurisdictions/{jurisdiction_code}/calculate-tax")
async def calculate_tax_liability(
    jurisdiction_code: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    gain_loss: float = Query(..., description="Gain or loss amount"),
    is_long_term: bool = Query(..., description="Is long-term holding"),
    tax_year: int | None = Query(None, description="Tax year"),
) -> dict[str, Any]:
    """
    Calculate tax liability for a gain/loss in a specific jurisdiction
    """
    try:
        jurisdiction = Jurisdiction(jurisdiction_code.upper())
        tax_calculation = multi_jurisdiction_tax_service.calculate_tax_liability(
            gain_loss=gain_loss,
            is_long_term=is_long_term,
            jurisdiction=jurisdiction,
            tax_year=tax_year,
        )

        return tax_calculation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating tax liability: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate tax liability")


# Accounting System Export Endpoints
@router.get("/export/accounting/{system}")
async def export_to_accounting_system(
    system: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    tax_year: int = Query(..., ge=2020, le=2100, description="Tax year"),
    format: str = Query("csv", description="Export format"),
):
    """
    Export tax data to accounting system (QuickBooks, Xero, etc.)

    Supported systems:
    - quickbooks (IIF format)
    - xero (CSV format)
    - csv_generic (Generic CSV)
    """
    try:
        user_id = _get_user_id(current_user)

        # Get tax events for the year (simplified - would fetch from database)
        # In production, this would query actual tax events from the database
        tax_events = []  # Placeholder - would be populated from database

        # Convert system string to enum
        try:
            accounting_system = AccountingSystem(system.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported accounting system: {system}. Supported: {[s.value for s in AccountingSystem]}",
            )

        # Export
        exported_data = accounting_export_service.export(
            tax_events=tax_events,
            system=accounting_system,
            tax_year=tax_year,
        )

        # Determine content type and filename
        if accounting_system == AccountingSystem.QUICKBOOKS:
            content_type = "application/x-iif"
            filename = f"quickbooks_export_{tax_year}.iif"
        else:
            content_type = "text/csv"
            filename = f"{system}_export_{tax_year}.csv"

        from fastapi.responses import Response

        return Response(
            content=exported_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to accounting system: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to export to accounting system"
        )


@router.post("/export/accounting/{system}/from-events")
async def export_tax_events_to_accounting(
    system: str,
    tax_events: list[dict[str, Any]],
    current_user: Annotated[dict, Depends(get_current_user)],
    tax_year: int = Query(..., ge=2020, le=2100, description="Tax year"),
):
    """
    Export specific tax events to accounting system

    Accepts a list of tax events and exports them in the specified format.
    """
    try:
        # Convert system string to enum
        try:
            accounting_system = AccountingSystem(system.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Unsupported accounting system: {system}"
            )

        # Export
        exported_data = accounting_export_service.export(
            tax_events=tax_events,
            system=accounting_system,
            tax_year=tax_year,
        )

        # Determine content type and filename
        if accounting_system == AccountingSystem.QUICKBOOKS:
            content_type = "application/x-iif"
            filename = f"quickbooks_export_{tax_year}.iif"
        else:
            content_type = "text/csv"
            filename = f"{system}_export_{tax_year}.csv"

        from fastapi.responses import Response

        return Response(
            content=exported_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting tax events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export tax events")


# Tax Software Integration Endpoints
class ExportToTaxSoftwareRequest(BaseModel):
    tax_year: int = Field(..., description="Tax year")
    tax_data: dict[str, Any] = Field(..., description="Tax data to export")


class StoreCredentialsRequest(BaseModel):
    software: str = Field(..., description="Tax software: taxact, turbotax, hr_block")
    api_key: str | None = Field(None, description="API key")
    access_token: str | None = Field(None, description="Access token")
    refresh_token: str | None = Field(None, description="Refresh token")


@router.post("/export/taxact")
async def export_to_taxact(
    request: ExportToTaxSoftwareRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Export tax data to TaxAct"""
    try:
        user_id = _get_user_id(current_user)

        export = tax_software_integration_service.export_to_taxact(
            user_id=user_id,
            tax_year=request.tax_year,
            tax_data=request.tax_data,
        )

        return {
            "export_id": export.export_id,
            "software": export.software.value,
            "format": export.format,
            "status": export.status,
            "exported_at": export.exported_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error exporting to TaxAct: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export to TaxAct")


@router.post("/export/turbotax")
async def export_to_turbotax(
    request: ExportToTaxSoftwareRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Export tax data to TurboTax"""
    try:
        user_id = _get_user_id(current_user)

        export = tax_software_integration_service.export_to_turbotax(
            user_id=user_id,
            tax_year=request.tax_year,
            tax_data=request.tax_data,
        )

        return {
            "export_id": export.export_id,
            "software": export.software.value,
            "format": export.format,
            "status": export.status,
            "exported_at": export.exported_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error exporting to TurboTax: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export to TurboTax")


@router.post("/export/hr-block")
async def export_to_hr_block(
    request: ExportToTaxSoftwareRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Export tax data to H&R Block"""
    try:
        user_id = _get_user_id(current_user)

        export = tax_software_integration_service.export_to_hr_block(
            user_id=user_id,
            tax_year=request.tax_year,
            tax_data=request.tax_data,
        )

        return {
            "export_id": export.export_id,
            "software": export.software.value,
            "format": export.format,
            "status": export.status,
            "exported_at": export.exported_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error exporting to H&R Block: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export to H&R Block")


@router.post("/software/credentials")
async def store_tax_software_credentials(
    request: StoreCredentialsRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Store tax software API credentials"""
    try:
        user_id = _get_user_id(current_user)
        software = TaxSoftware(request.software.lower())

        tax_software_integration_service.store_credentials(
            user_id=user_id,
            software=software,
            api_key=request.api_key,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
        )

        return {"status": "ok", "software": software.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error storing credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store credentials")


@router.get("/software/exports")
async def list_tax_software_exports(
    current_user: Annotated[dict, Depends(get_current_user)],
    tax_year: int | None = Query(None, description="Filter by tax year"),
):
    """List tax software exports for user"""
    try:
        user_id = _get_user_id(current_user)

        exports = tax_software_integration_service.list_user_exports(
            user_id=user_id,
            tax_year=tax_year,
        )

        return [
            {
                "export_id": exp.export_id,
                "software": exp.software.value,
                "tax_year": exp.tax_year,
                "format": exp.format,
                "status": exp.status,
                "exported_at": exp.exported_at.isoformat(),
            }
            for exp in exports
        ]
    except Exception as e:
        logger.error(f"Error listing exports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list exports")


@router.get("/software/statistics")
async def get_tax_software_statistics(
    current_user: Annotated[dict, Depends(get_current_user)] = None,
):
    """Get tax software integration statistics"""
    try:
        return tax_software_integration_service.get_statistics()
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# Accounting System OAuth Routes
class ConnectAccountingRequest(BaseModel):
    system: str = Field(..., description="Accounting system: quickbooks or xero")


class CompleteOAuthRequest(BaseModel):
    system: str = Field(..., description="Accounting system: quickbooks or xero")
    authorization_code: str = Field(
        ..., description="Authorization code from OAuth callback"
    )
    state: str | None = Field(None, description="State parameter from OAuth callback")


class UpdateSyncConfigRequest(BaseModel):
    sync_frequency: str = Field(
        ..., description="Sync frequency: manual, daily, weekly, monthly"
    )
    account_mappings: dict[str, str] | None = Field(
        None, description="Account code mappings"
    )


@router.get("/accounting/connect/{system}")
async def connect_accounting_system(
    system: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get OAuth authorization URL for accounting system"""
    try:
        user_id = _get_user_id(current_user)
        service = AccountingConnectionService(db)

        system_enum = AccountingSystemEnum(system.lower())
        auth_url = await service.get_authorization_url(user_id, system_enum)

        return {"authorization_url": auth_url, "system": system}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting authorization URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get authorization URL")


@router.post("/accounting/complete")
async def complete_accounting_oauth(
    request: CompleteOAuthRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Complete OAuth flow and store credentials"""
    try:
        user_id = _get_user_id(current_user)
        service = AccountingConnectionService(db)

        system_enum = AccountingSystemEnum(request.system.lower())
        connection = await service.complete_oauth_flow(
            user_id, system_enum, request.authorization_code, request.state
        )

        return {
            "id": connection.id,
            "system": connection.system,
            "status": connection.status,
            "connected_at": connection.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing OAuth: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete OAuth")


@router.get("/accounting/connections")
async def get_accounting_connections(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get all accounting connections for user"""
    try:
        user_id = _get_user_id(current_user)
        service = AccountingConnectionService(db)

        connections = await service.get_user_connections(user_id)

        return [
            {
                "id": c.id,
                "system": c.system,
                "status": c.status,
                "sync_frequency": c.sync_frequency,
                "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
                "next_sync_at": c.next_sync_at.isoformat() if c.next_sync_at else None,
                "enabled": c.enabled,
                "connected_at": c.created_at.isoformat(),
            }
            for c in connections
        ]
    except Exception as e:
        logger.error(f"Error getting connections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get connections")


@router.post("/accounting/export/{system}")
async def export_to_accounting_system(
    system: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tax_year: int = Query(..., description="Tax year"),
    start_date: datetime | None = Query(None, description="Start date"),
    end_date: datetime | None = Query(None, description="End date"),
):
    """Export tax data to accounting system via API"""
    try:
        user_id = _get_user_id(current_user)
        service = AccountingConnectionService(db)

        system_enum = AccountingSystemEnum(system.lower())
        connection = await service.get_connection(user_id, system_enum)

        if not connection or connection.status != "connected":
            raise HTTPException(
                status_code=400, detail="Accounting system not connected"
            )

        # Get credentials
        credentials = await service.get_credentials(connection)
        if not credentials:
            raise HTTPException(status_code=400, detail="Failed to get credentials")

        # Get tax events (simplified - in production, fetch from tax service)
        # For now, return success
        return {
            "success": True,
            "system": system,
            "tax_year": tax_year,
            "message": "Export initiated (implementation pending)",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to accounting system: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export")


@router.post("/accounting/{system}/sync-config")
async def update_sync_config(
    system: str,
    request: UpdateSyncConfigRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update sync configuration"""
    try:
        user_id = _get_user_id(current_user)
        service = AccountingConnectionService(db)

        system_enum = AccountingSystemEnum(system.lower())
        sync_freq = SyncFrequency(request.sync_frequency.lower())

        connection = await service.update_sync_config(
            user_id, system_enum, sync_freq, request.account_mappings
        )

        return {
            "id": connection.id,
            "sync_frequency": connection.sync_frequency,
            "next_sync_at": connection.next_sync_at.isoformat()
            if connection.next_sync_at
            else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating sync config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update sync config")


@router.delete("/accounting/{system}/disconnect")
async def disconnect_accounting_system(
    system: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Disconnect accounting system"""
    try:
        user_id = _get_user_id(current_user)
        service = AccountingConnectionService(db)

        system_enum = AccountingSystemEnum(system.lower())
        success = await service.disconnect(user_id, system_enum)

        if not success:
            raise HTTPException(status_code=404, detail="Connection not found")

        return {"success": True, "system": system}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to disconnect")
