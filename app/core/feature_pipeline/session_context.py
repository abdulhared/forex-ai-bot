from datetime import datetime
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory


class SessionContext:
    """Determines active forex trading sessions from timestamp"""
    
    def __init__(self):
        self.logger = setup_logger()
    
    def get_session(self, timestamp_str):
        """
        Get one-hot encoded active sessions for a given timestamp.
        
        Args:
            timestamp_str: ISO timestamp string (e.g., "2026-03-29T14:30:00Z")
            
        Returns:
            Dictionary with session flags (1 for active, 0 for inactive)
        """
        # Parse timestamp and get UTC hour
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        hour = dt.hour
        
        # Initialize all sessions inactive
        sessions = {
            "sydney": 0,
            "tokyo": 0,
            "london": 0,
            "new_york": 0
        }
        
        # Sydney: 21:00 - 06:00 UTC (crosses midnight)
        if hour >= 21 or hour < 6:
            sessions["sydney"] = 1
        
        # Tokyo: 00:00 - 09:00 UTC
        if 0 <= hour < 9:
            sessions["tokyo"] = 1
        
        # London: 07:00 - 16:00 UTC
        if 7 <= hour < 16:
            sessions["london"] = 1
        
        # New York: 12:00 - 21:00 UTC
        if 12 <= hour < 21:
            sessions["new_york"] = 1
        
        return sessions