import sentry_sdk

sentry_sdk.init(
    dsn="your-dsn-here",
    traces_sample_rate=1.0  # captures 100% of transactions
)import sentry_sdk
from app.shared.config import SENTRY_DSN
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


def setup_sentry():
    """
    Initialize Sentry for error tracking and monitoring.
    
    Checks if SENTRY_DSN is configured in environment variables.
    If configured, initializes Sentry SDK to capture unhandled exceptions
    and send alerts. If not configured, logs a warning and continues
    gracefully without error tracking.
    """
    # Get logger instance
    logger = setup_logger()
    
    # Check if Sentry DSN is configured
    if not SENTRY_DSN:
        logger.bind(category=LogCategory.SYSTEM.value).warning(
            "SENTRY_DSN not configured — error tracking disabled. "
            "Set SENTRY_DSN in environment variables to enable Sentry monitoring."
        )
        return
    
    try:
        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0  # Capture 100% of transactions for full visibility
        )
        
        # Log successful initialization
        logger.bind(category=LogCategory.SYSTEM.value).info(
            "Sentry error tracking enabled — unhandled exceptions will be captured and reported"
        )
    
    except Exception as e:
        # If Sentry initialization fails, log error but don't crash the bot
        logger.bind(category=LogCategory.ERROR.value).error(
            f"Failed to initialize Sentry: {e} — error tracking disabled"
        )