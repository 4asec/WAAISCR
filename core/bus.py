import asyncio
from typing import Any, Callable, Coroutine, Dict, List
from core.logger import get_logger

logger = get_logger("event_bus")

EventHandler = Callable[[Any], Coroutine[Any, Any, None]]

class EventBus:
    """Lightweight in-memory asynchronous event bus for decoupled communication."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register an async event handler for a given event topic."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)
        logger.debug(f"Subscribed handler '{handler.__name__}' to event '{event_name}'")

    async def publish(self, event_name: str, payload: Any = None) -> None:
        """Publish an event to all registered subscribers concurrently."""
        handlers = self._subscribers.get(event_name, [])
        if not handlers:
            logger.debug(f"No handlers registered for event '{event_name}'")
            return

        tasks = []
        for handler in handlers:
            tasks.append(self._safe_invoke(handler, event_name, payload))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_invoke(self, handler: EventHandler, event_name: str, payload: Any) -> None:
        try:
            await handler(payload)
        except Exception as e:
            logger.exception(f"Error handling event '{event_name}' in '{handler.__name__}': {e}")

# Global event bus singleton
bus = EventBus()
