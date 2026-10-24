import logging

logger = logging.getLogger("uvicorn.error")


def send_email(to: str, subject: str, body: str) -> None:
    """Fake sender for now. Later, replace the body of this function with real SMTP."""
    logger.info("FAKE SEND to=%s subject=%s\n%s", to, subject, body)