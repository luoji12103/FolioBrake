import logging

logger = logging.getLogger(__name__)

class SentimentService:
    def analyze_sentiment(self, text: str):
        logger.info(f"Analyzing sentiment: {text[:50]}...")
        return {"text": text, "sentiment": "neutral", "score": 0.5}
    
    def get_market_sentiment(self, symbol: str):
        logger.info(f"Getting market sentiment for {symbol}")
        return {"symbol": symbol, "sentiment": "neutral", "score": 0.5}
