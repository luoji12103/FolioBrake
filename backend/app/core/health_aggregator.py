def aggregate_health():
    from app.core.startup_check import check_database, check_redis
    db_ok = check_database()
    redis_ok = check_redis()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
