from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["batch"])

class BatchRequest(BaseModel):
    operations: list[dict]

@router.post("/execute")
def execute_batch(req: BatchRequest, db: Session = Depends(get_db)):
    results = []
    for op in req.operations:
        op_type = op.get("type")
        if op_type == "health_check":
            results.append({"type": op_type, "status": "ok"})
        else:
            results.append({"type": op_type, "error": "Unknown operation"})
    return {"results": results, "total": len(results)}
