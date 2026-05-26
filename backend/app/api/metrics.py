from fastapi import APIRouter
import time

router = APIRouter(tags=["metrics"])

start_time = time.time()

@router.get("/metrics")
def get_metrics():
    uptime = time.time() - start_time
    return {
        "uptime_seconds": int(uptime),
        "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
        "status": "healthy"
    }
