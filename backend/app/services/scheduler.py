import logging
from typing import Callable, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self._jobs: Dict[str, dict] = {}
    
    def schedule(self, name: str, func: Callable, interval_seconds: int):
        self._jobs[name] = {"func": func, "interval": interval_seconds, "last_run": None}
        logger.info(f"Scheduled job: {name} every {interval_seconds}s")
    
    def run_pending(self):
        now = datetime.now()
        for name, job in self._jobs.items():
            if job["last_run"] is None or (now - job["last_run"]).total_seconds() >= job["interval"]:
                try:
                    job["func"]()
                    job["last_run"] = now
                except Exception as e:
                    logger.error(f"Job {name} failed: {e}")
