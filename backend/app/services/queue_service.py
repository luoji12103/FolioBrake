import logging
from typing import Any, List
from collections import deque

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(self):
        self._queue = deque()
    
    def enqueue(self, item: Any):
        self._queue.append(item)
        logger.info(f"Enqueued: {len(self._queue)} items")
    
    def dequeue(self) -> Any:
        if self._queue:
            return self._queue.popleft()
        return None
    
    def size(self) -> int:
        return len(self._queue)
