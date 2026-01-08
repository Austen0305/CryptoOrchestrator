"""
Custom Metric Dashboards Service
User-configurable metric dashboards
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Chart type"""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    GAUGE = "gauge"
    HEATMAP = "heatmap"


@dataclass
class DashboardWidget:
    """Dashboard widget"""

    id: str
    title: str
    chart_type: ChartType
    metric_name: str
    time_range: str  # "1h", "24h", "7d", "30d"
    position: dict[str, int]  # x, y, width, height
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Dashboard:
    """Custom dashboard"""

    id: str
    user_id: int
    name: str
    description: str | None = None
    widgets: list[DashboardWidget] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_public: bool = False


class CustomDashboardsService:
    """
    Custom metric dashboards service

    Features:
    - User-configurable dashboards
    - Widget management
    - Dashboard sharing
    - Template dashboards
    """

    def __init__(self):
        self.dashboards: dict[str, Dashboard] = {}
        self.user_dashboards: dict[int, list[str]] = defaultdict(list)
        self.templates: dict[str, Dashboard] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize template dashboards"""
        # System health template
        system_health = Dashboard(
            id="template_system_health",
            user_id=0,  # System template
            name="System Health",
            description="Default system health dashboard",
            widgets=[
                DashboardWidget(
                    id="cpu_usage",
                    title="CPU Usage",
                    chart_type=ChartType.LINE,
                    metric_name="cpu_usage",
                    time_range="1h",
                    position={"x": 0, "y": 0, "width": 6, "height": 4},
                ),
                DashboardWidget(
                    id="memory_usage",
                    title="Memory Usage",
                    chart_type=ChartType.LINE,
                    metric_name="memory_usage",
                    time_range="1h",
                    position={"x": 6, "y": 0, "width": 6, "height": 4},
                ),
                DashboardWidget(
                    id="request_rate",
                    title="Request Rate",
                    chart_type=ChartType.BAR,
                    metric_name="api_requests",
                    time_range="24h",
                    position={"x": 0, "y": 4, "width": 12, "height": 4},
                ),
            ],
            is_public=True,
        )

        self.templates["system_health"] = system_health

    def create_dashboard(
        self,
        user_id: int,
        name: str,
        description: str | None = None,
        template_id: str | None = None,
    ) -> Dashboard:
        """
        Create a new dashboard

        Args:
            user_id: User ID
            name: Dashboard name
            description: Optional description
            template_id: Optional template ID to clone

        Returns:
            Dashboard
        """
        dashboard_id = (
            f"dashboard_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        # Clone from template if provided
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            dashboard = Dashboard(
                id=dashboard_id,
                user_id=user_id,
                name=name,
                description=description or template.description,
                widgets=[
                    DashboardWidget(
                        id=f"{widget.id}_{dashboard_id}",
                        title=widget.title,
                        chart_type=widget.chart_type,
                        metric_name=widget.metric_name,
                        time_range=widget.time_range,
                        position=widget.position.copy(),
                        config=widget.config.copy(),
                    )
                    for widget in template.widgets
                ],
            )
        else:
            dashboard = Dashboard(
                id=dashboard_id,
                user_id=user_id,
                name=name,
                description=description,
            )

        self.dashboards[dashboard_id] = dashboard
        self.user_dashboards[user_id].append(dashboard_id)

        logger.info(f"Created dashboard {dashboard_id} for user {user_id}")

        return dashboard

    def add_widget(
        self,
        dashboard_id: str,
        widget: DashboardWidget,
    ) -> bool:
        """
        Add widget to dashboard

        Args:
            dashboard_id: Dashboard ID
            widget: Widget to add

        Returns:
            True if successful
        """
        if dashboard_id not in self.dashboards:
            return False

        dashboard = self.dashboards[dashboard_id]
        dashboard.widgets.append(widget)
        dashboard.updated_at = datetime.utcnow()

        logger.debug(f"Added widget {widget.id} to dashboard {dashboard_id}")

        return True

    def remove_widget(self, dashboard_id: str, widget_id: str) -> bool:
        """Remove widget from dashboard"""
        if dashboard_id not in self.dashboards:
            return False

        dashboard = self.dashboards[dashboard_id]
        original_count = len(dashboard.widgets)
        dashboard.widgets = [w for w in dashboard.widgets if w.id != widget_id]

        if len(dashboard.widgets) < original_count:
            dashboard.updated_at = datetime.utcnow()
            return True

        return False

    def update_widget(
        self,
        dashboard_id: str,
        widget_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """Update widget configuration"""
        if dashboard_id not in self.dashboards:
            return False

        dashboard = self.dashboards[dashboard_id]
        widget = next((w for w in dashboard.widgets if w.id == widget_id), None)

        if not widget:
            return False

        # Update widget properties
        for key, value in updates.items():
            if hasattr(widget, key):
                setattr(widget, key, value)

        dashboard.updated_at = datetime.utcnow()

        return True

    def get_dashboard(
        self, dashboard_id: str, user_id: int | None = None
    ) -> Dashboard | None:
        """Get dashboard by ID"""
        dashboard = self.dashboards.get(dashboard_id)

        if not dashboard:
            return None

        # Check access
        if user_id is not None:
            if dashboard.user_id != user_id and not dashboard.is_public:
                return None

        return dashboard

    def list_user_dashboards(self, user_id: int) -> list[Dashboard]:
        """List all dashboards for a user"""
        dashboard_ids = self.user_dashboards.get(user_id, [])
        return [self.dashboards[did] for did in dashboard_ids if did in self.dashboards]

    def list_public_dashboards(self) -> list[Dashboard]:
        """List all public dashboards"""
        return [
            dashboard for dashboard in self.dashboards.values() if dashboard.is_public
        ]

    def list_templates(self) -> list[Dashboard]:
        """List available templates"""
        return list(self.templates.values())

    def delete_dashboard(self, dashboard_id: str, user_id: int) -> bool:
        """Delete a dashboard"""
        dashboard = self.dashboards.get(dashboard_id)

        if not dashboard or dashboard.user_id != user_id:
            return False

        del self.dashboards[dashboard_id]

        if dashboard_id in self.user_dashboards[user_id]:
            self.user_dashboards[user_id].remove(dashboard_id)

        logger.info(f"Deleted dashboard {dashboard_id}")

        return True


# Global instance
custom_dashboards_service = CustomDashboardsService()
