import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def schedule_task(self, task_type: str, schedule: str):
        logger.info(f"Scheduling task {task_type} at {schedule}")
        return {"task_id": 0, "status": "scheduled"}
    
    def get_scheduled_tasks(self):
        logger.info("Getting scheduled tasks")
        return []
