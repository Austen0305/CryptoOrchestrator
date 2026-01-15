"""
Crash Report Triage Service
Forwards Sentry and Electron crash events to incident management systems (PagerDuty, OpsGenie, etc.)
"""

import logging
import os
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class IncidentSystem(Enum):
    """Supported incident management systems"""

    PAGERDUTY = "pagerduty"
    OPSGENIE = "opsgenie"
    WEBHOOK = "webhook"


class CrashSeverity(Enum):
    """Crash severity levels"""

    LOW = "low"  # Non-critical errors, warnings
    MEDIUM = "medium"  # Errors affecting non-critical features
    HIGH = "high"  # Errors affecting critical features
    CRITICAL = "critical"  # Application crashes, data loss, security issues


class CrashReportTriageService:
    """
    Service for triaging crash reports from Sentry and Electron
    and forwarding critical events to incident management systems.
    """

    def __init__(self):
        self.pagerduty_integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
        self.opsgenie_api_key = os.getenv("OPSGENIE_API_KEY")
        self.opsgenie_api_url = os.getenv(
            "OPSGENIE_API_URL", "https://api.opsgenie.com/v2"
        )
        self.incident_webhook_url = os.getenv("INCIDENT_WEBHOOK_URL")
        self.enabled_systems: list[IncidentSystem] = []

        # Determine which systems are enabled
        if self.pagerduty_integration_key:
            self.enabled_systems.append(IncidentSystem.PAGERDUTY)
        if self.opsgenie_api_key:
            self.enabled_systems.append(IncidentSystem.OPSGENIE)
        if self.incident_webhook_url:
            self.enabled_systems.append(IncidentSystem.WEBHOOK)

        # Severity thresholds for forwarding
        self.forward_threshold = CrashSeverity.HIGH  # Forward HIGH and CRITICAL

        logger.info(
            f"Crash report triage initialized. Enabled systems: {[s.value for s in self.enabled_systems]}"
        )

    def determine_severity(self, event: dict[str, Any]) -> CrashSeverity:
        """
        Determine crash severity from Sentry/Electron event.

        Args:
            event: Sentry event dictionary

        Returns:
            CrashSeverity level
        """
        # Check for critical indicators
        level = event.get("level", "error").lower()
        tags = event.get("tags", {})
        contexts = event.get("contexts", {})

        # Critical: Application crashes, unhandled exceptions
        if (
            level == "fatal"
            or event.get("exception", {}).get("values", [{}])[0].get("type")
            == "SystemExit"
            or tags.get("handled") == "false"
            or contexts.get("runtime", {}).get("name") == "Electron"
            and level == "error"
        ):
            return CrashSeverity.CRITICAL

        # High: Errors in critical paths (trading, authentication, payments)
        critical_paths = ["/api/trades", "/api/auth", "/api/payments", "/api/wallets"]
        request_url = event.get("request", {}).get("url", "")
        if any(path in request_url for path in critical_paths) and level == "error":
            return CrashSeverity.HIGH

        # Medium: Errors in non-critical features
        if level == "error":
            return CrashSeverity.MEDIUM

        # Low: Warnings and info
        return CrashSeverity.LOW

    def should_forward(self, severity: CrashSeverity) -> bool:
        """Check if event should be forwarded to incident management"""
        severity_levels = {
            CrashSeverity.CRITICAL: 4,
            CrashSeverity.HIGH: 3,
            CrashSeverity.MEDIUM: 2,
            CrashSeverity.LOW: 1,
        }
        threshold_level = severity_levels.get(self.forward_threshold, 3)
        event_level = severity_levels.get(severity, 1)

        return event_level >= threshold_level

    async def forward_to_pagerduty(
        self,
        title: str,
        description: str,
        severity: CrashSeverity,
        metadata: dict[str, Any],
    ) -> bool:
        """
        Forward crash event to PagerDuty.

        Args:
            title: Incident title
            description: Incident description
            severity: Crash severity
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.pagerduty_integration_key:
            logger.warning("PagerDuty integration key not configured")
            return False

        # Map severity to PagerDuty severity
        pagerduty_severity_map = {
            CrashSeverity.CRITICAL: "critical",
            CrashSeverity.HIGH: "error",
            CrashSeverity.MEDIUM: "warning",
            CrashSeverity.LOW: "info",
        }

        payload = {
            "routing_key": self.pagerduty_integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": title,
                "source": metadata.get("source", "cryptoorchestrator"),
                "severity": pagerduty_severity_map.get(severity, "error"),
                "custom_details": {
                    "description": description,
                    "timestamp": datetime.now(UTC).isoformat(),
                    **metadata,
                },
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                logger.info(
                    f"Crash event forwarded to PagerDuty: {title}",
                    extra={
                        "severity": severity.value,
                        "pagerduty_response": response.json(),
                    },
                )
                return True
        except Exception as e:
            logger.error(
                f"Failed to forward crash event to PagerDuty: {e}",
                exc_info=True,
                extra={"title": title, "severity": severity.value},
            )
            return False

    async def forward_to_opsgenie(
        self,
        title: str,
        description: str,
        severity: CrashSeverity,
        metadata: dict[str, Any],
    ) -> bool:
        """
        Forward crash event to OpsGenie.

        Args:
            title: Incident title
            description: Incident description
            severity: Crash severity
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.opsgenie_api_key:
            logger.warning("OpsGenie API key not configured")
            return False

        # Map severity to OpsGenie priority
        opsgenie_priority_map = {
            CrashSeverity.CRITICAL: "P1",
            CrashSeverity.HIGH: "P2",
            CrashSeverity.MEDIUM: "P3",
            CrashSeverity.LOW: "P4",
        }

        payload = {
            "message": title,
            "description": description,
            "priority": opsgenie_priority_map.get(severity, "P3"),
            "tags": [
                "crash-report",
                f"severity-{severity.value}",
                metadata.get("source", "cryptoorchestrator"),
            ],
            "details": {"timestamp": datetime.now(UTC).isoformat(), **metadata},
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.opsgenie_api_url}/alerts",
                    json=payload,
                    headers={
                        "Authorization": f"GenieKey {self.opsgenie_api_key}",
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

                logger.info(
                    f"Crash event forwarded to OpsGenie: {title}",
                    extra={
                        "severity": severity.value,
                        "opsgenie_response": response.json(),
                    },
                )
                return True
        except Exception as e:
            logger.error(
                f"Failed to forward crash event to OpsGenie: {e}",
                exc_info=True,
                extra={"title": title, "severity": severity.value},
            )
            return False

    async def forward_to_webhook(
        self,
        title: str,
        description: str,
        severity: CrashSeverity,
        metadata: dict[str, Any],
    ) -> bool:
        """
        Forward crash event to custom webhook.

        Args:
            title: Incident title
            description: Incident description
            severity: Crash severity
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.incident_webhook_url:
            logger.warning("Incident webhook URL not configured")
            return False

        payload = {
            "event_type": "crash_report",
            "title": title,
            "description": description,
            "severity": severity.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.incident_webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                logger.info(
                    f"Crash event forwarded to webhook: {title}",
                    extra={"severity": severity.value},
                )
                return True
        except Exception as e:
            logger.error(
                f"Failed to forward crash event to webhook: {e}",
                exc_info=True,
                extra={"title": title, "severity": severity.value},
            )
            return False

    async def process_sentry_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """
        Process a Sentry webhook event and forward to incident management if needed.

        Args:
            event: Sentry webhook event payload

        Returns:
            Processing result dictionary
        """
        try:
            # Extract event data from Sentry webhook
            action = event.get("action", "")
            if action != "created":
                return {"processed": False, "reason": f"Action {action} not handled"}

            data = event.get("data", {})
            event_data = data.get("event", {})

            # Determine severity
            severity = self.determine_severity(event_data)

            # Check if should forward
            if not self.should_forward(severity):
                logger.debug(
                    f"Sentry event below threshold, not forwarding: {severity.value}",
                    extra={"event_id": event_data.get("event_id")},
                )
                return {"processed": False, "reason": "Below severity threshold"}

            # Extract event details
            title = self._extract_title(event_data)
            description = self._extract_description(event_data)
            metadata = self._extract_metadata(event_data, source="sentry")

            # Forward to enabled systems
            results = {}
            for system in self.enabled_systems:
                if system == IncidentSystem.PAGERDUTY:
                    results["pagerduty"] = await self.forward_to_pagerduty(
                        title, description, severity, metadata
                    )
                elif system == IncidentSystem.OPSGENIE:
                    results["opsgenie"] = await self.forward_to_opsgenie(
                        title, description, severity, metadata
                    )
                elif system == IncidentSystem.WEBHOOK:
                    results["webhook"] = await self.forward_to_webhook(
                        title, description, severity, metadata
                    )

            # Also create incident in internal system
            from ..alerting.incident_management import get_incident_management_service

            incident_service = get_incident_management_service()
            incident = incident_service.create_incident(
                title=title,
                description=description,
                severity=severity.value,
                source="sentry",
                metadata=metadata,
            )

            return {
                "processed": True,
                "severity": severity.value,
                "incident_id": incident["id"],
                "forwarding_results": results,
            }

        except Exception as e:
            logger.error(
                f"Error processing Sentry event: {e}",
                exc_info=True,
                extra={"event": event},
            )
            return {"processed": False, "error": str(e)}

    async def process_electron_crash(
        self, crash_report: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process an Electron crash report and forward to incident management if needed.

        Args:
            crash_report: Electron crash report dictionary

        Returns:
            Processing result dictionary
        """
        try:
            # Electron crashes are always critical
            severity = CrashSeverity.CRITICAL

            title = f"Electron App Crash: {crash_report.get('process_type', 'main')}"
            description = crash_report.get("crash_report", "Application crashed")
            metadata = {
                "source": "electron",
                "process_type": crash_report.get("process_type"),
                "version": crash_report.get("version"),
                "platform": crash_report.get("platform"),
                "crash_report": crash_report.get("crash_report"),
                "minidump": crash_report.get("minidump_path"),
            }

            # Forward to enabled systems
            results = {}
            for system in self.enabled_systems:
                if system == IncidentSystem.PAGERDUTY:
                    results["pagerduty"] = await self.forward_to_pagerduty(
                        title, description, severity, metadata
                    )
                elif system == IncidentSystem.OPSGENIE:
                    results["opsgenie"] = await self.forward_to_opsgenie(
                        title, description, severity, metadata
                    )
                elif system == IncidentSystem.WEBHOOK:
                    results["webhook"] = await self.forward_to_webhook(
                        title, description, severity, metadata
                    )

            # Create incident in internal system
            from ..alerting.incident_management import get_incident_management_service

            incident_service = get_incident_management_service()
            incident = incident_service.create_incident(
                title=title,
                description=description,
                severity=severity.value,
                source="electron",
                metadata=metadata,
            )

            return {
                "processed": True,
                "severity": severity.value,
                "incident_id": incident["id"],
                "forwarding_results": results,
            }

        except Exception as e:
            logger.error(
                f"Error processing Electron crash: {e}",
                exc_info=True,
                extra={"crash_report": crash_report},
            )
            return {"processed": False, "error": str(e)}

    def _extract_title(self, event: dict[str, Any]) -> str:
        """Extract title from Sentry event"""
        message = event.get("message", "")
        if message:
            return message[:100]  # Truncate to 100 chars

        exception = event.get("exception", {}).get("values", [{}])
        if exception:
            exc_type = exception[0].get("type", "Error")
            exc_value = exception[0].get("value", "")
            return f"{exc_type}: {exc_value}"[:100]

        return "Sentry Event"

    def _extract_description(self, event: dict[str, Any]) -> str:
        """Extract description from Sentry event"""
        message = event.get("message", "")
        exception = event.get("exception", {}).get("values", [{}])

        if exception:
            exc_value = exception[0].get("value", "")
            if exc_value:
                return exc_value

        if message:
            return message

        return "No description available"

    def _extract_metadata(self, event: dict[str, Any], source: str) -> dict[str, Any]:
        """Extract metadata from Sentry event"""
        metadata = {
            "source": source,
            "event_id": event.get("event_id"),
            "release": event.get("release"),
            "environment": event.get("environment"),
            "level": event.get("level"),
            "timestamp": event.get("timestamp"),
            "platform": event.get("platform"),
            "sdk": event.get("sdk", {}).get("name"),
            "user": event.get("user", {}),
            "tags": event.get("tags", {}),
        }

        # Add request context if available
        request = event.get("request", {})
        if request:
            metadata["request"] = {
                "url": request.get("url"),
                "method": request.get("method"),
                "headers": request.get("headers", {}),
            }

        # Add exception details if available
        exception = event.get("exception", {}).get("values", [{}])
        if exception:
            metadata["exception"] = {
                "type": exception[0].get("type"),
                "value": exception[0].get("value"),
                "stacktrace": exception[0]
                .get("stacktrace", {})
                .get("frames", [])[-5:],  # Last 5 frames
            }

        return metadata


def get_crash_report_triage_service() -> CrashReportTriageService:
    """Get singleton crash report triage service instance"""
    if not hasattr(get_crash_report_triage_service, "_instance"):
        get_crash_report_triage_service._instance = CrashReportTriageService()
    return get_crash_report_triage_service._instance
