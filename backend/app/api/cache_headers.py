from fastapi import APIRouter

router = APIRouter(tags=["cache"])

@router.get("/cache/test")
def test_cache():
    return {"cached": True, "ttl": 300}
