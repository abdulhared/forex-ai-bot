from datetime import datetime, timedelta, timezone
from app.infrastructure.monitoring.logger import setup_logger
from app.shared.constants import LogCategory
from app.shared.config import NEWS_BUFFER_MINUTES


class NewsFilter:
    """
    Blocks trading around high-impact news events.
    Prevents trades during periods of low liquidity and high volatility.
    """
    
    def __init__(self):
        self.logger = setup_logger()
        self.buffer_minutes = NEWS_BUFFER_MINUTES  # 15 minutes default
        self.upcoming_events = []  # List of event datetimes
    
    def add_event(self, event_time):
        """
        Add a news event timestamp to block around.
        
        Args:
            event_time: datetime object of the event
        """
        self.upcoming_events.append(event_time)
        self.logger.bind(category=LogCategory.SYSTEM.value).debug(
            f"News event added: {event_time.isoformat()}"
        )
    
    def is_news_window(self, current_time):
        """
        Check if current time is within buffer of any news event.
        
        Args:
            current_time: Current datetime
            
        Returns:
            True if trading should be blocked, False if safe
        """
        for event_time in self.upcoming_events:
            # Calculate time difference
            time_diff = abs((event_time - current_time).total_seconds() / 60)
            
            # Block if within buffer minutes before or after
            if time_diff <= self.buffer_minutes:
                self.logger.bind(category=LogCategory.SYSTEM.value).debug(
                    f"News window active - {time_diff:.1f} minutes from event"
                )
                return True
        
        return False
    
    def clear_past_events(self, current_time):
        """
        Remove events that are more than buffer minutes in the past.
        
        Args:
            current_time: Current datetime
        """
        cutoff = current_time - timedelta(minutes=self.buffer_minutes)
        original_count = len(self.upcoming_events)
        
        self.upcoming_events = [
            event for event in self.upcoming_events 
            if event > cutoff
        ]
        
        if len(self.upcoming_events) != original_count:
            self.logger.bind(category=LogCategory.SYSTEM.value).debug(
                f"Cleared {original_count - len(self.upcoming_events)} past events"
            )