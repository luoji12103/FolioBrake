from fastapi import FastAPI

from app.api.data import router as data_router

app = FastAPI(title="Retail ETF Guardian API", version="0.1.0")

app.include_router(data_router, prefix="/data", tags=["data"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}
