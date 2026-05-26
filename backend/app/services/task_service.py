import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class TaskService:
    def __init__(self):
        self._tasks = {}
    
    def register_task(self, name: str, handler: Callable):
        self._tasks[name] = handler
        logger.info(f"Registered task: {name}")
    
    def execute_task(self, name: str, params: dict = None) -> Any:
        if name in self._tasks:
            logger.info(f"Executing task: {name}")
            return self._tasks[name](params or {})
        logger.warning(f"Task not found: {name}")
        return None
