
import logging
import os

import logfire
from dotenv import load_dotenv


def setup_logging() -> logging.Logger:
    """
    Configure application logging and optionally connect Logfire.
    """

    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    logger = logging.getLogger("ai_meeting_intelligence")

    token = os.getenv("LOGFIRE_TOKEN", "").strip()

    if token:
        try:
            logfire.configure(
                token=token,
                send_to_logfire=True,
            )

            logfire.info(
                "AI Meeting Intelligence logging initialized."
            )

            logger.info("Logfire configured.")

        except Exception:
            logger.exception(
                "Logfire initialization failed. "
                "Standard logging will continue."
            )
    else:
        logger.warning(
            "LOGFIRE_TOKEN is not configured. "
            "Continuing with console logging."
        )

    return logger


logger = setup_logging()