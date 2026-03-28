from fastapi import Request
from fastapi.responses import JSONResponse
from app.shared.config import API_KEY, API_KEY_DEV
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory

# Public endpoints that don't require authentication
PUBLIC_PATHS = ["/", "/health", "/docs", "/openapi.json", "/redoc"]

# Valid API keys (production and development)
VALID_KEYS = {API_KEY, API_KEY_DEV}


async def authenticate_request(request: Request, call_next):
    """
    Authentication middleware that validates API key on every request.
    
    Public paths (/, /health, /docs, /openapi.json, /redoc) are exempt.
    All other paths require a valid X-API-Key header.
    """
    logger = setup_logger()
    
    # Check if the path is public
    path = request.url.path
    if path in PUBLIC_PATHS:
        # Skip authentication for public paths
        return await call_next(request)
    
    # Extract API key from headers
    api_key = request.headers.get("X-API-Key")
    
    # Validate API key
    if not api_key:
        logger.bind(category=LogCategory.SYSTEM.value).warning(
            f"Authentication failed for {path}: missing API key"
        )
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "detail": "X-API-Key header missing"}
        )
    
    if api_key not in VALID_KEYS:
        logger.bind(category=LogCategory.SYSTEM.value).warning(
            f"Authentication failed for {path}: invalid API key (key starts with: {api_key[:8]}...)"
        )
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication failed", "detail": "Invalid API key"}
        )
    
    # Log successful authentication (debug level to avoid noise)
    logger.bind(category=LogCategory.SYSTEM.value).debug(
        f"Authentication successful for {path}"
    )
    
    # Valid key — proceed to the route handler
    return await call_next(request)