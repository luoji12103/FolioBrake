"""News sentiment analysis engine.

Dependencies (optional):
    pip install transformers torch

If transformers is not installed, a keyword-based fallback is provided.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline as hf_pipeline  # type: ignore[import-untyped]

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    hf_pipeline = None  # type: ignore[misc,assignment]

POSITIVE_KEYWORDS = {
    "利好", "上涨", "突破", "增长", "盈利", "反弹", "牛市", "买入", "推荐",
    "利好", "涨停", "大涨", "新高", "景气", "复苏", "超预期", "增持",
    "bullish", "buy", "upgrade", "outperform", "growth", "profit", "surge",
    "rally", "breakout", "positive", "strong", "beat",
}

NEGATIVE_KEYWORDS = {
    "利空", "下跌", "跌破", "亏损", "下滑", "熊市", "卖出", "减持", "风险",
    "跌停", "暴跌", "新低", "衰退", "低迷", "不及预期", "爆仓",
    "bearish", "sell", "downgrade", "underperform", "loss", "decline", "crash",
    "slump", "breakdown", "negative", "weak", "miss",
}


class SentimentAnalyzer:

    def __init__(self, model_name: str = "finiteautomata/bertweet-base-sentiment-analysis"):
        self.model_name = model_name
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None and HAS_TRANSFORMERS:
            assert hf_pipeline is not None
            self._pipeline = hf_pipeline("sentiment-analysis", model=self.model_name)
        return self._pipeline

    def analyze(self, text: str) -> dict[str, Any]:
        if HAS_TRANSFORMERS:
            return self._analyze_transformers(text)
        return self._analyze_keywords(text)

    def analyze_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        if HAS_TRANSFORMERS:
            return self._analyze_batch_transformers(texts)
        return [self._analyze_keywords(t) for t in texts]

    def _analyze_transformers(self, text: str) -> dict[str, Any]:
        pipe = self._get_pipeline()
        assert pipe is not None
        truncated = text[:512]
        result = pipe(truncated)
        raw_label = result[0]["label"].upper()
        score = float(result[0]["score"])

        if "POS" in raw_label or "POSITIVE" in raw_label:
            label = "POSITIVE"
        elif "NEG" in raw_label or "NEGATIVE" in raw_label:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        return {"label": label, "score": score, "model": self.model_name}

    def _analyze_batch_transformers(self, texts: list[str]) -> list[dict[str, Any]]:
        pipe = self._get_pipeline()
        assert pipe is not None
        truncated = [t[:512] for t in texts]
        results = pipe(truncated, batch_size=16)
        output = []
        for r in results:
            raw_label = r["label"].upper()
            score = float(r["score"])
            if "POS" in raw_label or "POSITIVE" in raw_label:
                label = "POSITIVE"
            elif "NEG" in raw_label or "NEGATIVE" in raw_label:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"
            output.append({"label": label, "score": score, "model": self.model_name})
        return output

    def _analyze_keywords(self, text: str) -> dict[str, Any]:
        text_lower = text.lower()
        pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
        total = pos_count + neg_count

        if total == 0:
            return {"label": "NEUTRAL", "score": 0.5, "model": "keyword_fallback"}

        pos_ratio = pos_count / total
        if pos_ratio > 0.6:
            return {"label": "POSITIVE", "score": pos_ratio, "model": "keyword_fallback"}
        elif pos_ratio < 0.4:
            return {"label": "NEGATIVE", "score": 1 - pos_ratio, "model": "keyword_fallback"}
        return {"label": "NEUTRAL", "score": 0.5, "model": "keyword_fallback"}
