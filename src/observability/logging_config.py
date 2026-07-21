import logging
import structlog
from src.core.config import Settings

def configure_logging()-> None:
    logging.basicConfig(format='%(message)s',level=Settings.log_level)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(settings.log_level)),
    )
def get_logger(name: str):
    return structlog.get_logger(name)