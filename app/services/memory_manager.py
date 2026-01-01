"""
Memory Management System for LLM Conversations
Handles conversation history, summarization, and context management
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Manages conversation memory with intelligent context management.
    
    Features:
    - Token counting and limits
    - Conversation summarization
    - Important message retention
    - Context window management
    - Smart message selection
    """
    
    def __init__(
        self,
        max_tokens: int = 2000,
        max_messages: int = 10,
        summarize_threshold: int = 15,
        important_keywords: List[str] = None
    ):
        """
        Initialize memory manager.
        
        Args:
            max_tokens: Maximum tokens to keep in context
            max_messages: Maximum number of messages to keep
            summarize_threshold: Number of messages before summarizing
            important_keywords: Keywords that mark messages as important
        """
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.summarize_threshold = summarize_threshold
        self.important_keywords = important_keywords or [
            'important', 'remember', 'note', 'save', 'key', 'critical'
        ]
        
        self.messages: List[Dict] = []
        self.summary: Optional[str] = None
        self.total_tokens = 0
        
        logger.info(f"Memory manager initialized: max_tokens={max_tokens}, max_messages={max_messages}")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'tokens': self._estimate_tokens(content),
            'important': self._is_important(content)
        }
        
        self.messages.append(message)
        self.total_tokens += message['tokens']
        
        logger.debug(f"Added {role} message: {len(content)} chars, {message['tokens']} tokens")
        
        # Auto-manage memory
        self._manage_memory()
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters).
        For more accuracy, could use tiktoken or similar.
        """
        return len(text) // 4
    
    def _is_important(self, content: str) -> bool:
        """Check if message contains important keywords"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.important_keywords)
    
    def _manage_memory(self) -> None:
        """Automatically manage memory when limits are exceeded"""
        # Check if we need to summarize
        if len(self.messages) > self.summarize_threshold:
            self._summarize_old_messages()
        
        # Check token limit
        if self.total_tokens > self.max_tokens:
            self._compress_context()
        
        # Check message limit
        if len(self.messages) > self.max_messages:
            self._trim_messages()
    
    def _summarize_old_messages(self) -> None:
        """Summarize old messages to save tokens"""
        if len(self.messages) <= 2:
            return
        
        # Keep recent messages, summarize older ones
        keep_recent = 4  # Keep last 4 messages (2 exchanges)
        to_summarize = self.messages[:-keep_recent]
        recent = self.messages[-keep_recent:]
        
        if not to_summarize:
            return
        
        # Create summary of old messages
        summary_text = self._create_summary(to_summarize)
        
        # Replace old messages with summary
        self.messages = [{
            'role': 'system',
            'content': f"Previous conversation summary: {summary_text}",
            'timestamp': datetime.now().isoformat(),
            'tokens': self._estimate_tokens(summary_text),
            'important': False,
            'is_summary': True
        }] + recent
        
        # Recalculate tokens
        self.total_tokens = sum(msg['tokens'] for msg in self.messages)
        
        logger.info(f"Summarized {len(to_summarize)} messages into summary, kept {len(recent)} recent")
    
    def _create_summary(self, messages: List[Dict]) -> str:
        """
        Create a summary of messages.
        Simple implementation - can be enhanced with LLM summarization.
        """
        summary_parts = []
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            # Truncate long messages
            if len(content) > 100:
                content = content[:100] + "..."
            
            summary_parts.append(f"{role.capitalize()}: {content}")
        
        return " | ".join(summary_parts)
    
    def _compress_context(self) -> None:
        """Compress context when token limit is exceeded"""
        # Keep important messages and recent messages
        important = [msg for msg in self.messages if msg.get('important', False)]
        recent = self.messages[-4:]  # Last 4 messages
        
        # Combine and deduplicate
        combined = []
        seen = set()
        
        for msg in important + recent:
            msg_id = id(msg)
            if msg_id not in seen:
                combined.append(msg)
                seen.add(msg_id)
        
        # Sort by timestamp
        combined.sort(key=lambda x: x.get('timestamp', ''))
        
        # Trim until under token limit
        while self._calculate_total_tokens(combined) > self.max_tokens and len(combined) > 2:
            # Remove least important (not important, not recent)
            if len(combined) > 2:
                combined.pop(0)
        
        self.messages = combined
        self.total_tokens = self._calculate_total_tokens(self.messages)
        
        logger.info(f"Compressed context: {len(self.messages)} messages, {self.total_tokens} tokens")
    
    def _calculate_total_tokens(self, messages: List[Dict]) -> int:
        """Calculate total tokens for messages"""
        return sum(msg.get('tokens', 0) for msg in messages)
    
    def _trim_messages(self) -> None:
        """Trim messages when count limit is exceeded"""
        # Keep important and recent messages
        important = [msg for msg in self.messages if msg.get('important', False)]
        recent = self.messages[-self.max_messages:]
        
        # Combine
        combined = []
        seen = set()
        
        for msg in important + recent:
            msg_id = id(msg)
            if msg_id not in seen:
                combined.append(msg)
                seen.add(msg_id)
        
        # Sort and limit
        combined.sort(key=lambda x: x.get('timestamp', ''))
        self.messages = combined[-self.max_messages:]
        self.total_tokens = self._calculate_total_tokens(self.messages)
        
        logger.info(f"Trimmed to {len(self.messages)} messages")
    
    def get_context(self, max_tokens: Optional[int] = None) -> List[Dict]:
        """
        Get conversation context for LLM.
        
        Args:
            max_tokens: Optional token limit (uses self.max_tokens if None)
            
        Returns:
            List of messages formatted for LLM
        """
        limit = max_tokens or self.max_tokens
        
        # Select messages that fit within token limit
        selected = []
        token_count = 0
        
        # Start from most recent and work backwards
        for msg in reversed(self.messages):
            msg_tokens = msg.get('tokens', 0)
            
            if token_count + msg_tokens <= limit:
                selected.insert(0, msg)
                token_count += msg_tokens
            else:
                break
        
        # Format for LLM (remove metadata)
        context = []
        for msg in selected:
            context.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        logger.debug(f"Returning context: {len(context)} messages, ~{token_count} tokens")
        return context
    
    def clear(self) -> None:
        """Clear all conversation memory"""
        self.messages = []
        self.summary = None
        self.total_tokens = 0
        logger.info("Conversation memory cleared")
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            'total_messages': len(self.messages),
            'total_tokens': self.total_tokens,
            'max_tokens': self.max_tokens,
            'max_messages': self.max_messages,
            'has_summary': self.summary is not None,
            'important_messages': sum(1 for msg in self.messages if msg.get('important', False))
        }


class AdvancedMemoryManager(ConversationMemory):
    """
    Advanced memory manager with LLM-based summarization.
    Requires LLM access for intelligent summarization.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_summarize = kwargs.get('llm_summarize', False)
    
    def _create_summary(self, messages: List[Dict]) -> str:
        """
        Create summary using LLM (if available) or fallback to simple summary.
        """
        if not self.llm_summarize:
            return super()._create_summary(messages)
        
        # TODO: Implement LLM-based summarization
        # This would call the LLM to create a proper summary
        # For now, use simple summary
        return super()._create_summary(messages)

