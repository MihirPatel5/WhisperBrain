"""
Model Configuration
Defines available LLM models and their use cases
"""
from typing import Dict, List

# Available models (ordered by size/performance)
AVAILABLE_MODELS = [
    "tinyllama",      # Fastest, smallest
    "phi3:mini",      # Fast, efficient
    "llama3.2:1b",    # Small, good quality
    "llama3.2",       # Medium, balanced
    "phi3",           # Medium-large, high quality
]

# Model use case mapping
MODEL_USE_CASES: Dict[str, List[str]] = {
    "tinyllama": ["quick", "simple", "fast"],
    "phi3:mini": ["general", "chat", "fast"],
    "llama3.2:1b": ["general", "chat", "balanced"],
    "llama3.2": ["general", "chat", "detailed", "balanced"],
    "phi3": ["detailed", "complex", "high-quality"],
}

# Default model
DEFAULT_MODEL = "phi3:mini"

# Model selection rules
USE_CASE_KEYWORDS = {
    "coding": ["code", "program", "function", "script", "debug", "python", "javascript"],
    "math": ["calculate", "math", "equation", "solve", "number", "sum"],
    "creative": ["write", "story", "poem", "creative", "imagine"],
    "analysis": ["analyze", "explain", "compare", "why", "how"],
    "quick": ["quick", "short", "brief", "simple"],
}


def get_model_for_use_case(use_case: str = None, text: str = None) -> str:
    """
    Select best model for use case.
    
    Args:
        use_case: Explicit use case (optional)
        text: User text to analyze for use case detection
    
    Returns:
        Model name
    """
    # If explicit use case provided, use it
    if use_case:
        for model, use_cases in MODEL_USE_CASES.items():
            if use_case in use_cases:
                return model
    
    # Auto-detect use case from text
    if text:
        text_lower = text.lower()
        for use_case_name, keywords in USE_CASE_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                # Map use case to model
                if use_case_name == "coding":
                    return "phi3"  # Better for code
                elif use_case_name == "math":
                    return "llama3.2"  # Good for reasoning
                elif use_case_name == "creative":
                    return "phi3"  # Better creativity
                elif use_case_name == "analysis":
                    return "llama3.2"  # Good analysis
                elif use_case_name == "quick":
                    return "tinyllama"  # Fast response
    
    # Default model
    return DEFAULT_MODEL

