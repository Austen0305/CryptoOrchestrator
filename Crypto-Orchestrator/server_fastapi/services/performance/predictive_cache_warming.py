"""
Predictive Cache Warming Service
Warm cache based on user patterns and predicted requests
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class UserPattern:
    """User access pattern"""
    user_id: int
    endpoint: str
    frequency: float  # Requests per hour
    time_of_day: List[int]  # Hours when accessed (0-23)
    day_of_week: List[int]  # Days when accessed (0-6, Monday=0)
    last_accessed: datetime
    access_count: int = 0


@dataclass
class CacheWarmupTask:
    """Cache warmup task"""
    endpoint: str
    parameters: Dict[str, Any]
    priority: int  # 1-10, higher = more important
    predicted_time: datetime
    user_id: Optional[int] = None


class PredictiveCacheWarmingService:
    """
    Predictive cache warming service
    
    Features:
    - User pattern learning
    - Request prediction
    - Automatic cache warming
    - Priority-based warmup
    """
    
    def __init__(self, cache_service=None):
        """
        Initialize predictive cache warming service
        
        Args:
            cache_service: Cache service instance for warming
        """
        self.cache_service = cache_service
        self.user_patterns: Dict[int, Dict[str, UserPattern]] = defaultdict(dict)
        self.access_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.warmup_tasks: List[CacheWarmupTask] = []
        self.enabled = True
    
    def record_access(
        self,
        user_id: int,
        endpoint: str,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """
        Record user access for pattern learning
        
        Args:
            user_id: User ID
            endpoint: API endpoint accessed
            parameters: Optional request parameters
        """
        if not self.enabled:
            return
        
        timestamp = datetime.utcnow()
        
        # Record in history
        self.access_history[user_id].append({
            "endpoint": endpoint,
            "parameters": parameters or {},
            "timestamp": timestamp,
            "hour": timestamp.hour,
            "day_of_week": timestamp.weekday(),
        })
        
        # Update pattern
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {}
        
        if endpoint not in self.user_patterns[user_id]:
            pattern = UserPattern(
                user_id=user_id,
                endpoint=endpoint,
                frequency=0.0,
                time_of_day=[],
                day_of_week=[],
                last_accessed=timestamp,
            )
            self.user_patterns[user_id][endpoint] = pattern
        else:
            pattern = self.user_patterns[user_id][endpoint]
        
        pattern.access_count += 1
        pattern.last_accessed = timestamp
        
        # Update frequency (requests per hour)
        recent_accesses = [
            a for a in self.access_history[user_id]
            if a["timestamp"] >= timestamp - timedelta(hours=24)
        ]
        pattern.frequency = len(recent_accesses) / 24.0
        
        # Update time patterns
        hours = [a["hour"] for a in recent_accesses]
        if hours:
            # Most common hours
            hour_counts = defaultdict(int)
            for h in hours:
                hour_counts[h] += 1
            pattern.time_of_day = sorted(
                hour_counts.keys(),
                key=lambda h: hour_counts[h],
                reverse=True
            )[:6]  # Top 6 hours
        
        # Update day patterns
        days = [a["day_of_week"] for a in recent_accesses]
        if days:
            day_counts = defaultdict(int)
            for d in days:
                day_counts[d] += 1
            pattern.day_of_week = sorted(
                day_counts.keys(),
                key=lambda d: day_counts[d],
                reverse=True
            )
    
    def predict_next_access(
        self,
        user_id: int,
        endpoint: Optional[str] = None,
    ) -> List[CacheWarmupTask]:
        """
        Predict next accesses and create warmup tasks
        
        Args:
            user_id: User ID
            endpoint: Optional specific endpoint to predict
        
        Returns:
            List of cache warmup tasks
        """
        if not self.enabled:
            return []
        
        tasks = []
        now = datetime.utcnow()
        current_hour = now.hour
        current_day = now.weekday()
        
        if user_id not in self.user_patterns:
            return []
        
        patterns = self.user_patterns[user_id]
        
        # Filter by endpoint if specified
        if endpoint:
            patterns = {endpoint: patterns.get(endpoint)} if endpoint in patterns else {}
        
        for ep, pattern in patterns.items():
            if not pattern:
                continue
            
            # Check if user typically accesses this endpoint at this time
            should_warm = False
            
            # Check time of day pattern
            if pattern.time_of_day:
                # Check if current hour is in pattern (with 1-hour window)
                for preferred_hour in pattern.time_of_day:
                    if abs(current_hour - preferred_hour) <= 1:
                        should_warm = True
                        break
            else:
                # No time pattern, warm if recently accessed
                if (now - pattern.last_accessed).total_seconds() < 3600:  # Within last hour
                    should_warm = True
            
            # Check day of week pattern
            if pattern.day_of_week and current_day not in pattern.day_of_week:
                should_warm = False  # Not a typical day
            
            if should_warm and pattern.frequency > 0.1:  # At least 0.1 requests/hour
                # Predict next access time (based on frequency)
                hours_until_next = 1.0 / pattern.frequency if pattern.frequency > 0 else 1.0
                predicted_time = now + timedelta(hours=hours_until_next)
                
                task = CacheWarmupTask(
                    endpoint=ep,
                    parameters={},  # Would use most common parameters
                    priority=int(pattern.frequency * 10),  # Scale frequency to 1-10
                    predicted_time=predicted_time,
                    user_id=user_id,
                )
                
                tasks.append(task)
        
        # Sort by priority
        tasks.sort(key=lambda t: t.priority, reverse=True)
        
        return tasks
    
    def warm_cache_for_user(self, user_id: int):
        """
        Warm cache for a user based on predicted accesses
        
        Args:
            user_id: User ID
        """
        if not self.enabled or not self.cache_service:
            return
        
        tasks = self.predict_next_access(user_id)
        
        for task in tasks[:10]:  # Limit to top 10 tasks
            try:
                # Generate cache key
                cache_key = f"{task.endpoint}:{user_id}:{task.parameters}"
                
                # Check if already cached
                if self.cache_service.get(cache_key):
                    continue
                
                # In production, would make actual API call to warm cache
                # For now, just log
                logger.debug(
                    f"Warming cache for user {user_id}, endpoint {task.endpoint}, "
                    f"predicted at {task.predicted_time}"
                )
            except Exception as e:
                logger.error(f"Error warming cache: {e}", exc_info=True)
    
    def get_user_patterns(self, user_id: int) -> Dict[str, UserPattern]:
        """Get patterns for a user"""
        return self.user_patterns.get(user_id, {})
    
    def get_warmup_statistics(self) -> Dict[str, Any]:
        """Get warmup statistics"""
        total_patterns = sum(len(patterns) for patterns in self.user_patterns.values())
        total_users = len(self.user_patterns)
        
        return {
            "total_users": total_users,
            "total_patterns": total_patterns,
            "average_patterns_per_user": (
                total_patterns / total_users if total_users > 0 else 0
            ),
            "warmup_tasks_queued": len(self.warmup_tasks),
        }


# Global instance (will be initialized with cache service)
predictive_cache_warming_service = None

def initialize_predictive_cache_warming(cache_service):
    """Initialize predictive cache warming with cache service"""
    global predictive_cache_warming_service
    predictive_cache_warming_service = PredictiveCacheWarmingService(cache_service)
    return predictive_cache_warming_service
