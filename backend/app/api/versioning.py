from fastapi import APIRouter

router = APIRouter(tags=["versioning"])

@router.get("/version")
def get_version():
    return {
        "version": "0.2.0",
        "api_version": "v1",
        "build": "latest"
    }

@router.get("/versions")
def list_versions():
    return {
        "versions": [
            {"version": "v1", "status": "current", "release_date": "2026-05-01"},
        ]
    }
