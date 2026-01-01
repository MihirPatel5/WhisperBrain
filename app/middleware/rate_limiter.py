"""
Rate Limiting Middleware
Limits API usage per user/organization for cost control and fair usage
"""
import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter for API endpoints.
    Tracks requests per user/IP and enforces limits.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100,
        requests_per_day: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        # Track requests: {identifier: [(timestamp, count), ...]}
        self.request_history: Dict[str, List[float]] = defaultdict(list)
        
        logger.info(f"Rate limiter initialized: {requests_per_minute}/min, {requests_per_hour}/hour, {requests_per_day}/day")
    
    def is_allowed(
        self,
        identifier: str,
        current_time: Optional[float] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: User ID, IP address, or session ID
            current_time: Current timestamp (optional, uses time.time() if None)
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if current_time is None:
            current_time = time.time()
        
        # Clean old entries (older than 24 hours)
        cutoff = current_time - 86400  # 24 hours
        self.request_history[identifier] = [
            ts for ts in self.request_history[identifier] if ts > cutoff
        ]
        
        history = self.request_history[identifier]
        
        # Check per-minute limit
        minute_ago = current_time - 60
        recent_minute = [ts for ts in history if ts > minute_ago]
        if len(recent_minute) >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check per-hour limit
        hour_ago = current_time - 3600
        recent_hour = [ts for ts in history if ts > hour_ago]
        if len(recent_hour) >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Check per-day limit
        day_ago = current_time - 86400
        recent_day = [ts for ts in history if ts > day_ago]
        if len(recent_day) >= self.requests_per_day:
            return False, f"Rate limit exceeded: {self.requests_per_day} requests per day"
        
        # Record this request
        history.append(current_time)
        
        return True, None
    
    def get_remaining_requests(
        self,
        identifier: str,
        period: str = "minute"
    ) -> int:
        """
        Get remaining requests for a period.
        
        Args:
            identifier: User ID, IP address, or session ID
            period: "minute", "hour", or "day"
        
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        
        if period == "minute":
            limit = self.requests_per_minute
            window = 60
        elif period == "hour":
            limit = self.requests_per_hour
            window = 3600
        elif period == "day":
            limit = self.requests_per_day
            window = 86400
        else:
            return 0
        
        cutoff = current_time - window
        history = self.request_history[identifier]
        recent = [ts for ts in history if ts > cutoff]
        
        return max(0, limit - len(recent))
    
    def reset(self, identifier: str):
        """Reset rate limit for an identifier"""
        if identifier in self.request_history:
            del self.request_history[identifier]
            logger.info(f"Reset rate limit for: {identifier}")


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter

