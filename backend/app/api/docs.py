from fastapi import APIRouter

router = APIRouter(tags=["docs"])

@router.get("/endpoints")
def list_endpoints():
    return {
        "endpoints": [
            {"path": "/api/health", "method": "GET", "description": "Health check"},
            {"path": "/api/data/instruments", "method": "GET", "description": "List instruments"},
            {"path": "/api/strategy/signals", "method": "GET", "description": "Get signals"},
        ]
    }
