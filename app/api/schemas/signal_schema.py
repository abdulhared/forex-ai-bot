from pydantic import BaseModel, Field


class SignalSchema(BaseModel):
    """
    Pydantic model for AI-generated trading signals.
    
    This is the shared contract between Domain A (AI Model) and Domain B (Risk Manager).
    All signals flow through this schema for validation and serialization.
    """
    
    pair: str
    action: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    stop_loss: float
    take_profit: float
    lot_size: float
    timestamp: str
    model_version: str