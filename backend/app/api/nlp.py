from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.db.base import get_db
from app.nlp.models import NewsArticle, SentimentResult
from app.nlp.sentiment import SentimentAnalyzer

router = APIRouter(tags=["nlp"])

_analyzer = SentimentAnalyzer()


class AnalyzeRequest(BaseModel):
    text: str
    instrument_id: int | None = None


class AnalyzeBatchRequest(BaseModel):
    texts: list[str]
    instrument_id: int | None = None


class IngestNewsRequest(BaseModel):
    title: str
    content: str | None = None
    source: str | None = None
    url: str | None = None
    published_at: str | None = None
    instrument_id: int | None = None


@router.post("/analyze")
def analyze_text(req: AnalyzeRequest, db: Session = Depends(get_db)):
    result = _analyzer.analyze(req.text)

    record = SentimentResult(
        instrument_id=req.instrument_id,
        text_snippet=req.text[:500],
        label=result["label"],
        score=result["score"],
        model_name=result.get("model"),
    )
    db.add(record)
    db.commit()

    return {
        "sentiment_id": record.id,
        "label": result["label"],
        "score": result["score"],
        "model": result.get("model"),
    }


@router.post("/analyze-batch")
def analyze_batch(req: AnalyzeBatchRequest, db: Session = Depends(get_db)):
    results = _analyzer.analyze_batch(req.texts)

    records = []
    for text, result in zip(req.texts, results):
        record = SentimentResult(
            instrument_id=req.instrument_id,
            text_snippet=text[:500],
            label=result["label"],
            score=result["score"],
            model_name=result.get("model"),
        )
        db.add(record)
        records.append(record)
    db.commit()

    return {
        "count": len(records),
        "results": [
            {"sentiment_id": r.id, "label": r.label, "score": r.score}
            for r in records
        ],
    }


@router.post("/ingest-news")
def ingest_news(req: IngestNewsRequest, db: Session = Depends(get_db)):
    article = NewsArticle(
        title=req.title,
        content=req.content,
        source=req.source,
        url=req.url,
        instrument_id=req.instrument_id,
    )
    db.add(article)
    db.flush()

    text = req.title
    if req.content:
        text += " " + req.content

    result = _analyzer.analyze(text)
    sentiment = SentimentResult(
        article_id=article.id,
        instrument_id=req.instrument_id,
        text_snippet=text[:500],
        label=result["label"],
        score=result["score"],
        model_name=result.get("model"),
    )
    db.add(sentiment)
    db.commit()

    return {
        "article_id": article.id,
        "sentiment": {
            "label": result["label"],
            "score": result["score"],
        },
    }


@router.get("/sentiments")
def list_sentiments(
    instrument_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = select(SentimentResult).order_by(desc(SentimentResult.analyzed_at))
    if instrument_id:
        query = query.where(SentimentResult.instrument_id == instrument_id)
    query = query.limit(limit)

    results = list(db.execute(query).scalars().all())
    return [
        {
            "id": r.id,
            "instrument_id": r.instrument_id,
            "text_snippet": r.text_snippet[:100],
            "label": r.label,
            "score": r.score,
            "analyzed_at": str(r.analyzed_at),
        }
        for r in results
    ]


@router.get("/sentiment-summary/{instrument_id}")
def sentiment_summary(instrument_id: int, db: Session = Depends(get_db)):
    results = list(
        db.execute(
            select(SentimentResult).where(SentimentResult.instrument_id == instrument_id)
        ).scalars().all()
    )
    if not results:
        return {"instrument_id": instrument_id, "count": 0}

    pos = sum(1 for r in results if r.label == "POSITIVE")
    neg = sum(1 for r in results if r.label == "NEGATIVE")
    neu = sum(1 for r in results if r.label == "NEUTRAL")
    avg_score = sum(r.score for r in results) / len(results)

    return {
        "instrument_id": instrument_id,
        "count": len(results),
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "avg_score": round(avg_score, 4),
    }
