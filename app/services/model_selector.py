"""
Model Selector Service
Dynamically selects the best LLM model for different use cases
"""
import logging
from typing import Optional
from app.config.models import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    get_model_for_use_case
)

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Selects appropriate LLM model based on use case or text analysis.
    """
    
    def __init__(self):
        self.current_model = DEFAULT_MODEL
        self.model_history = []  # Track model usage
        logger.info(f"Model selector initialized with default: {DEFAULT_MODEL}")
    
    def select_model(
        self,
        use_case: Optional[str] = None,
        text: Optional[str] = None,
        user_preference: Optional[str] = None
    ) -> str:
        """
        Select best model for the given context.
        
        Args:
            use_case: Explicit use case (e.g., "coding", "chat")
            text: User text to analyze
            user_preference: User's preferred model (overrides auto-selection)
        
        Returns:
            Selected model name
        """
        # User preference takes priority
        if user_preference and user_preference in AVAILABLE_MODELS:
            self.current_model = user_preference
            logger.info(f"Using user-preferred model: {user_preference}")
            return user_preference
        
        # Auto-select based on use case or text
        selected = get_model_for_use_case(use_case, text)
        self.current_model = selected
        
        if use_case or text:
            logger.info(f"Auto-selected model: {selected} (use_case={use_case})")
        
        # Track model usage
        self.model_history.append({
            'model': selected,
            'use_case': use_case,
            'timestamp': __import__('time').time()
        })
        
        # Keep only last 100 entries
        if len(self.model_history) > 100:
            self.model_history = self.model_history[-100:]
        
        return selected
    
    def get_current_model(self) -> str:
        """Get currently selected model"""
        return self.current_model
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        return AVAILABLE_MODELS.copy()
    
    def get_model_stats(self) -> dict:
        """Get statistics about model usage"""
        from collections import Counter
        model_counts = Counter(entry['model'] for entry in self.model_history)
        return {
            'current_model': self.current_model,
            'total_selections': len(self.model_history),
            'model_usage': dict(model_counts),
            'available_models': AVAILABLE_MODELS
        }


# Global model selector instance
_model_selector = ModelSelector()


def get_model_selector() -> ModelSelector:
    """Get global model selector instance"""
    return _model_selector

