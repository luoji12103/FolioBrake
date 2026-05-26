import logging

logger = logging.getLogger(__name__)

def send_email(to: str, subject: str, body: str):
    logger.info(f"Email to {to}: {subject}")
    return True
