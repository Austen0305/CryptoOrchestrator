from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """Base class for all system events."""

    event_name: str
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None


class EventBus:
    """
    Asynchronous, in-memory event bus for local service decoupling.
    Uses strict typing and asyncio for non-blocking dispatch.
    """

    def __init__(self):
        self._subscribers: dict[
            str, list[Callable[[Event], Coroutine[Any, Any, None]]]
        ] = defaultdict(list)
        self._background_tasks: set[asyncio.Task] = set()

    def subscribe(
        self,
        event_type: type[Event],
        handler: Callable[[Event], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Register an async handler for a specific event type.
        """
        event_name = event_type.model_fields["event_name"].default
        if not event_name:
            # Fallback to class name if no default event_name is set,
            # though explicit field is preferred for serialization clarity.
            event_name = event_type.__name__

        self._subscribers[event_name].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_name}")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        FIRE-AND-FORGET: This method does NOT wait for handlers to finish.
        It schedules them as tasks to ensure the publisher is not blocked.
        """
        event_name = event.event_name
        if not event_name:
            event_name = event.__class__.__name__

        handlers = self._subscribers.get(event_name, [])

        if not handlers:
            logger.debug(f"No handlers for event: {event_name}")
            return

        # Fire and forget pattern using asyncio.create_task
        # We wrap in a safe executor to catch exceptions within the handler
        for handler in handlers:
            task = asyncio.create_task(self._safe_execute_handler(handler, event))
            # Prevent garbage collection before completion
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def _safe_execute_handler(
        self, handler: Callable[[Event], Coroutine[Any, Any, None]], event: Event
    ) -> None:
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Error handling event {event.event_name} in {handler.__name__}: {e}",
                exc_info=True,
            )


# Global singleton available for DI
bus = EventBus()
