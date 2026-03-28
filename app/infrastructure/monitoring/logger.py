import sys
from loguru import logger
from app.shared.constants import LogCategory


def setup_logger():
    """
    Configure Loguru with separate log files for each category.
    
    Creates 5 file handlers (trades, signals, errors, performance, system)
    with 100MB rotation and 90-day retention, plus a console handler for
    development.
    
    Returns:
        logger: Configured Loguru logger instance
    """
    # Remove the default handler to prevent duplicate logs
    logger.remove()
    
    # Add console handler for development (prints to terminal)
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>"
    )
    
    # Add trades log file
    logger.add(
        "logs/trades.log",
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda record: record["extra"].get("category") == LogCategory.TRADE.value
    )
    
    # Add signals log file
    logger.add(
        "logs/signals.log",
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda record: record["extra"].get("category") == LogCategory.SIGNAL.value
    )
    
    # Add errors log file
    logger.add(
        "logs/errors.log",
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda record: record["extra"].get("category") == LogCategory.ERROR.value
    )
    
    # Add performance log file
    logger.add(
        "logs/performance.log",
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        filter=lambda record: record["extra"].get("category") == LogCategory.PERFORMANCE.value
    )
    
    # Add system log file (default for uncategorized logs)
    logger.add(
        "logs/system.log",
        rotation="100 MB",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        filter=lambda record: record["extra"].get("category") == LogCategory.SYSTEM.value
    )
    
    return logger