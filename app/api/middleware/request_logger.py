import time
from fastapi import Request
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


async def log_requests(request: Request, call_next):
    """
    Middleware that logs every request with method, path, status, and duration.
    
    This runs on every request to provide observability into API performance.
    """
    # Get logger instance
    logger = setup_logger()
    
    # Record start time
    start_time = time.time()
    
    # Process the request (pass to next middleware or route handler)
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log the request details
    logger.bind(category=LogCategory.SYSTEM.value).info(
        f"{request.method} {request.url.path} | Status: {response.status_code} | Duration: {duration:.3f}s"
    )
    
    return response