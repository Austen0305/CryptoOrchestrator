"""
Event System for Decoupled Communication
Provides pub/sub pattern for inter-service communication
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types"""

    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Bot events
    BOT_CREATED = "bot.created"
    BOT_UPDATED = "bot.updated"
    BOT_DELETED = "bot.deleted"
    BOT_STARTED = "bot.started"
    BOT_STOPPED = "bot.stopped"

    # Trade events
    TRADE_EXECUTED = "trade.executed"
    TRADE_FAILED = "trade.failed"
    TRADE_CANCELLED = "trade.cancelled"

    # Portfolio events
    PORTFOLIO_UPDATED = "portfolio.updated"
    BALANCE_CHANGED = "balance.changed"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    ERROR_OCCURRED = "error.occurred"


@dataclass
class Event:
    """Event data structure"""

    event_type: EventType
    payload: dict[str, Any]
    timestamp: datetime
    source: str
    event_id: str | None = None

    def __post_init__(self):
        if self.event_id is None:
            import uuid

            self.event_id = str(uuid.uuid4())
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


class EventBus:
    """
    Event bus for pub/sub pattern

    Features:
    - Type-safe event handling
    - Async event processing
    - Event filtering
    - Event history
    - Error handling
    """

    def __init__(self, max_history: int = 1000):
        self.subscribers: dict[EventType, list[Callable]] = defaultdict(list)
        self.event_history: list[Event] = []
        self.max_history = max_history
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type"""
        if handler not in self.subscribers[event_type]:
            self.subscribers[event_type].append(handler)
            logger.debug(f"Subscribed to {event_type}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from an event type"""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from {event_type}")

    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        async with self._lock:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)

            # Get subscribers
            handlers = self.subscribers.get(event.event_type, []).copy()

        # Notify subscribers asynchronously
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(self._safe_call(handler, event))
                else:
                    # Sync handler
                    asyncio.create_task(self._safe_call_sync(handler, event))
            except Exception as e:
                logger.error(f"Error creating task for handler: {e}")

        # Wait for all async handlers
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, handler: Callable, event: Event):
        """Safely call async handler"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Error in event handler {handler.__name__}: {e}", exc_info=True
            )

    async def _safe_call_sync(self, handler: Callable, event: Event):
        """Safely call sync handler"""
        try:
            handler(event)
        except Exception as e:
            logger.error(
                f"Error in sync event handler {handler.__name__}: {e}", exc_info=True
            )

    def get_history(
        self, event_type: EventType | None = None, limit: int = 100
    ) -> list[Event]:
        """Get event history"""
        events = self.event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get number of subscribers for event type"""
        return len(self.subscribers.get(event_type, []))


# Global event bus instance
event_bus = EventBus()


# Decorator for event handlers
def event_handler(event_type: EventType):
    """Decorator to register event handler"""

    def decorator(func: Callable):
        event_bus.subscribe(event_type, func)
        return func

    return decorator


# Helper functions
async def publish_event(
    event_type: EventType,
    payload: dict[str, Any],
    source: str = "system",
):
    """Helper to publish an event"""
    event = Event(
        event_type=event_type,
        payload=payload,
        timestamp=datetime.now(UTC),
        source=source,
    )
    await event_bus.publish(event)
