"""
Reconnection Manager Service
Handles automatic reconnection logic
"""
import logging
import asyncio
from typing import Optional, Callable, Dict, Any
from app.services.user_preferences import get_user_preferences

logger = logging.getLogger(__name__)


class ReconnectionManager:
    """
    Manages automatic reconnection with exponential backoff.
    """
    
    def __init__(self):
        self.preferences = get_user_preferences()
        self.reconnect_attempts = 0
        self.max_attempts = self.preferences.get_preference("connection", "max_retries", 5)
        self.base_delay = self.preferences.get_preference("connection", "reconnect_delay", 3)
        self.is_reconnecting = False
        logger.info("Reconnection manager initialized")
    
    async def attempt_reconnect(
        self,
        reconnect_func: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        
        Args:
            reconnect_func: Async function to call for reconnection
            context: Additional context
        
        Returns:
            True if reconnected successfully, False otherwise
        """
        auto_reconnect = self.preferences.get_preference("connection", "auto_reconnect", True)
        
        if not auto_reconnect:
            logger.info("Auto-reconnect is disabled")
            return False
        
        if self.is_reconnecting:
            logger.warning("Reconnection already in progress")
            return False
        
        self.is_reconnecting = True
        
        try:
            for attempt in range(1, self.max_attempts + 1):
                delay = self.base_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.info(f"Reconnection attempt {attempt}/{self.max_attempts} in {delay}s...")
                
                await asyncio.sleep(delay)
                
                try:
                    await reconnect_func()
                    logger.info(f"Successfully reconnected on attempt {attempt}")
                    self.reconnect_attempts = 0
                    self.is_reconnecting = False
                    return True
                except Exception as e:
                    logger.warning(f"Reconnection attempt {attempt} failed: {e}")
                    if attempt == self.max_attempts:
                        logger.error(f"Failed to reconnect after {self.max_attempts} attempts")
                        self.is_reconnecting = False
                        return False
            
            self.is_reconnecting = False
            return False
        except Exception as e:
            logger.error(f"Reconnection error: {e}")
            self.is_reconnecting = False
            return False
    
    def reset(self):
        """Reset reconnection state"""
        self.reconnect_attempts = 0
        self.is_reconnecting = False
        logger.debug("Reconnection manager reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get reconnection status"""
        return {
            "is_reconnecting": self.is_reconnecting,
            "attempts": self.reconnect_attempts,
            "max_attempts": self.max_attempts,
            "auto_reconnect": self.preferences.get_preference("connection", "auto_reconnect", True)
        }


# Global reconnection manager instance
_reconnection_manager = ReconnectionManager()


def get_reconnection_manager() -> ReconnectionManager:
    """Get global reconnection manager instance"""
    return _reconnection_manager

