"""
Incident Management Service
Provides integration with external incident management systems (PagerDuty, Opsgenie, etc.)
and automated incident response workflows.
"""

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class IncidentStatus(Enum):
    """Incident status values"""

    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentPriority(Enum):
    """Incident priority levels"""

    P5 = "P5"  # Lowest
    P4 = "P4"
    P3 = "P3"
    P2 = "P2"
    P1 = "P1"  # Highest


class IncidentManagementService:
    """
    Service for managing incidents and integrating with external systems
    """

    def __init__(self):
        self.incidents: dict[str, dict[str, Any]] = {}
        self.integrations: dict[str, Any] = {}
        self.response_playbooks: dict[str, dict[str, Any]] = {}

    def create_incident(
        self,
        title: str,
        description: str,
        severity: str,
        source: str = "alerting",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new incident

        Args:
            title: Incident title
            description: Incident description
            severity: Severity level (low, medium, high, critical)
            source: Source of incident (alerting, manual, etc.)
            metadata: Additional metadata

        Returns:
            Incident dictionary with ID and details
        """
        incident = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "severity": severity,
            "status": IncidentStatus.OPEN.value,
            "priority": self._calculate_priority(severity),
            "source": source,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "assigned_to": None,
            "related_alerts": [],
            "response_steps": [],
            "metadata": metadata or {},
        }

        self.incidents[incident["id"]] = incident

        # Execute response playbook if available
        playbook = self.response_playbooks.get(severity)
        if playbook:
            self._execute_playbook(incident, playbook)

        logger.warning(
            f"Incident created: {incident['id']} - {title}",
            extra={
                "incident_id": incident["id"],
                "severity": severity,
                "priority": incident["priority"],
            },
        )

        return incident

    def _calculate_priority(self, severity: str) -> str:
        """Calculate incident priority from severity"""
        priority_map = {
            "critical": IncidentPriority.P1.value,
            "high": IncidentPriority.P2.value,
            "medium": IncidentPriority.P3.value,
            "low": IncidentPriority.P4.value,
        }
        return priority_map.get(severity.lower(), IncidentPriority.P4.value)

    def _execute_playbook(
        self, incident: dict[str, Any], playbook: dict[str, Any]
    ) -> None:
        """Execute incident response playbook"""
        steps = playbook.get("steps", [])

        for step in steps:
            try:
                action = step.get("action")
                if action == "notify_team":
                    self._notify_team(incident, step.get("team", "oncall"))
                elif action == "create_ticket":
                    self._create_ticket(incident, step.get("system", "jira"))
                elif action == "escalate":
                    self._escalate_incident(incident, step.get("level", 1))
                elif action == "run_script":
                    self._run_automation_script(incident, step.get("script"))
            except Exception as e:
                logger.error(
                    f"Error executing playbook step: {e}",
                    exc_info=True,
                    extra={"incident_id": incident["id"], "step": step},
                )

    def _notify_team(self, incident: dict[str, Any], team: str) -> None:
        """Notify on-call team about incident"""
        logger.info(
            f"Notifying {team} team about incident {incident['id']}",
            extra={"incident_id": incident["id"], "team": team},
        )
        # Integration with notification service would go here

    def _create_ticket(self, incident: dict[str, Any], system: str) -> None:
        """Create ticket in external system (Jira, ServiceNow, etc.)"""
        logger.info(
            f"Creating ticket in {system} for incident {incident['id']}",
            extra={"incident_id": incident["id"], "system": system},
        )
        # Integration with ticketing system would go here

    def _escalate_incident(self, incident: dict[str, Any], level: int) -> None:
        """Escalate incident to higher level"""
        logger.warning(
            f"Escalating incident {incident['id']} to level {level}",
            extra={"incident_id": incident["id"], "escalation_level": level},
        )
        incident["metadata"]["escalation_level"] = level

    def _run_automation_script(
        self, incident: dict[str, Any], script: str | None
    ) -> None:
        """Run automation script for incident response"""
        if not script:
            return

        logger.info(
            f"Running automation script {script} for incident {incident['id']}",
            extra={"incident_id": incident["id"], "script": script},
        )
        # Automation script execution would go here

    def update_incident_status(
        self, incident_id: str, status: IncidentStatus, updated_by: str | None = None
    ) -> bool:
        """Update incident status"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        incident["status"] = status.value
        incident["updated_at"] = datetime.utcnow().isoformat()

        if status == IncidentStatus.RESOLVED:
            incident["resolved_at"] = datetime.utcnow().isoformat()

        if updated_by:
            incident["metadata"]["updated_by"] = updated_by

        logger.info(
            f"Incident {incident_id} status updated to {status.value}",
            extra={
                "incident_id": incident_id,
                "status": status.value,
                "updated_by": updated_by,
            },
        )

        return True

    def assign_incident(self, incident_id: str, assignee: str) -> bool:
        """Assign incident to a team member"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        incident["assigned_to"] = assignee
        incident["updated_at"] = datetime.utcnow().isoformat()

        logger.info(
            f"Incident {incident_id} assigned to {assignee}",
            extra={"incident_id": incident_id, "assignee": assignee},
        )

        return True

    def add_response_step(
        self, incident_id: str, step: str, executed_by: str | None = None
    ) -> bool:
        """Add a response step to incident"""
        if incident_id not in self.incidents:
            return False

        incident = self.incidents[incident_id]
        response_step = {
            "step": step,
            "executed_by": executed_by,
            "timestamp": datetime.utcnow().isoformat(),
        }
        incident["response_steps"].append(response_step)
        incident["updated_at"] = datetime.utcnow().isoformat()

        return True

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        """Get incident by ID"""
        return self.incidents.get(incident_id)

    def get_active_incidents(self, severity: str | None = None) -> list[dict[str, Any]]:
        """Get active incidents"""
        incidents = [
            i
            for i in self.incidents.values()
            if i["status"]
            not in [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value]
        ]

        if severity:
            incidents = [i for i in incidents if i["severity"] == severity]

        return sorted(incidents, key=lambda i: i["created_at"], reverse=True)

    def register_playbook(self, severity: str, playbook: dict[str, Any]) -> None:
        """Register a response playbook for a severity level"""
        self.response_playbooks[severity] = playbook
        logger.info(f"Registered response playbook for severity: {severity}")


def get_incident_management_service() -> IncidentManagementService:
    """Get singleton incident management service instance"""
    if not hasattr(get_incident_management_service, "_instance"):
        get_incident_management_service._instance = IncidentManagementService()
    return get_incident_management_service._instance
