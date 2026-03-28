from app.infrastructure.monitoring.logger import setup_logger

logger = setup_logger()

logger.bind(category="trade").info("Test trade log")
logger.bind(category="signal").info("Test signal log")
logger.bind(category="error").error("Test error log")
logger.bind(category="performance").info("Test performance log")
logger.bind(category="system").info("Test system log")

print("Check your logs/ folder")