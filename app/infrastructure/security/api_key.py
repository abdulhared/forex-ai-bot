from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from app.shared.config import API_KEY, API_KEY_DEV
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory

# Configure API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def validate_api_key(api_key: str = Security(api_key_header)):
    """
    Validate the API key from the X-API-Key header.
    
    Accepts either the production API_KEY or development API_KEY_DEV.
    Raises HTTPException 401 if the key is missing or invalid.
    
    Args:
        api_key (str): API key extracted from the X-API-Key header
    
    Returns:
        str: The validated API key
    
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    logger = setup_logger()
    
    # Check if API key is missing
    if not api_key:
        logger.bind(category=LogCategory.SYSTEM.value).warning(
            "API request rejected: missing API key"
        )
        raise HTTPException(
            status_code=401,
            detail="API key missing. Provide X-API-Key header."
        )
    
    # Check if API key is valid (matches either production or development key)
    if api_key == API_KEY:
        # Production key used
        logger.bind(category=LogCategory.SYSTEM.value).debug(
            "API request authenticated with production key"
        )
        return api_key
    elif api_key == API_KEY_DEV:
        # Development key used
        logger.bind(category=LogCategory.SYSTEM.value).debug(
            "API request authenticated with development key"
        )
        return api_key
    else:
        # Invalid key
        logger.bind(category=LogCategory.SYSTEM.value).warning(
            f"API request rejected: invalid API key (key starts with: {api_key[:8]}...)"
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )