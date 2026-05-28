from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.base import get_db

router = APIRouter(tags=["batch"])

MAX_BATCH_OPERATIONS = 20
VALID_OPERATION_TYPES = {"health_check"}


class BatchOperation(BaseModel):
    type: str = Field(..., max_length=64)


class BatchRequest(BaseModel):
    operations: list[BatchOperation] = Field(..., min_length=1, max_length=MAX_BATCH_OPERATIONS)


@router.post("/execute")
def execute_batch(req: BatchRequest, db: Session = Depends(get_db)):
    results = []
    for op in req.operations:
        if op.type not in VALID_OPERATION_TYPES:
            results.append({"type": op.type, "error": "Unknown operation"})
        else:
            results.append({"type": op.type, "status": "ok"})
    return {"results": results, "total": len(results)}
