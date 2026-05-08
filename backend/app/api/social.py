from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func as sql_func

from app.db.base import get_db
from app.auth.security import verify_token
from app.auth.models import User
from app.social.models import (
    SharedStrategy,
    StrategyPerformanceSnapshot,
    StrategyComment,
    StrategyLike,
    StrategyFork,
)
from app.strategy.models import StrategyConfig

router = APIRouter(tags=["social"])


def _get_optional_user(
    authorization: str | None = None,
    db: Session | None = None,
) -> User | None:
    if not authorization or not authorization.startswith("Bearer ") or db is None:
        return None
    from app.auth.security import verify_token
    payload = verify_token(authorization[7:])
    if not payload:
        return None
    return db.execute(select(User).where(User.id == payload["sub"])).scalar_one_or_none()


class ShareStrategyRequest(BaseModel):
    strategy_config_id: int
    title: str
    description: str | None = None
    tags: list[str] = []
    is_public: bool = True


class AddCommentRequest(BaseModel):
    content: str


class AddPerformanceRequest(BaseModel):
    snapshot_date: str
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    trade_count: int = 0
    extra_metrics: dict = {}


@router.post("/share")
def share_strategy(
    req: ShareStrategyRequest,
    authorization: str = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required to share strategies")

    config = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == req.strategy_config_id)
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Strategy config not found")

    shared = SharedStrategy(
        user_id=user.id,
        strategy_config_id=req.strategy_config_id,
        title=req.title,
        description=req.description,
        tags=req.tags,
        is_public=req.is_public,
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)

    return {
        "shared_strategy_id": shared.id,
        "title": shared.title,
        "is_public": shared.is_public,
    }


@router.get("/strategies")
def list_shared_strategies(
    tag: str | None = None,
    user_id: int | None = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = select(SharedStrategy).where(SharedStrategy.is_public == True)
    if tag:
        query = query.where(SharedStrategy.tags.contains([tag]))
    if user_id:
        query = query.where(SharedStrategy.user_id == user_id)
    query = query.order_by(desc(SharedStrategy.created_at)).offset(offset).limit(limit)

    strategies = list(db.execute(query).scalars().all())
    results = []
    for s in strategies:
        like_count = db.execute(
            select(sql_func.count()).select_from(StrategyLike).where(
                StrategyLike.shared_strategy_id == s.id
            )
        ).scalar() or 0
        comment_count = db.execute(
            select(sql_func.count()).select_from(StrategyComment).where(
                StrategyComment.shared_strategy_id == s.id
            )
        ).scalar() or 0

        results.append({
            "id": s.id,
            "user_id": s.user_id,
            "title": s.title,
            "description": s.description,
            "tags": s.tags,
            "view_count": s.view_count,
            "fork_count": s.fork_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "created_at": str(s.created_at),
        })

    return results


@router.get("/strategies/{strategy_id}")
def get_shared_strategy(strategy_id: int, db: Session = Depends(get_db)):
    shared = db.execute(
        select(SharedStrategy).where(SharedStrategy.id == strategy_id)
    ).scalar_one_or_none()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared strategy not found")

    shared.view_count += 1
    db.commit()

    config = db.execute(
        select(StrategyConfig).where(StrategyConfig.id == shared.strategy_config_id)
    ).scalar_one_or_none()

    snapshots = list(
        db.execute(
            select(StrategyPerformanceSnapshot)
            .where(StrategyPerformanceSnapshot.shared_strategy_id == strategy_id)
            .order_by(StrategyPerformanceSnapshot.snapshot_date)
        ).scalars().all()
    )

    return {
        "id": shared.id,
        "user_id": shared.user_id,
        "title": shared.title,
        "description": shared.description,
        "tags": shared.tags,
        "is_public": shared.is_public,
        "view_count": shared.view_count,
        "fork_count": shared.fork_count,
        "strategy_config": {
            "name": config.name if config else None,
            "parameters": config.parameters if config else {},
        },
        "performance_snapshots": [
            {
                "date": s.snapshot_date,
                "total_return": s.total_return,
                "sharpe_ratio": s.sharpe_ratio,
                "max_drawdown": s.max_drawdown,
                "win_rate": s.win_rate,
            }
            for s in snapshots
        ],
        "created_at": str(shared.created_at),
    }


@router.post("/strategies/{strategy_id}/performance")
def add_performance_snapshot(
    strategy_id: int,
    req: AddPerformanceRequest,
    authorization: str = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    shared = db.execute(
        select(SharedStrategy).where(SharedStrategy.id == strategy_id)
    ).scalar_one_or_none()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared strategy not found")
    if shared.user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can add performance data")

    snapshot = StrategyPerformanceSnapshot(
        shared_strategy_id=strategy_id,
        snapshot_date=req.snapshot_date,
        total_return=req.total_return,
        sharpe_ratio=req.sharpe_ratio,
        max_drawdown=req.max_drawdown,
        win_rate=req.win_rate,
        trade_count=req.trade_count,
        extra_metrics=req.extra_metrics,
    )
    db.add(snapshot)
    db.commit()

    return {"snapshot_id": snapshot.id, "date": snapshot.snapshot_date}


@router.post("/strategies/{strategy_id}/like")
def like_strategy(
    strategy_id: int,
    authorization: str = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    existing = db.execute(
        select(StrategyLike).where(
            StrategyLike.shared_strategy_id == strategy_id,
            StrategyLike.user_id == user.id,
        )
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "unliked", "strategy_id": strategy_id}

    like = StrategyLike(shared_strategy_id=strategy_id, user_id=user.id)
    db.add(like)
    db.commit()
    return {"action": "liked", "strategy_id": strategy_id}


@router.post("/strategies/{strategy_id}/comment")
def add_comment(
    strategy_id: int,
    req: AddCommentRequest,
    authorization: str = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    shared = db.execute(
        select(SharedStrategy).where(SharedStrategy.id == strategy_id)
    ).scalar_one_or_none()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared strategy not found")

    comment = StrategyComment(
        shared_strategy_id=strategy_id,
        user_id=user.id,
        content=req.content,
    )
    db.add(comment)
    db.commit()

    return {"comment_id": comment.id, "user_id": user.id, "content": comment.content}


@router.get("/strategies/{strategy_id}/comments")
def get_comments(strategy_id: int, limit: int = 50, db: Session = Depends(get_db)):
    comments = list(
        db.execute(
            select(StrategyComment)
            .where(StrategyComment.shared_strategy_id == strategy_id)
            .order_by(desc(StrategyComment.created_at))
            .limit(limit)
        ).scalars().all()
    )
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "content": c.content,
            "created_at": str(c.created_at),
        }
        for c in comments
    ]


@router.post("/strategies/{strategy_id}/fork")
def fork_strategy(
    strategy_id: int,
    authorization: str = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    source = db.execute(
        select(SharedStrategy).where(SharedStrategy.id == strategy_id)
    ).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source strategy not found")

    forked = SharedStrategy(
        user_id=user.id,
        strategy_config_id=source.strategy_config_id,
        title=f"[Fork] {source.title}",
        description=source.description,
        tags=source.tags,
        is_public=True,
    )
    db.add(forked)
    db.flush()

    fork_record = StrategyFork(
        source_strategy_id=strategy_id,
        forked_strategy_id=forked.id,
        user_id=user.id,
    )
    db.add(fork_record)

    source.fork_count += 1
    db.commit()

    return {
        "forked_strategy_id": forked.id,
        "source_strategy_id": strategy_id,
        "title": forked.title,
    }
