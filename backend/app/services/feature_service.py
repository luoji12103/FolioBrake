import logging

logger = logging.getLogger(__name__)

class FeatureService:
    def compute_features(self, instrument_id: int, as_of_date: str):
        logger.info(f"Computing features for instrument {instrument_id}")
        return {}
    
    def get_definitions(self):
        logger.info("Getting feature definitions")
        return []
