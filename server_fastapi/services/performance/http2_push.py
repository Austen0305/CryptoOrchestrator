"""
HTTP/2 Server Push Service
Server push for preloading resources and query results
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class PushResource:
    """Resource to push via HTTP/2"""
    path: str
    content_type: str
    priority: int  # 1-256, lower = higher priority
    push_promise: bool = True


class HTTP2PushService:
    """
    HTTP/2 Server Push service
    
    Features:
    - Resource preloading
    - Query result prefetching
    - Priority-based pushing
    - Push promise management
    """
    
    def __init__(self):
        self.push_resources: Dict[str, List[PushResource]] = {}
        self.push_history: deque = deque(maxlen=1000)
        self.enabled = True
    
    def add_push_resource(
        self,
        endpoint: str,
        resource_path: str,
        content_type: str = "application/json",
        priority: int = 100,
    ):
        """
        Add a resource to push for an endpoint
        
        Args:
            endpoint: API endpoint that should trigger push
            resource_path: Path to resource to push
            content_type: Content type of resource
            priority: Push priority (1-256, lower = higher priority)
        """
        if endpoint not in self.push_resources:
            self.push_resources[endpoint] = []
        
        resource = PushResource(
            path=resource_path,
            content_type=content_type,
            priority=priority,
        )
        
        self.push_resources[endpoint].append(resource)
        self.push_resources[endpoint].sort(key=lambda r: r.priority)
        
        logger.debug(f"Added push resource {resource_path} for endpoint {endpoint}")
    
    def get_push_resources(self, endpoint: str) -> List[PushResource]:
        """
        Get resources to push for an endpoint
        
        Args:
            endpoint: API endpoint
        
        Returns:
            List of resources to push
        """
        return self.push_resources.get(endpoint, [])
    
    def record_push(
        self,
        endpoint: str,
        resource_path: str,
        success: bool,
    ):
        """Record a push attempt"""
        self.push_history.append({
            "endpoint": endpoint,
            "resource_path": resource_path,
            "success": success,
            "timestamp": datetime.utcnow(),
        })
    
    def get_push_statistics(self) -> Dict[str, Any]:
        """Get push statistics"""
        if not self.push_history:
            return {
                "total_pushes": 0,
                "successful_pushes": 0,
                "failed_pushes": 0,
                "success_rate": 0.0,
            }
        
        total = len(self.push_history)
        successful = sum(1 for p in self.push_history if p["success"])
        failed = total - successful
        
        return {
            "total_pushes": total,
            "successful_pushes": successful,
            "failed_pushes": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0.0,
        }
    
    def configure_endpoint_push(
        self,
        endpoint: str,
        related_endpoints: List[str],
    ):
        """
        Configure push resources for related endpoints
        
        Args:
            endpoint: Main endpoint
            related_endpoints: List of related endpoints to push
        """
        for related in related_endpoints:
            self.add_push_resource(
                endpoint=endpoint,
                resource_path=related,
                content_type="application/json",
                priority=100,
            )


# Global instance
http2_push_service = HTTP2PushService()
