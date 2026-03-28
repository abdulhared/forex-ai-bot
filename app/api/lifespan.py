from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.infrastructure.monitoring.logger import setup_logger
from app.infrastructure.monitoring.sentry import setup_sentry
from app.infrastructure.database.sqlite_client import SQLiteClient
from app.shared.constants import LogCategory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    
    Handles:
    - Logger initialisation
    - Sentry error tracking initialisation
    - Database migration execution
    - Graceful shutdown logging
    """
    
    # ==================== STARTUP ====================
    
    # Initialise logger first — all subsequent logs depend on this
    logger = setup_logger()
    
    # Log startup initiation
    logger.bind(category=LogCategory.SYSTEM.value).info("Forex bot API starting...")
    
    # Initialise Sentry for error tracking (after logger, so errors can be logged)
    try:
        setup_sentry()
    except Exception as e:
        # If Sentry fails, log but continue — it's not critical
        logger.bind(category=LogCategory.ERROR.value).error(
            f"Sentry initialisation failed during startup: {e}"
        )
    
    # Run database migrations
    try:
        logger.bind(category=LogCategory.SYSTEM.value).info("Running database migrations...")
        db_client = SQLiteClient()
        logger.bind(category=LogCategory.SYSTEM.value).info("Database migrations completed successfully")
    except Exception as e:
        logger.bind(category=LogCategory.ERROR.value).error(
            f"Database migration failed during startup: {e}"
        )
        # Re-raise to prevent the API from starting with an invalid database
        raise
    
    # ==================== RUNNING ====================
    
    yield  # The application runs here
    
    # ==================== SHUTDOWN ====================
    
    # Log shutdown
    logger.bind(category=LogCategory.SYSTEM.value).info("Forex bot API shutting down...")