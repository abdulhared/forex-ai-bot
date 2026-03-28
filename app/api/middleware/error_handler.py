import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


async def handle_errors(request: Request, call_next):
    """
    Global exception handler middleware that catches all unhandled exceptions.
    
    Logs the full error with traceback internally, but returns a clean JSON
    response to the client without exposing internal implementation details.
    """
    logger = setup_logger()
    
    try:
        # Process the request normally
        response = await call_next(request)
        return response
        
    except Exception as e:
        # Log the full error with traceback for debugging
        error_traceback = traceback.format_exc()
        logger.bind(category=LogCategory.ERROR.value).error(
            f"Unhandled exception in {request.method} {request.url.path}: {e}\n{error_traceback}"
        )
        
        # Return clean JSON response to client
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(e) if str(e) else "An unexpected error occurred"
            }
        )