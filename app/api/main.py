from fastapi import FastAPI
from app.api.lifespan import lifespan
from app.api.middleware.auth import authenticate_request
from app.api.middleware.error_handler import handle_errors
from app.api.middleware.request_logger import log_requests
from app.api.routes import status
from app.api.routes import trades

# Create FastAPI application with metadata
app = FastAPI(
    title="Forex AI Bot API",
    description="API for controlling the forex trading bot. Provides endpoints for monitoring trades, performance, and system control.",
    version="1.0.0",
    lifespan=lifespan
)

# Register middleware (order matters — they execute in reverse registration order)
app.middleware("http")(handle_errors)
app.middleware("http")(log_requests)
app.middleware("http")(authenticate_request)
app.include_router(status.router)
app.include_router(trades.router)

# Root endpoint for health check
@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "Forex AI Bot API is operational",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }