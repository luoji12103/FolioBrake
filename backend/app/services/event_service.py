import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable):
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def emit(self, event: str, data: dict = None):
        logger.info(f"Event: {event}")
        for handler in self._handlers.get(event, []):
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
