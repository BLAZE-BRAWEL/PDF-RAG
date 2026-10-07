import logging

logging.basicConfig(
    level = logging.WARNING,
    filename = "app/logger/logs.log",
    format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force = True
)

logger = logging.getLogger(__name__)

logger.info('Text')