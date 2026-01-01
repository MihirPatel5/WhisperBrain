"""
Memory Management Configuration
Configure memory settings for conversation management
"""
from typing import List

# Memory Management Settings
MEMORY_CONFIG = {
    # Token Management
    'max_tokens': 2000,              # Maximum tokens to keep in context
    'reserve_tokens': 500,           # Reserve tokens for LLM response
    
    # Message Management
    'max_messages': 10,              # Maximum messages to keep
    'summarize_threshold': 15,       # Summarize after this many messages
    
    # Important Keywords (messages with these are kept longer)
    'important_keywords': [
        'important', 'remember', 'note', 'save', 'key', 'critical',
        'don\'t forget', 'keep in mind', 'essential'
    ],
    
    # Context Selection
    'min_context_messages': 2,        # Minimum messages to keep (1 exchange)
    'prefer_recent': True,            # Prefer recent messages over old ones
    'keep_important': True,           # Always keep important messages
}

# Advanced Settings
ADVANCED_MEMORY = {
    'use_llm_summarization': False,  # Use LLM for better summarization (slower)
    'compression_ratio': 0.3,         # Compress old messages to 30% of original
    'importance_scoring': True,        # Score messages by importance
}

