"""
Error Handler Service
Centralized error handling and recovery
"""
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error type enumeration"""
    WEBSOCKET_DISCONNECT = "websocket_disconnect"
    API_ERROR = "api_error"
    STT_ERROR = "stt_error"
    LLM_ERROR = "llm_error"
    TTS_ERROR = "tts_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorHandler:
    """
    Centralized error handling with recovery strategies.
    """
    
    def __init__(self):
        self.error_counts = {}  # Track error frequency
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # Seconds between retries
        logger.info("Error handler initialized")
    
    def handle_error(
        self,
        error: Exception,
        error_type: ErrorType,
        context: Optional[Dict[str, Any]] = None,
        retry_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Handle an error with appropriate recovery strategy.
        
        Args:
            error: Exception that occurred
            error_type: Type of error
            context: Additional context
            retry_func: Optional function to retry
        
        Returns:
            Error response dictionary
        """
        error_key = f"{error_type.value}_{str(error)}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        logger.error(
            f"Error [{error_type.value}]: {str(error)}",
            exc_info=True,
            extra={"context": context or {}}
        )
        
        # Determine if error is recoverable
        is_recoverable = self._is_recoverable(error, error_type)
        
        response = {
            "error": str(error),
            "error_type": error_type.value,
            "recoverable": is_recoverable,
            "retry_count": self.error_counts.get(error_key, 0),
            "context": context or {}
        }
        
        # Attempt recovery if possible
        if is_recoverable and retry_func and self.error_counts[error_key] <= self.max_retries:
            response["should_retry"] = True
            response["retry_delay"] = self.retry_delays[min(
                self.error_counts[error_key] - 1,
                len(self.retry_delays) - 1
            )]
        else:
            response["should_retry"] = False
        
        return response
    
    def _is_recoverable(self, error: Exception, error_type: ErrorType) -> bool:
        """Determine if error is recoverable"""
        # Network errors are usually recoverable
        if error_type in [ErrorType.NETWORK_ERROR, ErrorType.WEBSOCKET_DISCONNECT]:
            return True
        
        # Check error message for recoverable patterns
        error_str = str(error).lower()
        recoverable_patterns = [
            "connection",
            "timeout",
            "network",
            "temporary",
            "retry"
        ]
        
        if any(pattern in error_str for pattern in recoverable_patterns):
            return True
        
        return False
    
    def reset_error_count(self, error_key: str):
        """Reset error count for a specific error"""
        if error_key in self.error_counts:
            del self.error_counts[error_key]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "error_counts": self.error_counts.copy()
        }


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    return _error_handler

