"""
Alert Routing and Escalation Service
Escalation policies, on-call rotation, and notification routing
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EscalationAction(str, Enum):
    """Escalation action type"""

    NOTIFY = "notify"
    PAGE = "page"
    CREATE_TICKET = "create_ticket"
    EXECUTE_RUNBOOK = "execute_runbook"


@dataclass
class EscalationStep:
    """Escalation step"""

    delay_minutes: int  # Minutes to wait before escalating
    action: EscalationAction
    target: str  # User ID, email, on-call rotation, etc.
    message_template: str | None = None


@dataclass
class EscalationPolicy:
    """Escalation policy"""

    id: str
    name: str
    description: str | None = None
    alert_severity: str  # "low", "medium", "high", "critical"
    steps: list[EscalationStep] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OnCallRotation:
    """On-call rotation"""

    id: str
    name: str
    team_members: list[str]  # User IDs
    current_on_call: str | None = None
    rotation_schedule: str = "weekly"  # "daily", "weekly", "monthly"
    start_date: datetime = field(default_factory=datetime.utcnow)
    timezone: str = "UTC"


@dataclass
class AlertEscalation:
    """Alert escalation record"""

    alert_key: str
    policy_id: str
    current_step: int
    escalated_at: datetime
    next_escalation: datetime | None = None
    completed: bool = False


class AlertEscalationService:
    """
    Alert routing and escalation service

    Features:
    - Escalation policies
    - On-call rotation management
    - Alert routing
    - Multi-step escalation
    - Notification channels
    """

    def __init__(self):
        self.escalation_policies: dict[str, EscalationPolicy] = {}
        self.on_call_rotations: dict[str, OnCallRotation] = {}
        self.active_escalations: dict[str, AlertEscalation] = {}
        self.notification_channels: dict[str, dict[str, Any]] = {}

    def create_escalation_policy(
        self,
        name: str,
        alert_severity: str,
        steps: list[dict[str, Any]],
        description: str | None = None,
    ) -> EscalationPolicy:
        """
        Create an escalation policy

        Args:
            name: Policy name
            alert_severity: Severity level this policy applies to
            steps: List of escalation steps
            description: Optional description

        Returns:
            EscalationPolicy
        """
        policy_id = f"policy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        escalation_steps = [
            EscalationStep(
                delay_minutes=step.get("delay_minutes", 15),
                action=EscalationAction(step.get("action", "notify")),
                target=step.get("target", ""),
                message_template=step.get("message_template"),
            )
            for step in steps
        ]

        policy = EscalationPolicy(
            id=policy_id,
            name=name,
            description=description,
            alert_severity=alert_severity,
            steps=escalation_steps,
        )

        self.escalation_policies[policy_id] = policy

        logger.info(f"Created escalation policy {policy_id}: {name}")

        return policy

    def create_on_call_rotation(
        self,
        name: str,
        team_members: list[str],
        rotation_schedule: str = "weekly",
        timezone: str = "UTC",
    ) -> OnCallRotation:
        """
        Create an on-call rotation

        Args:
            name: Rotation name
            team_members: List of user IDs
            rotation_schedule: Schedule type
            timezone: Timezone

        Returns:
            OnCallRotation
        """
        rotation_id = f"rotation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Set initial on-call (first member)
        current_on_call = team_members[0] if team_members else None

        rotation = OnCallRotation(
            id=rotation_id,
            name=name,
            team_members=team_members,
            current_on_call=current_on_call,
            rotation_schedule=rotation_schedule,
            timezone=timezone,
        )

        self.on_call_rotations[rotation_id] = rotation

        logger.info(f"Created on-call rotation {rotation_id}: {name}")

        return rotation

    def escalate_alert(
        self,
        alert_key: str,
        alert_severity: str,
    ) -> AlertEscalation | None:
        """
        Escalate an alert based on policies

        Args:
            alert_key: Alert key
            alert_severity: Alert severity

        Returns:
            AlertEscalation if policy found
        """
        # Find matching policy
        policy = None
        for p in self.escalation_policies.values():
            if p.alert_severity == alert_severity and p.enabled:
                policy = p
                break

        if not policy:
            return None

        # Create escalation
        escalation = AlertEscalation(
            alert_key=alert_key,
            policy_id=policy.id,
            current_step=0,
            escalated_at=datetime.utcnow(),
        )

        # Calculate next escalation time
        if policy.steps:
            first_step = policy.steps[0]
            escalation.next_escalation = datetime.utcnow() + timedelta(
                minutes=first_step.delay_minutes
            )

        self.active_escalations[alert_key] = escalation

        # Execute first step
        self._execute_escalation_step(escalation, policy, 0)

        logger.info(f"Escalated alert {alert_key} using policy {policy.id}")

        return escalation

    def _execute_escalation_step(
        self,
        escalation: AlertEscalation,
        policy: EscalationPolicy,
        step_index: int,
    ):
        """Execute an escalation step"""
        if step_index >= len(policy.steps):
            escalation.completed = True
            return

        step = policy.steps[step_index]

        # Determine target
        target = step.target

        # If target is a rotation, get current on-call
        if target.startswith("rotation:"):
            rotation_id = target.replace("rotation:", "")
            rotation = self.on_call_rotations.get(rotation_id)
            if rotation and rotation.current_on_call:
                target = rotation.current_on_call

        # Execute action
        if step.action == EscalationAction.NOTIFY:
            self._send_notification(target, escalation, step)
        elif step.action == EscalationAction.PAGE:
            self._send_page(target, escalation, step)
        elif step.action == EscalationAction.CREATE_TICKET:
            self._create_ticket(target, escalation, step)

        logger.info(
            f"Executed escalation step {step_index} for alert {escalation.alert_key}: "
            f"{step.action.value} to {target}"
        )

    def _send_notification(
        self,
        target: str,
        escalation: AlertEscalation,
        step: EscalationStep,
    ):
        """Send notification (placeholder)"""
        # In production, would integrate with notification service
        logger.info(
            f"Sending notification to {target} for alert {escalation.alert_key}"
        )

    def _send_page(
        self,
        target: str,
        escalation: AlertEscalation,
        step: EscalationStep,
    ):
        """Send page (placeholder)"""
        # In production, would integrate with paging service
        logger.info(f"Paging {target} for alert {escalation.alert_key}")

    def _create_ticket(
        self,
        target: str,
        escalation: AlertEscalation,
        step: EscalationStep,
    ):
        """Create ticket (placeholder)"""
        # In production, would integrate with ticketing system
        logger.info(f"Creating ticket for alert {escalation.alert_key}")

    def process_escalations(self):
        """Process pending escalations (should be called periodically)"""
        now = datetime.utcnow()

        for alert_key, escalation in list(self.active_escalations.items()):
            if escalation.completed:
                continue

            if escalation.next_escalation and now >= escalation.next_escalation:
                policy = self.escalation_policies.get(escalation.policy_id)
                if policy:
                    # Move to next step
                    escalation.current_step += 1

                    if escalation.current_step < len(policy.steps):
                        # Execute next step
                        self._execute_escalation_step(
                            escalation, policy, escalation.current_step
                        )

                        # Calculate next escalation time
                        next_step = policy.steps[escalation.current_step]
                        escalation.next_escalation = now + timedelta(
                            minutes=next_step.delay_minutes
                        )
                    else:
                        # All steps completed
                        escalation.completed = True
                        escalation.next_escalation = None

    def get_escalation_policy(self, policy_id: str) -> EscalationPolicy | None:
        """Get escalation policy"""
        return self.escalation_policies.get(policy_id)

    def get_on_call_rotation(self, rotation_id: str) -> OnCallRotation | None:
        """Get on-call rotation"""
        return self.on_call_rotations.get(rotation_id)

    def get_active_escalations(self) -> list[AlertEscalation]:
        """Get active escalations"""
        return [esc for esc in self.active_escalations.values() if not esc.completed]

    def resolve_escalation(self, alert_key: str):
        """Resolve an escalation"""
        if alert_key in self.active_escalations:
            self.active_escalations[alert_key].completed = True
            logger.info(f"Resolved escalation for alert {alert_key}")


# Global instance
alert_escalation_service = AlertEscalationService()
