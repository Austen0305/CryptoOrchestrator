"""
SLA Service
Calculates and tracks Service Level Agreements (SLAs)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SLAType(Enum):
    """SLA type"""

    AVAILABILITY = "availability"  # Uptime percentage
    LATENCY = "latency"  # Response time (p95, p99)
    ERROR_RATE = "error_rate"  # Error percentage
    THROUGHPUT = "throughput"  # Requests per second


@dataclass
class SLATarget:
    """SLA target configuration"""

    name: str
    sla_type: SLAType
    target_value: float  # e.g., 99.99 for availability, 50.0 for latency (ms)
    measurement_window_minutes: int = 60
    enabled: bool = True
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class SLAMetric:
    """SLA metric measurement"""

    sla_name: str
    sla_type: SLAType
    target_value: float
    current_value: float
    compliance_percentage: float  # How close to target (0-100)
    is_compliant: bool
    measurement_window_start: datetime
    measurement_window_end: datetime
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)


class SLAService:
    """
    Service Level Agreement (SLA) tracking service

    Features:
    - Availability tracking (uptime %)
    - Latency tracking (p95, p99)
    - Error rate tracking
    - Throughput tracking
    - Compliance calculation
    - SLA violation detection
    """

    def __init__(self):
        self.sla_targets: dict[str, SLATarget] = {}
        self.sla_metrics: list[SLAMetric] = []
        self.availability_data: dict[str, list[tuple]] = {}  # (timestamp, is_up)
        self.latency_data: dict[str, list[float]] = {}
        self.error_data: dict[str, list[tuple]] = {}  # (timestamp, is_error)
        self.throughput_data: dict[str, list[tuple]] = {}  # (timestamp, requests)
        self.max_history = 1000

    def register_sla(self, sla_target: SLATarget):
        """Register an SLA target"""
        self.sla_targets[sla_target.name] = sla_target
        logger.info(f"Registered SLA: {sla_target.name} ({sla_target.sla_type.value})")

    def record_availability(
        self, service_name: str, is_up: bool, tags: dict[str, str] | None = None
    ):
        """Record availability status"""
        key = self._make_key(service_name, tags)
        if key not in self.availability_data:
            self.availability_data[key] = []

        self.availability_data[key].append((datetime.utcnow(), is_up))

        # Keep only recent data
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.availability_data[key] = [
            (t, up) for t, up in self.availability_data[key] if t >= cutoff
        ]

    def record_latency(
        self, service_name: str, latency_ms: float, tags: dict[str, str] | None = None
    ):
        """Record latency measurement"""
        key = self._make_key(service_name, tags)
        if key not in self.latency_data:
            self.latency_data[key] = []

        self.latency_data[key].append(latency_ms)

        # Keep only last 10000 measurements
        if len(self.latency_data[key]) > 10000:
            self.latency_data[key] = self.latency_data[key][-10000:]

    def record_error(
        self, service_name: str, is_error: bool, tags: dict[str, str] | None = None
    ):
        """Record error occurrence"""
        key = self._make_key(service_name, tags)
        if key not in self.error_data:
            self.error_data[key] = []

        self.error_data[key].append((datetime.utcnow(), is_error))

        # Keep only recent data
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.error_data[key] = [
            (t, err) for t, err in self.error_data[key] if t >= cutoff
        ]

    def record_throughput(
        self, service_name: str, requests: int, tags: dict[str, str] | None = None
    ):
        """Record throughput measurement"""
        key = self._make_key(service_name, tags)
        if key not in self.throughput_data:
            self.throughput_data[key] = []

        self.throughput_data[key].append((datetime.utcnow(), requests))

        # Keep only recent data
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.throughput_data[key] = [
            (t, req) for t, req in self.throughput_data[key] if t >= cutoff
        ]

    def calculate_sla(self, sla_name: str) -> SLAMetric | None:
        """Calculate current SLA compliance"""
        if sla_name not in self.sla_targets:
            return None

        sla_target = self.sla_targets[sla_name]
        if not sla_target.enabled:
            return None

        key = self._make_key(sla_name, sla_target.tags)
        window_start = datetime.utcnow() - timedelta(
            minutes=sla_target.measurement_window_minutes
        )
        window_end = datetime.utcnow()

        current_value = 0.0
        is_compliant = False
        compliance_percentage = 0.0

        if sla_target.sla_type == SLAType.AVAILABILITY:
            # Calculate uptime percentage
            if key in self.availability_data:
                recent_data = [
                    (t, up)
                    for t, up in self.availability_data[key]
                    if window_start <= t <= window_end
                ]
                if recent_data:
                    uptime_count = sum(1 for _, up in recent_data if up)
                    total_count = len(recent_data)
                    current_value = (
                        (uptime_count / total_count * 100) if total_count > 0 else 100.0
                    )
                else:
                    current_value = 100.0  # No data = assume up
            else:
                current_value = 100.0  # No data = assume up

            is_compliant = current_value >= sla_target.target_value
            compliance_percentage = (
                min(100.0, (current_value / sla_target.target_value) * 100)
                if sla_target.target_value > 0
                else 100.0
            )

        elif sla_target.sla_type == SLAType.LATENCY:
            # Calculate p95 latency
            if key in self.latency_data:
                recent_latencies = self.latency_data[key][
                    -1000:
                ]  # Last 1000 measurements
                if recent_latencies:
                    sorted_latencies = sorted(recent_latencies)
                    p95_index = int(len(sorted_latencies) * 0.95)
                    current_value = (
                        sorted_latencies[p95_index]
                        if p95_index < len(sorted_latencies)
                        else sorted_latencies[-1]
                    )
                else:
                    current_value = 0.0
            else:
                current_value = 0.0

            is_compliant = current_value <= sla_target.target_value
            compliance_percentage = (
                min(100.0, (sla_target.target_value / current_value) * 100)
                if current_value > 0
                else 100.0
            )

        elif sla_target.sla_type == SLAType.ERROR_RATE:
            # Calculate error rate percentage
            if key in self.error_data:
                recent_data = [
                    (t, err)
                    for t, err in self.error_data[key]
                    if window_start <= t <= window_end
                ]
                if recent_data:
                    error_count = sum(1 for _, err in recent_data if err)
                    total_count = len(recent_data)
                    current_value = (
                        (error_count / total_count * 100) if total_count > 0 else 0.0
                    )
                else:
                    current_value = 0.0
            else:
                current_value = 0.0

            is_compliant = current_value <= sla_target.target_value
            compliance_percentage = (
                min(100.0, (sla_target.target_value / current_value) * 100)
                if current_value > 0
                else 100.0
            )

        elif sla_target.sla_type == SLAType.THROUGHPUT:
            # Calculate average throughput
            if key in self.throughput_data:
                recent_data = [
                    (t, req)
                    for t, req in self.throughput_data[key]
                    if window_start <= t <= window_end
                ]
                if recent_data:
                    total_requests = sum(req for _, req in recent_data)
                    time_span_minutes = (window_end - window_start).total_seconds() / 60
                    current_value = (
                        (total_requests / time_span_minutes * 60)
                        if time_span_minutes > 0
                        else 0.0
                    )  # req/sec
                else:
                    current_value = 0.0
            else:
                current_value = 0.0

            is_compliant = current_value >= sla_target.target_value
            compliance_percentage = (
                min(100.0, (current_value / sla_target.target_value) * 100)
                if sla_target.target_value > 0
                else 0.0
            )

        sla_metric = SLAMetric(
            sla_name=sla_name,
            sla_type=sla_target.sla_type,
            target_value=sla_target.target_value,
            current_value=current_value,
            compliance_percentage=compliance_percentage,
            is_compliant=is_compliant,
            measurement_window_start=window_start,
            measurement_window_end=window_end,
            timestamp=datetime.utcnow(),
            tags=sla_target.tags,
        )

        self.sla_metrics.append(sla_metric)
        if len(self.sla_metrics) > self.max_history:
            self.sla_metrics = self.sla_metrics[-self.max_history :]

        return sla_metric

    def get_all_slas(self) -> list[SLAMetric]:
        """Calculate and return all SLA metrics"""
        results = []
        for sla_name in self.sla_targets.keys():
            metric = self.calculate_sla(sla_name)
            if metric:
                results.append(metric)
        return results

    def get_sla_summary(self) -> dict[str, Any]:
        """Get SLA summary statistics"""
        all_metrics = self.get_all_slas()

        total_slas = len(all_metrics)
        compliant_slas = sum(1 for m in all_metrics if m.is_compliant)
        non_compliant_slas = total_slas - compliant_slas

        avg_compliance = (
            sum(m.compliance_percentage for m in all_metrics) / total_slas
            if total_slas > 0
            else 100.0
        )

        return {
            "total_slas": total_slas,
            "compliant_slas": compliant_slas,
            "non_compliant_slas": non_compliant_slas,
            "compliance_rate": (compliant_slas / total_slas * 100)
            if total_slas > 0
            else 100.0,
            "average_compliance_percentage": avg_compliance,
            "sla_metrics": [
                {
                    "name": m.sla_name,
                    "type": m.sla_type.value,
                    "target": m.target_value,
                    "current": m.current_value,
                    "compliant": m.is_compliant,
                    "compliance_percentage": m.compliance_percentage,
                }
                for m in all_metrics
            ],
        }

    def _make_key(self, name: str, tags: dict[str, str] | None) -> str:
        """Create a key from name and tags"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"


# Global instance
sla_service = SLAService()
