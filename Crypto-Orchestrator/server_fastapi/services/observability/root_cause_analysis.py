"""
Root Cause Analysis Service
Automated root cause identification for incidents
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Incident:
    """Incident record"""
    id: str
    title: str
    description: str
    severity: str
    start_time: datetime
    end_time: Optional[datetime] = None
    affected_services: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    root_cause: Optional[str] = None
    confidence: float = 0.0


@dataclass
class Correlation:
    """Correlation between metrics/events"""
    metric_a: str
    metric_b: str
    correlation_score: float  # -1 to 1
    time_window_minutes: int


class RootCauseAnalysisService:
    """
    Root cause analysis service
    
    Features:
    - Incident correlation
    - Dependency mapping
    - Metric correlation analysis
    - Automated root cause identification
    - Service dependency tracking
    """
    
    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self.correlations: List[Correlation] = []
        self.service_dependencies: Dict[str, List[str]] = {
            "api": ["database", "redis", "external_apis"],
            "database": [],
            "redis": [],
            "external_apis": [],
        }
        self.metric_history: Dict[str, List[tuple]] = defaultdict(list)  # (timestamp, value)
    
    def create_incident(
        self,
        title: str,
        description: str,
        severity: str,
        affected_services: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Incident:
        """
        Create an incident record
        
        Args:
            title: Incident title
            description: Incident description
            severity: Severity level
            affected_services: List of affected services
            metrics: Related metrics
        
        Returns:
            Incident
        """
        incident_id = f"inc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            start_time=datetime.utcnow(),
            affected_services=affected_services or [],
            metrics=metrics or {},
        )
        
        self.incidents[incident_id] = incident
        
        # Analyze root cause
        self._analyze_root_cause(incident)
        
        logger.info(f"Created incident {incident_id}: {title}")
        
        return incident
    
    def _analyze_root_cause(self, incident: Incident):
        """Analyze root cause for an incident"""
        # Check service dependencies
        root_causes = []
        
        for service in incident.affected_services:
            dependencies = self.service_dependencies.get(service, [])
            
            # Check if dependencies had issues
            for dep in dependencies:
                # Check for recent incidents affecting dependencies
                recent_incidents = [
                    inc for inc in self.incidents.values()
                    if dep in inc.affected_services
                    and inc.start_time >= incident.start_time - timedelta(minutes=30)
                    and inc.id != incident.id
                ]
                
                if recent_incidents:
                    root_causes.append({
                        "type": "dependency_failure",
                        "service": service,
                        "dependency": dep,
                        "related_incidents": [inc.id for inc in recent_incidents],
                        "confidence": 0.8,
                    })
        
        # Check metric correlations
        if incident.metrics:
            for metric_name, metric_value in incident.metrics.items():
                # Find correlated metrics
                correlations = [
                    c for c in self.correlations
                    if c.metric_a == metric_name or c.metric_b == metric_name
                ]
                
                for corr in correlations:
                    other_metric = (
                        corr.metric_b if corr.metric_a == metric_name else corr.metric_a
                    )
                    
                    # Check if other metric had anomalies
                    if other_metric in self.metric_history:
                        recent_values = [
                            v for t, v in self.metric_history[other_metric]
                            if t >= incident.start_time - timedelta(minutes=30)
                        ]
                        
                        if recent_values:
                            avg_value = sum(recent_values) / len(recent_values)
                            # Check for anomalies (simplified)
                            if abs(metric_value - avg_value) > avg_value * 0.5:
                                root_causes.append({
                                    "type": "metric_correlation",
                                    "metric": metric_name,
                                    "correlated_metric": other_metric,
                                    "correlation_score": corr.correlation_score,
                                    "confidence": abs(corr.correlation_score) * 0.7,
                                })
        
        # Select best root cause
        if root_causes:
            best_cause = max(root_causes, key=lambda c: c.get("confidence", 0.0))
            incident.root_cause = best_cause.get("type", "unknown")
            incident.confidence = best_cause.get("confidence", 0.0)
        else:
            incident.root_cause = "unknown"
            incident.confidence = 0.0
    
    def add_correlation(
        self,
        metric_a: str,
        metric_b: str,
        correlation_score: float,
        time_window_minutes: int = 60,
    ):
        """Add metric correlation"""
        correlation = Correlation(
            metric_a=metric_a,
            metric_b=metric_b,
            correlation_score=correlation_score,
            time_window_minutes=time_window_minutes,
        )
        
        self.correlations.append(correlation)
        logger.debug(f"Added correlation: {metric_a} <-> {metric_b} ({correlation_score:.2f})")
    
    def record_metric(self, metric_name: str, value: float):
        """Record metric value for analysis"""
        self.metric_history[metric_name].append((datetime.utcnow(), value))
        
        # Keep only last 1000 values
        if len(self.metric_history[metric_name]) > 1000:
            self.metric_history[metric_name] = self.metric_history[metric_name][-1000:]
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get an incident by ID"""
        return self.incidents.get(incident_id)
    
    def get_recent_incidents(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
    ) -> List[Incident]:
        """Get recent incidents"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        incidents = [
            inc for inc in self.incidents.values()
            if inc.start_time >= cutoff
        ]
        
        if severity:
            incidents = [inc for inc in incidents if inc.severity == severity]
        
        return sorted(incidents, key=lambda i: i.start_time, reverse=True)
    
    def resolve_incident(self, incident_id: str):
        """Resolve an incident"""
        if incident_id in self.incidents:
            self.incidents[incident_id].end_time = datetime.utcnow()
            logger.info(f"Resolved incident {incident_id}")
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary"""
        total_incidents = len(self.incidents)
        resolved_incidents = sum(
            1 for inc in self.incidents.values() if inc.end_time is not None
        )
        active_incidents = total_incidents - resolved_incidents
        
        root_cause_types = defaultdict(int)
        for inc in self.incidents.values():
            if inc.root_cause:
                root_cause_types[inc.root_cause] += 1
        
        return {
            "total_incidents": total_incidents,
            "active_incidents": active_incidents,
            "resolved_incidents": resolved_incidents,
            "root_cause_distribution": dict(root_cause_types),
            "correlations_count": len(self.correlations),
        }


# Global instance
root_cause_analysis_service = RootCauseAnalysisService()
