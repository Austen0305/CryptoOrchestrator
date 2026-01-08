"""
Crash Report Endpoints
Handles crash reports from Electron and frontend, forwards to incident workflow
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies.auth import require_permission
from ..services.monitoring.sentry_integration import sentry_client

logger = logging.getLogger(__name__)

router = APIRouter()


class ElectronCrashReport(BaseModel):
    """Crash report from Electron app"""

    process_type: str = Field(..., description="Process type (main, renderer)")
    version: str = Field(..., description="App version")
    platform: str = Field(..., description="Platform (win32, darwin, linux)")
    crash_report: str = Field(..., description="JSON stringified crash report")
    timestamp: str = Field(..., description="ISO timestamp")
    environment: str = Field(default="production", description="Environment")


class FrontendCrashReport(BaseModel):
    """Crash report from frontend"""

    error_message: str = Field(..., description="Error message")
    error_stack: str | None = Field(None, description="Error stack trace")
    user_agent: str | None = Field(None, description="User agent")
    url: str | None = Field(None, description="URL where error occurred")
    version: str = Field(..., description="App version")
    timestamp: str = Field(..., description="ISO timestamp")
    environment: str = Field(default="production", description="Environment")
    context: dict[str, Any] | None = Field(None, description="Additional context")


@router.post("/crash-reports/electron")
async def report_electron_crash(
    report: ElectronCrashReport,
    # No auth required for crash reports (service token optional)
):
    """
    Receive crash report from Electron app and forward to incident workflow
    """
    try:
        # Log crash report
        logger.error(
            f"Electron crash report received: {report.process_type} on {report.platform}",
            extra={
                "process_type": report.process_type,
                "version": report.version,
                "platform": report.platform,
                "environment": report.environment,
                "timestamp": report.timestamp,
            },
        )

        # Forward to Sentry if available
        if sentry_client:
            try:
                import json

                crash_data = json.loads(report.crash_report)
                sentry_client.capture_exception(
                    Exception(crash_data.get("message", "Electron crash")),
                    contexts={
                        "electron": {
                            "process_type": report.process_type,
                            "version": report.version,
                            "platform": report.platform,
                        }
                    },
                    tags={
                        "crash_type": "electron",
                        "environment": report.environment,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to forward crash report to Sentry: {e}")

        # TODO: Forward to incident management system (PagerDuty, OpsGenie, etc.)
        # Example:
        # await incident_service.create_incident(
        #     title=f"Electron Crash: {report.process_type}",
        #     severity="high",
        #     source="electron",
        #     details=report.crash_report
        # )

        return {"status": "received", "message": "Crash report received and processed"}

    except Exception as e:
        logger.error(f"Error processing crash report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process crash report")


@router.post("/crash-reports/frontend")
async def report_frontend_crash(
    report: FrontendCrashReport,
    # No auth required for crash reports (service token optional)
):
    """
    Receive crash report from frontend and forward to incident workflow
    """
    try:
        # Log crash report
        logger.error(
            f"Frontend crash report received: {report.error_message}",
            extra={
                "error_message": report.error_message,
                "error_stack": report.error_stack,
                "url": report.url,
                "version": report.version,
                "environment": report.environment,
                "timestamp": report.timestamp,
            },
        )

        # Forward to Sentry if available
        if sentry_client:
            try:
                error = Exception(report.error_message)
                error.__traceback__ = None  # Stack trace in report.error_stack

                sentry_client.capture_exception(
                    error,
                    contexts={
                        "browser": {
                            "user_agent": report.user_agent,
                            "url": report.url,
                        }
                    },
                    tags={
                        "crash_type": "frontend",
                        "environment": report.environment,
                    },
                    extra=report.context or {},
                )
            except Exception as e:
                logger.warning(f"Failed to forward crash report to Sentry: {e}")

        # TODO: Forward to incident management system
        # await incident_service.create_incident(...)

        return {"status": "received", "message": "Crash report received and processed"}

    except Exception as e:
        logger.error(f"Error processing crash report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process crash report")


@router.get("/crash-reports/stats")
async def get_crash_report_stats(
    current_user: Annotated[dict, Depends(require_permission("admin:read"))],
):
    """
    Get crash report statistics (admin only)
    """
    # TODO: Implement crash report statistics
    # Query database for crash reports, aggregate by type, platform, etc.
    return {
        "total_crashes": 0,
        "electron_crashes": 0,
        "frontend_crashes": 0,
        "by_platform": {},
        "by_version": {},
    }
