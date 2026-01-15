"""
DORA Operational Resilience Framework

Digital Operational Resilience Act (EU) compliance service.
Required for all CASPs (Crypto-Asset Service Providers) under MiCA.

Implements:
- ICT Risk Management Framework
- Incident Detection and Reporting
- Business Continuity Management
- Third-Party Risk Monitoring
- Resilience Testing Coordination

References:
- DORA Regulation (EU) 2022/2554
- EBA Guidelines on ICT Risk Management
"""

import asyncio
import hashlib
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class IncidentSeverity(str, Enum):
    """Incident severity levels per DORA classification"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    """Types of ICT incidents"""

    CYBER_ATTACK = "cyber_attack"
    SYSTEM_FAILURE = "system_failure"
    DATA_BREACH = "data_breach"
    SERVICE_DEGRADATION = "service_degradation"
    THIRD_PARTY_FAILURE = "third_party_failure"
    NETWORK_OUTAGE = "network_outage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class ServiceStatus(str, Enum):
    """Service health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ICTIncident(BaseModel):
    """ICT Incident record for DORA reporting"""

    incident_id: str
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str
    affected_services: list[str]
    detected_at: datetime
    resolved_at: datetime | None = None
    root_cause: str | None = None
    remediation_actions: list[str] = []
    reported_to_authority: bool = False
    authority_report_deadline: datetime | None = None


class ServiceHealthCheck(BaseModel):
    """Health check result for a service"""

    service_name: str
    status: ServiceStatus
    latency_ms: float
    last_checked: datetime
    error_message: str | None = None
    consecutive_failures: int = 0


class ThirdPartyRisk(BaseModel):
    """Third-party ICT provider risk assessment"""

    provider_name: str
    criticality: str  # critical, important, non-critical
    last_assessment: datetime
    risk_score: float  # 0-100
    compliance_status: str
    sla_metrics: dict[str, float]


@dataclass
class CircuitBreaker:
    """Circuit breaker for service resilience"""

    name: str
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 3

    _state: str = "closed"  # closed, open, half-open
    _failure_count: int = 0
    _last_failure_time: datetime | None = None
    _half_open_calls: int = 0

    def record_success(self) -> None:
        """Record successful call"""
        if self._state == "half-open":
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = "closed"
                self._failure_count = 0
                logger.info(f"Circuit breaker {self.name} closed")
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record failed call"""
        self._failure_count += 1
        self._last_failure_time = datetime.now(UTC)

        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(f"Circuit breaker {self.name} opened")

    def can_execute(self) -> bool:
        """Check if call can be executed"""
        if self._state == "closed":
            return True

        if self._state == "open":
            if self._last_failure_time:
                elapsed = (datetime.now(UTC) - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout_seconds:
                    self._state = "half-open"
                    self._half_open_calls = 0
                    logger.info(f"Circuit breaker {self.name} half-open")
                    return True
            return False

        # half-open: allow limited calls
        return self._half_open_calls < self.half_open_max_calls


class DORAResilienceService:
    """
    DORA Operational Resilience Framework Implementation

    Provides:
    - Continuous service health monitoring
    - Incident detection and classification
    - Automated incident reporting workflow
    - Business continuity tracking
    - Third-party risk management

    DORA requires:
    - Detection within 24 hours
    - Initial report to NCA within 4 hours (critical)
    - Intermediate report within 72 hours
    - Final report within 1 month
    """

    def __init__(self):
        self._incidents: list[ICTIncident] = []
        self._health_checks: dict[str, ServiceHealthCheck] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._third_party_risks: dict[str, ThirdPartyRisk] = {}
        self._metrics: dict[str, deque] = {}  # Rolling metrics

        # Recovery objectives
        self.rto_hours = 4  # Recovery Time Objective
        self.rpo_hours = 1  # Recovery Point Objective

        # Alert callbacks
        self._alert_handlers: list[Callable] = []

    def register_service(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ) -> None:
        """Register a service for monitoring"""
        self._circuit_breakers[service_name] = CircuitBreaker(
            name=service_name,
            failure_threshold=failure_threshold,
            recovery_timeout_seconds=recovery_timeout,
        )
        self._health_checks[service_name] = ServiceHealthCheck(
            service_name=service_name,
            status=ServiceStatus.UNKNOWN,
            latency_ms=0,
            last_checked=datetime.now(UTC),
        )
        logger.info(f"Registered service {service_name} for DORA monitoring")

    async def check_service_health(
        self,
        service_name: str,
        health_check_func: Callable[[], Any],
    ) -> ServiceHealthCheck:
        """Execute health check for a service"""
        if service_name not in self._health_checks:
            self.register_service(service_name)

        cb = self._circuit_breakers[service_name]
        check = self._health_checks[service_name]

        if not cb.can_execute():
            check.status = ServiceStatus.UNHEALTHY
            check.error_message = "Circuit breaker open"
            return check

        start = time.monotonic()
        try:
            await asyncio.wait_for(
                asyncio.to_thread(health_check_func),
                timeout=10.0,
            )
            latency = (time.monotonic() - start) * 1000

            cb.record_success()
            check.status = ServiceStatus.HEALTHY
            check.latency_ms = latency
            check.error_message = None
            check.consecutive_failures = 0

        except TimeoutError:
            cb.record_failure()
            check.status = ServiceStatus.UNHEALTHY
            check.error_message = "Health check timeout"
            check.consecutive_failures += 1

        except Exception as e:
            cb.record_failure()
            check.status = ServiceStatus.UNHEALTHY
            check.error_message = str(e)
            check.consecutive_failures += 1

            # Auto-detect incident if threshold exceeded
            if check.consecutive_failures >= 5:
                await self._auto_detect_incident(service_name, str(e))

        check.last_checked = datetime.now(UTC)
        return check

    async def report_incident(
        self,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        title: str,
        description: str,
        affected_services: list[str],
    ) -> ICTIncident:
        """Report a new ICT incident"""
        now = datetime.now(UTC)
        incident_id = hashlib.sha256(f"{now.isoformat()}:{title}".encode()).hexdigest()[
            :16
        ]

        # Calculate reporting deadline per DORA
        if severity == IncidentSeverity.CRITICAL:
            deadline = now + timedelta(hours=4)
        elif severity == IncidentSeverity.HIGH:
            deadline = now + timedelta(hours=24)
        else:
            deadline = now + timedelta(hours=72)

        incident = ICTIncident(
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            affected_services=affected_services,
            detected_at=now,
            authority_report_deadline=deadline,
        )

        self._incidents.append(incident)

        # Trigger alerts
        await self._trigger_alerts(incident)

        logger.critical(
            f"ICT Incident reported: {incident_id} - {title} "
            f"[{severity.value}] - Report deadline: {deadline}"
        )

        return incident

    async def resolve_incident(
        self,
        incident_id: str,
        root_cause: str,
        remediation_actions: list[str],
    ) -> ICTIncident | None:
        """Resolve an incident"""
        for incident in self._incidents:
            if incident.incident_id == incident_id:
                incident.resolved_at = datetime.now(UTC)
                incident.root_cause = root_cause
                incident.remediation_actions = remediation_actions

                logger.info(f"Incident {incident_id} resolved")
                return incident

        return None

    def register_third_party(
        self,
        provider_name: str,
        criticality: str,
        sla_metrics: dict[str, float] | None = None,
    ) -> None:
        """Register a third-party ICT provider for monitoring"""
        self._third_party_risks[provider_name] = ThirdPartyRisk(
            provider_name=provider_name,
            criticality=criticality,
            last_assessment=datetime.now(UTC),
            risk_score=50.0,  # Default medium risk
            compliance_status="pending_review",
            sla_metrics=sla_metrics or {},
        )

    def assess_third_party_risk(
        self,
        provider_name: str,
        risk_score: float,
        compliance_status: str,
    ) -> ThirdPartyRisk | None:
        """Update third-party risk assessment"""
        if provider_name not in self._third_party_risks:
            return None

        risk = self._third_party_risks[provider_name]
        risk.risk_score = max(0, min(100, risk_score))
        risk.compliance_status = compliance_status
        risk.last_assessment = datetime.now(UTC)

        if risk_score > 70 and risk.criticality == "critical":
            logger.warning(
                f"High risk third-party: {provider_name} (score: {risk_score})"
            )

        return risk

    def get_resilience_report(self) -> dict[str, Any]:
        """Generate DORA resilience report"""
        now = datetime.now(UTC)

        # Count incidents by severity
        incident_stats = {
            "total": len(self._incidents),
            "open": sum(1 for i in self._incidents if i.resolved_at is None),
            "by_severity": {},
        }
        for severity in IncidentSeverity:
            count = sum(1 for i in self._incidents if i.severity == severity)
            incident_stats["by_severity"][severity.value] = count

        # Service health summary
        service_stats = {
            "total": len(self._health_checks),
            "healthy": sum(
                1
                for h in self._health_checks.values()
                if h.status == ServiceStatus.HEALTHY
            ),
            "degraded": sum(
                1
                for h in self._health_checks.values()
                if h.status == ServiceStatus.DEGRADED
            ),
            "unhealthy": sum(
                1
                for h in self._health_checks.values()
                if h.status == ServiceStatus.UNHEALTHY
            ),
        }

        # Third-party risk summary
        tp_stats = {
            "total": len(self._third_party_risks),
            "high_risk": sum(
                1 for r in self._third_party_risks.values() if r.risk_score > 70
            ),
            "critical_providers": sum(
                1
                for r in self._third_party_risks.values()
                if r.criticality == "critical"
            ),
        }

        return {
            "report_type": "DORA_RESILIENCE_REPORT",
            "generated_at": now.isoformat(),
            "recovery_objectives": {
                "rto_hours": self.rto_hours,
                "rpo_hours": self.rpo_hours,
            },
            "incidents": incident_stats,
            "services": service_stats,
            "third_parties": tp_stats,
            "compliance_status": "compliant"
            if incident_stats["open"] == 0 and service_stats["unhealthy"] == 0
            else "review_required",
        }

    def add_alert_handler(self, handler: Callable) -> None:
        """Add alert handler for incident notifications"""
        self._alert_handlers.append(handler)

    async def _trigger_alerts(self, incident: ICTIncident) -> None:
        """Trigger all registered alert handlers"""
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(incident)
                else:
                    handler(incident)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    async def _auto_detect_incident(self, service_name: str, error: str) -> None:
        """Auto-detect and report incident from health check failures"""
        await self.report_incident(
            incident_type=IncidentType.SERVICE_DEGRADATION,
            severity=IncidentSeverity.HIGH,
            title=f"Service degradation: {service_name}",
            description=f"Service {service_name} failed health checks. Error: {error}",
            affected_services=[service_name],
        )


# Singleton instance
_dora_service: DORAResilienceService | None = None


def get_dora_service() -> DORAResilienceService:
    """Get or create DORA resilience service singleton"""
    global _dora_service
    if _dora_service is None:
        _dora_service = DORAResilienceService()
    return _dora_service
